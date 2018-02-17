"""Define abstract SQL backend class."""

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Type, Union

from anansi.core.abstract_storage import AbstractStorage
from anansi.core.middleware import Middleware
from anansi.core.context import (
    Ordering,
    ReturnType,
    make_context,
    resolve_namespace
)
from anansi.core.query import Query
from anansi.core.query_group import QueryGroup

from .utils import (
    args_to_sql,
    changes_to_sql,
    fields_to_sql,
    group_changes,
    order_to_sql,
    query_to_sql,
    updates_to_sql,
)


class AbstractSql(AbstractStorage, metaclass=ABCMeta):
    """Define abstract SQL based backend."""

    def __init__(
        self,
        *,
        database: str='',
        default_namespace: str='',
        middleware: 'Middleware'=None,
        host: str='',
        op_map: Dict[Union[Query.Op, QueryGroup.Op], str]=None,
        order_map: Dict[Ordering, str]=None,
        quote: str='',
        password: str='',
        port: int=0,
        username: str=''
    ):
        self.database = database
        self.default_namespace = default_namespace
        self.host = host
        self.middleware = middleware or Middleware()
        self.op_map = op_map or {}
        self.order_map = order_map or {}
        self.quote = quote
        self.password = password
        self.port = port
        self.username = username

    async def delete_collection(
        self,
        collection: 'Collection',
        context: 'Context'
    ) -> int:
        """Delete collection of records from the database."""
        pass

    async def create_record(self, record: 'Model', context: 'Context') -> dict:
        """Insert new record into the database."""
        standard_changes, i18n_changes = group_changes(record)
        if i18n_changes:
            return await self.create_i18n_record(
                record,
                context,
                standard_changes,
                i18n_changes
            )
        else:
            return await self.create_standard_record(
                record,
                context,
                standard_changes
            )

    async def create_i18n_record(
        self,
        record: 'Model',
        context: 'Context',
        standard_changes: dict,
        i18n_changes: dict
    ) -> dict:
        """Create new database record that has translatable fields."""
        schema = record.__schema__
        sql = (
            'INSERT INTO {q}{namespace}{q}.{q}{table}{q} (\n'
            '   {columns}\n'
            ')\n'
            'VALUES({values});\n'
            'INSERT INTO {q}{namespace}{q}.{q}{i18n_table}{q} (\n'
            '   {i18n_columns}\n'
            ')\n'
            'VALUES({i18n_values});'
        )

        column_str, value_str, values = changes_to_sql(
            standard_changes,
            quote=self.quote
        )

        i18n_changes.setdefault('locale', context.locale)
        i18n_column_str, i18n_value_str, i18n_values = changes_to_sql(
            i18n_changes,
            field_key='i18n_code',
            offset=len(values),
            quote=self.quote,
        )

        statement = sql.format(
            columns=column_str,
            i18n_columns=i18n_column_str,
            i18n_values=i18n_value_str,
            i18n_table=schema.i18n_name,
            namespace=resolve_namespace(
                schema,
                context,
                default=self.default_namespace
            ),
            q=self.quote,
            values=value_str,
            table=schema.resource_name,
        )
        return await self.execute(
            statement,
            *values,
            *i18n_values,
            method='fetch',
            connection=context.connection,
        )[0]

    async def create_standard_record(
        self,
        record: 'Model',
        context: 'Context',
        changes: dict
    ) -> dict:
        """Create a standard record in the database."""
        schema = record.__schema__
        sql = (
            'INSERT INTO {q}{namespace}{q}.{q}{table}{q} (\n'
            '   {columns}\n'
            ')\n'
            'VALUES({values});'
        )

        column_str, value_str, values = changes_to_sql(
            changes,
            quote=self.quote
        )

        statement = sql.format(
            columns=column_str,
            namespace=resolve_namespace(
                schema,
                context,
                default=self.default_namespace
            ),
            q=self.quote,
            values=value_str,
            table=schema.resource_name,
        )
        return await self.execute(
            statement,
            *values,
            method='fetch',
            connection=context.connection,
        )[0]

    async def delete_record(self, record: 'Model', context: 'Context') -> int:
        """Delete record from database."""
        schema = record.__schema__
        key_dict = await record.get_key_dict(key_property='code')
        args, values = args_to_sql(
            key_dict,
            joiner=' {} '.format(self.op_map[QueryGroup.Op.And]),
            quote=self.quote,
        )

        if schema.has_translations:
            sql = (
                'DELETE FROM {q}{namespace}{q}.{q}{i18n_table}{q} '
                'WHERE {args};\n'
                'DELETE FROM {q}{namespace}{q}.{q}{table}{q} '
                'WHERE {args};'
            )
        else:
            sql = (
                'DELETE FROM {q}{namespace}{q}.{q}{table}{q} '
                'WHERE {args};'
            )

        statement = sql.format(
            args=args,
            namespace=resolve_namespace(
                schema,
                context,
                default=self.default_namespace
            ),
            q=self.quote,
            table=schema.resource_name,
            i18n_table=schema.i18n_name
        )
        result = await self.execute(
            statement,
            *values,
            connection=context.connection,
        )
        return int(result.split(' ')[1])

    @abstractmethod
    async def execute(
        self,
        sql: str,
        *args,
        method: str='execute',
        connection: Any=None,
    ) -> bool:
        """Execute the given sql statement in this backend pool."""
        pass

    async def get_count(
        self,
        model: Type['Model'],
        context: 'Context'
    ) -> int:
        """Return number of records available for the given context."""
        count_context = make_context(
            returning=ReturnType.Count,
            context=context
        )
        results = await self.get_records(model, count_context)
        return results[0]['count']

    async def get_records(
        self,
        model: Type['Model'],
        context: 'Context'
    ) -> List[dict]:
        """Get records from the store based on the given context."""
        values = []
        statement = await self.get_records_statement(
            model,
            context,
            values=values
        )
        return await self.execute(
            statement + ';',
            *values,
            method='fetch',
            connection=context.connection,
        )

    async def get_records_statement(
        self,
        model: Type['Model'],
        context: 'Context',
        values: list=None,
        joins: list=None,
    ):
        """Generate SQL statement for selecting records."""
        values = values if values is not None else []
        joins = joins if joins is not None else []
        schema = model.__schema__
        sql = (
            'SELECT {distinct}{columns}\n'
            'FROM {q}{namespace}{q}.{q}{table}{q}\n'
            '{joins}'
            '{where}'
            '{order}'
            '{start}'
            '{limit}'
        )

        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace
        )

        if context.returning == ReturnType.Count:
            fields = []
            columns = ['COUNT(*) AS {0}count{0}'.format(self.quote)]
        else:
            fields, columns = fields_to_sql(
                model,
                context,
                quote=self.quote
            )

        if type(context.distinct) is set:
            distinct_columns = [
                '{0}{1}{0}'.format(self.quote, schema[field].code)
                for field in context.distinct
            ]
            distinct = 'DISTINCT ON ({}) '.format(', '.join(distinct_columns))
        elif context.distinct is True:
            distinct = 'DISTINCT '
        else:
            distinct = ''

        has_translations = any(
            field.test_flag(field.Flags.Translatable)
            for field in fields
        )
        if has_translations:
            i18n_join = (
                'LEFT JOIN {q}{namespace}{q}.{q}{table}{q} i18n '
                'ON ({columns})'
            )

            values.append(context.locale)
            i18n_columns = ' AND '.join(
                'i18n.{0}{1}{0} = {0}{1}{0}'.format(
                    self.quote,
                    field.i18n_code
                )
                for field in schema.key_fields
            )
            i18n_columns += ' AND i18n.{0}locale{0} = $1'.format(self.quote)

            joins.append(i18n_join.format(
                columns=i18n_columns,
                namespace=namespace,
                q=self.quote,
                table=schema.i18n_name,
            ))

        where = await query_to_sql(
            self,
            model,
            context.where,
            context,
            quote=self.quote,
            op_map=self.op_map,
            values=values
        )
        order = order_to_sql(
            model,
            context.order_by,
            order_map=self.order_map,
            quote=self.quote
        )

        statement = sql.format(
            columns=', '.join(columns),
            distinct=distinct,
            joins='{}\n'.format('\n'.join(joins)) if joins else '',
            limit='LIMIT {}\n'.format(context.limit) if context.limit else '',
            namespace=namespace,
            order='ORDER BY {}\n'.format(order) if order else '',
            q=self.quote,
            start='START {}\n'.format(context.start) if context.start else '',
            where='WHERE {}\n'.format(where) if where else '',
            table=schema.resource_name
        ).strip()
        return statement

    async def save_collection(
        self,
        collection: 'Collection',
        context: 'Context'
    ) -> int:
        """Save a collection of records to the database."""
        pass

    async def save_record(self, record: 'Model', context: 'Context') -> dict:
        """Save record to backend database."""
        if record.is_new_record:
            return await self.create_record(record, context)
        else:
            return await self.update_record(record, context)

    async def update_record(self, record: 'Model', context: 'Context') -> dict:
        """Insert new record into the database."""
        standard_changes, i18n_changes = group_changes(record)
        if i18n_changes:
            return await self.update_i18n_record(
                record,
                context,
                standard_changes,
                i18n_changes
            )
        else:
            return await self.update_standard_record(
                record,
                context,
                standard_changes
            )

    async def update_i18n_record(
        self,
        record: 'Model',
        context: 'Context',
        standard_changes: dict,
        i18n_changes: dict
    ) -> dict:
        """Create new database record that has translatable fields."""
        raise NotImplementedError

    async def update_standard_record(
        self,
        record: 'Model',
        context: 'Context',
        changes: dict
    ) -> dict:
        """Create a standard record in the database."""
        schema = record.__schema__
        sql = (
            'UPDATE {q}{namespace}{q}.{q}{table}{q} SET \n'
            '   {updates}\n'
            'WHERE {query};'
        )

        update_str, values = updates_to_sql(
            changes,
            quote=self.quote
        )
        where = record.make_fetch_query(await record.get_key())
        query_str = await query_to_sql(
            self,
            type(record),
            where,
            context,
            quote=self.quote,
            op_map=self.op_map,
            values=values
        )

        statement = sql.format(
            namespace=resolve_namespace(
                schema,
                context,
                default=self.default_namespace
            ),
            q=self.quote,
            query=query_str,
            table=schema.resource_name,
            updates=update_str,
        )
        results = await self.execute(
            statement,
            *values,
            method='fetch',
            connection=context.connection,
        )

        return results[0] if results else {}
