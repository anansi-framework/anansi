"""Define Postgres backend store.  Requires pip install anansi[postgres]."""
from anansi import value_literal
from anansi.utils import singlify
from contextlib import asynccontextmanager
from typing import Any, Union
import asyncpg
import logging

from .abstract import (
    AbstractSqlStorage,
    generate_arg_lists,
    resolve_namespace
)


log = logging.getLogger(__name__)


class Postgres(AbstractSqlStorage):
    """Implement abstract store backend for PostgreSQL database."""

    def __init__(
        self,
        *,
        max_pool_size: int=10,
        min_pool_size: int=5,
        pool: 'asyncpg.Pool'=None,
        use_pool: bool=None,
        **base_options,
    ):
        base_options.setdefault('default_namespace', 'public')
        base_options.setdefault('port', 5432)
        super().__init__(**base_options)

        self.use_pool = use_pool if use_pool is not None else bool(pool)
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool = pool

    async def close(self):
        """Close connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def create_standard_record(
        self,
        schema: 'Schema',
        context: 'Context',
        changes: dict
    ) -> dict:
        """Create a standard record in the database."""
        template = (
            'INSERT INTO {table} (\n'
            '   {columns}\n'
            ')\n'
            'VALUES({values})\n'
            'RETURNING *;'
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

    async def create_i18n_record(
        self,
        schema: 'Schema',
        context: 'Context',
        changes: dict,
        i18n_changes: dict
    ) -> dict:
        """Create a translatable record in the database."""
        template = (
            'WITH standard AS (\n'
            '   INSERT INTO {table} (\n'
            '       {columns}\n'
            '   )\n'
            '   VALUES({values})\n'
            '   RETURNING *\n'
            '), i18n AS (\n'
            '   INSERT INTO {i18n_table} (\n'
            '       {i18n_columns}\n'
            '   )\n'
            '   SELECT {i18n_values} FROM standard\n'
            '   RETURNING *\n'
            ')\n'
            'SELECT standard.*, i18n.* FROM standard, i18n;'
        )

        column_sql, value_sql, values = generate_arg_lists(
            changes,
            context=context,
            quote=self.quote,
        )

        i18n_changes.setdefault('locale', context.locale)
        for field in schema.key_fields:
            i18n_changes[field.i18n_code] = value_literal(
                'standard."{}"'.format(field.code)
            )

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

        namespace = resolve_namespace(
            schema,
            context,
            default=self.default_namespace
        )

        table = '.'.join(self.quote(namespace, schema.resource_name))
        i18n_table = '.'.join(self.quote(namespace, schema.i18n_name))

        sql = template.format(
            columns=', '.join(column_sql),
            i18n_columns=', '.join(i18n_column_sql),
            i18n_values=', '.join(i18n_value_sql),
            i18n_table=i18n_table,
            namespace=namespace,
            values=', '.join(value_sql),
            table=table,
        )
        result = await self.execute(
            sql,
            *values,
            *i18n_values,
            connection=context.connection,
            method='fetch'
        )
        return result[0]

    async def execute(
        self,
        sql: str,
        *args,
        connection: Any=None,
        method: str='execute',
    ):
        """Execute the given sql statement in this backend pool."""
        log.info('psql=\n\n%s\n\nargs=%s\n-----', sql, args)
        async with self.get_connection(connection) as conn:
            func = getattr(conn, method)
            try:
                return await func(sql, *args)
            except Exception:
                print(args)
                log.exception(sql)
                raise

    @asynccontextmanager
    async def get_connection(self, connection: Any=None):
        """Return a connection for this database instance."""
        if connection is not None:
            yield connection
        elif self.use_pool:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    yield conn
        else:
            conn = await asyncpg.connect(
                database=self.database,
                host=self.host,
                loop=self.loop,
                password=self.password,
                port=self.port,
                user=self.username,
            )
            yield conn
            await conn.close()

    async def get_pool(self):
        """Return the connection pool for this backend."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                database=self.database,
                host=self.host,
                loop=self.loop,
                password=self.password,
                port=self.port,
                user=self.username,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
            )
        return self._pool

    @staticmethod
    @singlify
    def quote(*text: str) -> Union[tuple, str]:
        """Wrap text in quotes for this engine."""
        return ['"{}"'.format(t) for t in text]
