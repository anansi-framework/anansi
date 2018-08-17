"""Define useful utility methods for manipulating sql calls."""
from anansi.core.collection import Collection
from anansi.core.context import (
    ReturnType,
    make_context,
    resolve_namespace,
)
from anansi.core.field import Field
from anansi.core.model import Model
from anansi.core.query_group import QueryGroup

from collections import OrderedDict
from typing import Any, Callable, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import anansi

I18N_PREFIX = 'i18n.'


def generate_arg_lists(
    args: dict,
    *,
    context: 'anansi.Context' = None,
    field_key: str = 'code',
    offset_index: int = 0,
    quote: Callable = None,
) -> Tuple[List[str], List[str], List[Any]]:
    """Convert dictionary to key / value SQL lists."""
    column_sql = []
    value_sql = []
    out_values = []

    for i, (field, value) in enumerate(args.items()):
        column_sql.append(quote(getattr(field, field_key, field)))
        if hasattr(value, 'literal_value'):
            value_sql.append(str(value.literal_value))
        else:
            try:
                dump_value = getattr(value, 'dump_value')
            except AttributeError:
                out_value = value
            else:
                out_value = dump_value(value, context=context)
            out_values.append(out_value)
            value_sql.append('${}'.format(len(out_values) + offset_index))

    return column_sql, value_sql, out_values


def generate_arg_pairs(
    args: dict,
    *,
    context: 'anansi.Context' = None,
    field_key: str = 'code',
    offset_index: int = 0,
    quote: Callable = None,
) -> Tuple[List[str], List[Any]]:
    """Convert dictionary to key / value SQL pair."""
    column_sql, value_sql, out_values = generate_arg_lists(
        args,
        context=context,
        field_key=field_key,
        offset_index=offset_index,
        quote=quote,
    )
    pairs = list(
        map(lambda x: '{}={}'.format(*x), zip(column_sql, value_sql)),
    )
    return pairs, out_values


def generate_select_columns(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    quote: Callable = None,
) -> Tuple[str, List['Field']]:
    """Generate field and sql column lists."""
    if context.returning == ReturnType.Count:
        return 'COUNT(*) AS {}'.format(quote('count')), []

    all_fields = schema.fields
    field_names = (
        context.fields if context.fields is not None
        else sorted(all_fields.keys())
    )
    columns = []
    fields = []
    for name in field_names:
        field = all_fields[name]
        if field.test_flag(field.Flags.Virtual):
            continue

        fields.append(field)
        i18n = field.test_flag(field.Flags.Translatable)

        prefix = '' if not i18n else I18N_PREFIX
        code = field.code if not i18n else field.i18n_code

        if code != name:
            column = ' AS '.join(quote(code, name))
        else:
            column = quote(code)

        columns.append(prefix + column)

    return ', '.join(columns), fields


def generate_select_distinct(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    quote: Callable = None,
):
    """Generate distinct lookup for the context information."""
    if not context.distinct:
        return ''
    elif context.distinct is True:
        return 'DISTINCT '

    all_fields = schema.fields
    columns = []
    for name in sorted(context.distinct):
        field = all_fields[name]
        if field.test_flag(field.Flags.Virtual):
            continue
        i18n = field.test_flag(field.Flags.Translatable)
        prefix = '' if not i18n else I18N_PREFIX
        code = field.code if not i18n else field.i18n_code
        columns.append(prefix + quote(code))

    return 'DISTINCT ON ({}) '.format(', '.join(columns))


def generate_select_order(
    schema,
    context,
    *,
    quote: Callable = None,
    resolve_order: Callable = None,
) -> str:
    """Genreate order by clause for select statement."""
    order_by = context.order_by
    if not order_by:
        return ''

    all_fields = schema.fields
    ordering = []
    for name, order in order_by:
        field = all_fields[name]
        if field.test_flag(field.Flags.Virtual):
            continue
        i18n = field.test_flag(field.Flags.Translatable)
        prefix = '' if not i18n else I18N_PREFIX
        code = field.code if not i18n else field.i18n_code
        ordering.append('{}{} {}'.format(
            prefix,
            quote(code),
            resolve_order(order)
        ))
    return 'ORDER BY {}'.format(', '.join(ordering))


async def generate_select_query(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    *,
    default_namespace: str = '',
    offset_index: int = 0,
    quote: Callable = None,
    resolve_order: Callable = None,
    resolve_query_op: Callable = None,
) -> Tuple[str, list]:
    """Generate a where query statement from the context."""
    where = context.where
    values = []
    if where is None or getattr(where, 'is_null', True):
        return '', []
    elif type(where) is QueryGroup:
        sub_queries = []
        for query in where.queries:
            sub_context = make_context(context=context)
            sub_context.where = query
            sub_sql, sub_values = await generate_select_query(
                schema,
                sub_context,
                default_namespace=default_namespace,
                offset_index=len(values) + offset_index,
                quote=quote,
                resolve_query_op=resolve_query_op,
                resolve_order=resolve_order,
            )
            if sub_sql:
                sub_queries.append(sub_sql)
                values.extend(sub_values)
        joiner = ' {} '.format(resolve_query_op(where.op))
        sql = '({})'.format(joiner.join(sub_queries))
        return sql, values
    else:
        left = where.get_left_for_schema(schema)
        right = where.get_right_for_schema(schema)

        left_sql, left_values = await make_store_value(
            schema,
            context,
            left,
            default_namespace=default_namespace,
            offset_index=len(values) + offset_index,
            quote=quote,
            resolve_order=resolve_order,
            resolve_query_op=resolve_query_op,
        )
        values.extend(left_values)
        right_sql, right_values = await make_store_value(
            schema,
            context,
            right,
            default_namespace=default_namespace,
            offset_index=len(values) + offset_index,
            quote=quote,
            resolve_order=resolve_order,
            resolve_query_op=resolve_query_op,
        )
        values.extend(right_values)
        if 'null' in (left_sql, right_sql):
            op = where.op.value
        else:
            op = resolve_query_op(where.op)
        return ' '.join((left_sql, op, right_sql)), values


def generate_select_translation(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    fields: List['Field'],
    *,
    namespace: str = '',
    offset_index: int = 0,
    quote: Callable = None,
) -> Tuple[str, list]:
    """Generate translation statement for select."""
    has_translations = any(
        field.test_flag(field.Flags.Translatable)
        for field in fields
    )
    if not has_translations:
        return '', []

    template = (
        'LEFT JOIN {table} AS {prefix} '
        'ON ({columns})'
    )
    table = '.'.join(quote(namespace, schema.i18n_name))
    columns = ' AND '.join(
        '{0}{1} = {2}'.format(I18N_PREFIX, *quote(field.i18n_code, field.code))
        for field in schema.key_fields
    )
    columns += ' AND {0}{1} = ${2}'.format(
        I18N_PREFIX,
        quote('locale'),
        offset_index + 1,
    )
    sql = template.format(
        table=table,
        columns=columns,
        prefix=I18N_PREFIX.strip('.'),
    )
    return sql, [context.locale]


async def generate_select_statement(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    *,
    default_namespace: str = None,
    offset_index: int = 0,
    quote: Callable = None,
    resolve_order: Callable = None,
    resolve_query_op: Callable = None,
) -> Tuple[str, list]:
    """Generate SQL selection statement."""
    values = []
    template = (
        'SELECT {distinct}{columns}\n'
        'FROM {table}\n'
        '{i18n}'
        '{where}'
        '{order}'
        '{start}'
        '{limit}'
    )
    namespace = resolve_namespace(
        schema,
        context,
        default=default_namespace
    )
    table = '.'.join(quote(namespace, schema.resource_name))
    columns, fields = generate_select_columns(schema, context, quote=quote)
    distinct = generate_select_distinct(schema, context, quote=quote)
    i18n, i18n_values = generate_select_translation(
        schema,
        context,
        fields,
        namespace=namespace,
        offset_index=offset_index,
        quote=quote,
    )
    values.extend(i18n_values)
    query, query_values = await generate_select_query(
        schema,
        context,
        default_namespace=default_namespace,
        offset_index=len(values) + offset_index,
        quote=quote,
        resolve_query_op=resolve_query_op,
    )
    values.extend(query_values)
    order = generate_select_order(
        schema,
        context,
        quote=quote,
        resolve_order=resolve_order,
    )
    where = 'WHERE {}'.format(query) if query else ''
    start = 'START {}'.format(context.start) if context.start else ''
    limit = 'LIMIT {}'.format(context.limit) if context.limit else ''
    sql = template.format(
        columns=columns,
        distinct=distinct,
        i18n=i18n + '\n' if i18n else '',
        where=where + '\n' if where else '',
        order=order + '\n' if order else '',
        start=start + '\n' if start else '',
        limit=limit,
        table=table,
    ).strip() + ';'

    return sql, values


async def make_store_value(
    schema: 'anansi.Schema',
    context: 'anansi.Context',
    value: Any,
    *,
    default_namespace: str = '',
    offset_index: int = 0,
    quote: Callable = None,
    resolve_order: Callable = None,
    resolve_query_op: Callable = None,
) -> Tuple[str, list]:
    """Convert given value to a storable query value."""
    action_value = value

    if isinstance(action_value, Field):
        i18n = action_value.test_flag(Field.Flags.Translatable)
        prefix = '' if not i18n else I18N_PREFIX
        code = action_value.code if not i18n else action_value.i18n_code
        return quote(prefix + code), []

    elif isinstance(action_value, Collection):
        select, select_values = await generate_select_statement(
            action_value.model.__schema__,
            action_value.context,
            offset_index=offset_index,
            quote=quote,
            default_namespace=default_namespace,
            resolve_order=resolve_order,
            resolve_query_op=resolve_query_op,
        )
        select = '({})'.format(select.strip(';'))
        return select, select_values

    elif isinstance(action_value, Model):
        key = await value.get_key()
        if type(key) is list:
            base = offset_index + 1
            holders = ('${}'.format(base + i) for i in range(len(key)))
            sql = '({})'.format(', '.join(holders))
            return sql, key
        return '${}'.format(offset_index + 1), [key]

    elif type(action_value) in (tuple, list, set):
        base = offset_index + 1
        holders = ('${}'.format(base + i) for i in range(len(action_value)))
        sql = '({})'.format(', '.join(holders))
        return sql, action_value

    elif action_value is None:
        return 'null', []

    elif hasattr(action_value, 'literal_value'):
        return str(action_value.literal_value), []

    else:
        return '${}'.format(offset_index + 1), [action_value]


def split_changes(fields: list, changes: dict) -> Tuple[dict, dict]:
    """Group changes into standard and translatable fields."""
    standard = OrderedDict()
    i18n = OrderedDict()

    for field_name, (_, new_value) in sorted(changes.items()):
        field = fields[field_name]
        if field.test_flag(field.Flags.Translatable):
            i18n[field] = new_value
        else:
            standard[field] = new_value

    return standard, i18n
