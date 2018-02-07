"""Define useful utility methods for manipulating sql calls."""
from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Type, Union

from anansi.actions.store import MakeStoreValue
from anansi.core.collection import Collection
from anansi.core.context import Ordering
from anansi.core.model import Model
from anansi.core.query import Query
from anansi.core.query_group import QueryGroup


DEFAULT_ORDER_MAP = {
    Ordering.Asc: 'ASC',
    Ordering.Desc: 'DESC'
}
DEFAULT_QUOTE = '`'
DEFAULT_OP_MAP = {
    Query.Op.After: '>',
    Query.Op.Before: '<',
    Query.Op.Contains: 'LIKE',
    Query.Op.ContainsInsensitive: 'ILIKE',
    Query.Op.Is: '=',
    Query.Op.IsIn: 'IN',
    Query.Op.IsNot: '!=',
    Query.Op.IsNotIn: 'NOT IN',
    Query.Op.GreaterThan: '>',
    Query.Op.GreaterThanOrEqual: '>=',
    Query.Op.LessThan: '<',
    Query.Op.LessThanOrEqual: '<=',
    Query.Op.Matches: '~',

    QueryGroup.Op.And: 'AND',
    QueryGroup.Op.Or: 'OR'
}


def args_to_sql(
    kwargs: dict,
    *,
    joiner: str=', ',
    quote: str=DEFAULT_QUOTE
) -> Tuple[str, list]:
    """Generate argument tuple from a dictionary."""
    pattern = '{q}{key}{q} = {value}'
    return (
        joiner.join(
            pattern.format(
                q=quote,
                key=key,
                value=getattr(
                    kwargs[key],
                    'literal_value',
                    '${}'.format(i + 1)
                )
            ) for i, key in enumerate(kwargs.keys())
        ),
        kwargs.values()
    )


def changes_to_sql(
    changes: Dict[Union['Field', str], Any],
    quote: str=DEFAULT_QUOTE,
    offset: int=0
) -> Tuple[str, str, list]:
    """Create change statements in sql."""
    column_str = ', '.join(
        '{0}{1}{0}'.format(quote, getattr(field, 'code', field))
        for field in changes.keys()
    )
    values = changes.values()
    value_str = ', '.join(
        getattr(value, 'literal_value', '${}'.format(i + 1 + offset))
        for i, value in enumerate(values)
    )
    return column_str, value_str, values


def group_changes(record: 'Model') -> Tuple[dict, dict]:
    """Group changes into standard and translatable fields."""
    standard = OrderedDict()
    i18n = OrderedDict()

    fields = record.__schema__.fields
    for field_name, (_, new_value) in sorted(record.local_changes.items()):
        field = fields[field_name]
        if field.test_flag(field.Flags.Translatable):
            i18n[field] = new_value
        else:
            standard[field] = new_value

    return standard, i18n


def fields_to_sql(
    model: Type['Model'],
    context: 'Context',
    *,
    quote: str=DEFAULT_QUOTE
) -> Tuple[List['Field'], List[str]]:
    """Extract fields and columns from the model and context."""
    schema = model.__schema__
    all_fields = schema.fields
    field_names = (
        context.fields if context.fields is not None
        else sorted(all_fields.keys())
    )
    fields = []
    columns = []
    for field_name in field_names:
        field = all_fields[field_name]
        fields.append(field)
        if field.code != field.name:
            key = '{prefix}{q}{code}{q} AS {q}{name}{q}'
        else:
            key = '{prefix}{q}{code}{q}'

        columns.append(key.format(
            code=field.code,
            name=field.name,
            prefix=(
                'i18n.' if field.test_flag(field.Flags.Translatable)
                else ''
            ),
            q=quote,
        ))

    return fields, columns


async def get_query_value(
    storage: 'AbstractStorage',
    model: Type['Model'],
    value: Any,
    context: 'Context',
    quote: str,
    values: list,
):
    """Convert given value to a storable query value."""
    try:
        field = model.__schema__.fields[value]
    except Exception as e:
        pass
    else:
        return '{0}{1}{0}'.format(quote, field.code)

    action = MakeStoreValue(value=value, context=context)
    action_value = await context.store.dispatch(action)

    if isinstance(action_value, Collection):
        statement = await storage.get_records_statement(
            action_value.model,
            action_value.context,
            values=values
        )
        return '({})'.format(statement)
    elif type(action_value) is tuple:
        base = len(values) + 1
        values.extend(action_value)
        return '({})'.format(
            ', '.join(
                '${}'.format(base + i)
                for i in range(len(action_value))
            )
        )
    elif action_value is None:
        return 'null'
    else:
        values.append(action_value)
        return getattr(
            action_value,
            'literal_value',
            '${}'.format(len(values))
        )


async def query_to_sql(
    storage: 'AbstractSql',
    model: Type['Model'],
    query: Union['Query', 'QueryGroup'],
    context: 'Context',
    *,
    quote: str=DEFAULT_QUOTE,
    op_map: Dict[Union[Query.Op, QueryGroup.Op], str]=DEFAULT_OP_MAP,
    values: list=None
) -> str:
    """Convert the Query object to a SQL statement."""
    if getattr(query, 'is_null', True):
        return ''
    elif isinstance(query, QueryGroup):
        joiner = op_map[query.op]
        sub_queries = []
        for sub_query in query.queries:
            sub_queries.append(
                await query_to_sql(
                    storage,
                    model,
                    sub_query,
                    context,
                    op_map=op_map,
                    quote=quote,
                    values=values
                )
            )
        return '({})'.format(' {} '.format(joiner).join(sub_queries))
    else:
        left = await get_query_value(
            storage,
            model,
            query.left,
            context,
            quote,
            values,
        )
        right = await get_query_value(
            storage,
            model,
            query.right,
            context,
            quote,
            values,
        )

        if query.op is Query.Op.Is and 'null' in (left, right):
            op = 'is'
        elif query.op is Query.Op.IsNot and 'null' in (left, right):
            op = 'is not'
        else:
            op = op_map[query.op]

        return '{} {} {}'.format(left, op, right)


def order_to_sql(
    model: Type['Model'],
    order: Dict[str, Ordering],
    *,
    order_map: Dict[Ordering, str]=DEFAULT_ORDER_MAP,
    quote: str=DEFAULT_QUOTE
) -> str:
    """Convert ordering information to SQL."""
    if not order:
        return ''

    fields = model.__schema__.fields
    return ', '.join(
        '{q}{field}{q} {order}'.format(
            field=fields[field_name].code,
            q=quote,
            order=order_map[ordering]
        ) for field_name, ordering in order
    )


async def sql_middleware(next):
    """Process action middleware for SQL stores."""
    async def handler(action):
        action_type = type(action)

        if action_type == MakeStoreValue:
            value = action.value
            if isinstance(value, Model):
                return await value.get_key()
            elif isinstance(value, (list, set)):
                return tuple(value)
            else:
                return value
        return await next(action)
    return handler
