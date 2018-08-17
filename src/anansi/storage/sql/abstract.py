"""Define abstract SQL backend class."""

from abc import ABCMeta, abstractmethod
from anansi.core.abstract_storage import AbstractStorage
from anansi.core.context import (
    Ordering,
    ReturnType,
    make_context,
    resolve_namespace
)
from anansi.core.query import Query
from anansi.core.query_group import QueryGroup
from anansi.utils import singlify
from typing import Any, List, Type, Union, TYPE_CHECKING

from .utils import (
    generate_arg_lists,
    generate_arg_pairs,
    generate_select_query,
    generate_select_statement,
    split_changes,
)

if TYPE_CHECKING:
    import anansi


class AbstractSqlStorage(AbstractStorage, metaclass=ABCMeta):
    """Define abstract SQL based backend."""

    def __init__(
        self,
        *,
        database: str = '',
        default_namespace: str = '',
        host: str = '',
        password: str = '',
        port: int = 0,
        username: str = '',
        **base_kwargs,
    ):
        super().__init__(**base_kwargs)

        self.database = database
        self.default_namespace = default_namespace
        self.host = host
        self.password = password
        self.port = port
        self.username = username

    async def create_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
    ) -> dict:
        """Insert new record into the database."""
        changes, i18n_changes = split_changes(
            record.__schema__.fields,
            record.local_changes,
        )

        if i18n_changes:
            result = await self.create_i18n_record(
                record.__schema__,
                context,
                changes,
                i18n_changes
            )
        elif changes:
            result = await self.create_standard_record(
                record.__schema__,
                context,
                changes
            )
        else:
            result = {}

        return result

    async def create_i18n_record(
        self,
        schema: 'anansi.Schema',
        context: 'anansi.Context',
        changes: dict,
        i18n_changes: dict
    ) -> dict:
        """Create new database record that has translatable fields."""
        template = (
            'INSERT INTO {table} (\n'
            '   {columns}\n'
            ')\n'
            'VALUES({values});\n'
            'INSERT INTO {i18n_table} (\n'
            '   {i18n_columns}\n'
            ')\n'
            'VALUES({i18n_values});'
        )

        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace,
        )
        table = '.'.join(self.quote(namespace, schema.resource_name))
        column_sql, value_sql, values = generate_arg_lists(
            changes,
            context=context,
            quote=self.quote,
        )

        i18n_table = '.'.join(self.quote(namespace, schema.i18n_name))
        i18n_changes.setdefault('locale', context.locale)
        (
            i18n_column_sql,
            i18n_value_sql,
            i18n_values,
        ) = generate_arg_lists(
            i18n_changes,
            context=context,
            field_key='i18n_code',
            offset_index=len(values),
            quote=self.quote,
        )

        sql = template.format(
            columns=', '.join(column_sql),
            values=', '.join(value_sql),
            i18n_columns=', '.join(i18n_column_sql),
            i18n_values=', '.join(i18n_value_sql),
            table=table,
            i18n_table=i18n_table,
        )

        result = await self.execute(
            sql,
            *values,
            *i18n_values,
            method='fetch',
            connection=context.connection,
        )
        return result[0]

    async def create_standard_record(
        self,
        schema: 'anansi.Schema',
        context: 'anansi.Context',
        changes: dict,
    ) -> dict:
        """Create a standard record in the database."""
        template = (
            'INSERT INTO {table} (\n'
            '   {columns}\n'
            ')\n'
            'VALUES({values});'
        )

        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace,
        )
        table = '.'.join(self.quote(namespace, schema.resource_name))
        column_sql, value_sql, values = generate_arg_lists(
            changes,
            context=context,
            quote=self.quote,
        )

        sql = template.format(
            columns=', '.join(column_sql),
            values=', '.join(value_sql),
            table=table,
        )

        result = await self.execute(
            sql,
            *values,
            method='fetch',
            connection=context.connection,
        )
        return result[0]

    async def delete_collection(
        self,
        model: 'anansi.Model',
        context: 'anansi.Context'
    ) -> int:
        """Delete collection of records from the database."""
        raise NotImplementedError

    async def delete_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
    ) -> int:
        """Delete record from database."""
        schema = record.__schema__
        keys = await record.get_key_dict(key_property='code')
        pairs, values = generate_arg_pairs(
            keys,
            context=context,
            quote=self.quote,
        )
        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace
        )

        template_options = {}
        template_options['where'] = ' AND '.join(pairs)
        template_options['table'] = '.'.join(
            self.quote(namespace, schema.resource_name)
        )

        template = (
            'DELETE FROM {table}\n'
            'WHERE {where};'
        )

        if schema.has_translations:
            i18n_keys = await record.get_key_dict(key_property='i18n_code')
            i18n_pairs, i18n_values = generate_arg_pairs(
                i18n_keys,
                context=context,
                offset_index=len(values),
                quote=self.quote,
            )
            template_options['i18n_where'] = ' AND '.join(i18n_pairs)
            template_options['i18n_table'] = '.'.join(self.quote(
                namespace,
                schema.i18n_name,
            ))

            template = (
                'DELETE FROM {i18n_table}\n'
                'WHERE {i18n_where};\n'
            ) + template
        else:
            i18n_values = []

        sql = template.format(**template_options)
        result = await self.execute(
            sql,
            *values,
            *i18n_values,
            connection=context.connection,
        )
        return int(result.split(' ')[1])

    @abstractmethod
    async def execute(
        self,
        sql: str,
        *args,
        method: str = 'execute',
        connection: Any = None,
    ) -> bool:
        """Execute the given sql statement in this backend pool."""
        pass

    async def get_count(
        self,
        model: Type['anansi.Model'],
        context: 'anansi.Context'
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
        model: Type['anansi.Model'],
        context: 'anansi.Context'
    ) -> List[dict]:
        """Get records from the store based on the given context."""
        sql, values = await generate_select_statement(
            model.__schema__,
            context,
            default_namespace=self.default_namespace,
            quote=self.quote,
            resolve_order=self.resolve_order,
            resolve_query_op=self.resolve_query_op,
        )
        return await self.execute(
            sql,
            *values,
            method='fetch',
            connection=context.connection,
        )

    async def save_collection(
        self,
        collection: 'anansi.Collection',
        context: 'anansi.Context'
    ) -> int:
        """Save a collection of records to the database."""
        pass

    async def save_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
    ) -> dict:
        """Save record to backend database."""
        if record.is_new:
            return await self.create_record(record, context)
        else:
            return await self.update_record(record, context)

    async def update_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
    ) -> dict:
        """Insert new record into the database."""
        changes, i18n_changes = split_changes(
            record.__schema__.fields,
            record.local_changes,
        )
        if i18n_changes:
            return await self.update_i18n_record(
                record,
                context,
                changes,
                i18n_changes
            )
        else:
            return await self.update_standard_record(
                record,
                context,
                changes
            )

    async def update_i18n_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
        changes: dict,
        i18n_changes: dict
    ) -> dict:
        """Create new database record that has translatable fields."""
        raise NotImplementedError  # pragma: no cover

    async def update_standard_record(
        self,
        record: 'anansi.Model',
        context: 'anansi.Context',
        changes: dict
    ) -> dict:
        """Create a standard record in the database."""
        template = (
            'UPDATE {table} SET\n'
            '   {values}\n'
            'WHERE {where};'
        )
        schema = record.__schema__
        pairs, values = generate_arg_pairs(
            changes,
            context=context,
            quote=self.quote
        )
        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace
        )
        table = '.'.join(
            self.quote(namespace, schema.resource_name)
        )
        key = await record.get_key()
        where = context.where or record.make_fetch_query(key)
        where_sql, where_values = await generate_select_query(
            schema,
            make_context(where=where, store=context.store),
            offset_index=len(values),
            quote=self.quote,
            resolve_query_op=self.resolve_query_op,
        )
        values.extend(where_values)

        sql = template.format(
            values=', '.join(pairs),
            where=where_sql,
            table=table,
        )
        results = await self.execute(
            sql,
            *values,
            method='fetch',
            connection=context.connection,
        )

        return results[0] if results else {}

    @staticmethod
    @singlify
    def quote(*text: str) -> Union[tuple, str]:
        """Wrap text in quotes for this engine."""
        return ['`{}`'.format(t) for t in text]

    @staticmethod
    def resolve_order(order: Ordering) -> str:
        """Resolve ordering to a SQL string."""
        return order.value.upper()

    @staticmethod
    def resolve_query_op(op: Union[Query.Op, QueryGroup.Op]) -> str:
        """Resolve operator to a SQL string."""
        if op in (Query.Op.After, Query.Op.GreaterThan):
            return '>'
        elif op in (Query.Op.Before, Query.Op.LessThan):
            return '<'
        elif op == Query.Op.Contains:
            return 'LIKE'
        elif op == Query.Op.ContainsInsensitive:
            return 'ILIKE'
        elif op == Query.Op.IsIn:
            return 'IN'
        elif op == Query.Op.IsNot:
            return '!='
        elif op == Query.Op.IsNotIn:
            return 'NOT IN'
        elif op == Query.Op.GreaterThanOrEqual:
            return '>='
        elif op == Query.Op.LessThanOrEqual:
            return '<='
        elif op == Query.Op.Matches:
            return '~'
        elif op == QueryGroup.Op.And:
            return 'AND'
        elif op == QueryGroup.Op.Or:
            return 'OR'
        else:
            return '='
