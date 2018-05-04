"""Test SQL utility methods."""
import pytest


@pytest.mark.parametrize('args,kw,col_sql,value_sql,values', (
    (
        {'a': 1},
        {'quote': '`{}`'.format},
        ['`a`'],
        ['$1'],
        [1],
    ),
    (
        {'a': 1},
        {'quote': '`{}`'.format, 'offset_index': 1},
        ['`a`'],
        ['$2'],
        [1],
    ),
))
def test_sql_utils_generate_arg_list(args, kw, col_sql, value_sql, values):
    """Test converting values to SQL lists."""
    from anansi.storage.sql.utils import generate_arg_lists

    a, b, c = generate_arg_lists(args, **kw)
    assert col_sql == a
    assert value_sql == b
    assert values == c


def test_sql_utils_generate_arg_lists_with_literals():
    """Test converting values to SQL lists using literal valus."""
    from anansi import value_literal
    from anansi.storage.sql.utils import generate_arg_lists

    column_sql, value_sql, values = generate_arg_lists(
        {'a': value_literal(1)},
        quote='`{}`'.format,
    )
    assert column_sql == ['`a`']
    assert value_sql == ['1']
    assert values == []


@pytest.mark.parametrize('args,kw,pairs,values', (
    (
        {'a': 1},
        {'quote': '`{}`'.format},
        ['`a`=$1'],
        [1],
    ),
    (
        {'a': 1},
        {'quote': '`{}`'.format, 'offset_index': 1},
        ['`a`=$2'],
        [1],
    ),
))
def test_sql_utils_generate_arg_pairs(args, kw, pairs, values):
    """Test converting values to SQL lists."""
    from anansi.storage.sql.utils import generate_arg_pairs

    a, b = generate_arg_pairs(args, **kw)
    assert a == pairs
    assert b == values


def test_sql_utils_generate_arg_pairs_with_literals():
    """Test converting values to SQL lists using literal valus."""
    from anansi import value_literal
    from anansi.storage.sql.utils import generate_arg_pairs

    pairs_sql, values = generate_arg_pairs(
        {'a': value_literal(1)},
        quote='`{}`'.format,
    )
    assert pairs_sql == ['`a`=1']
    assert values == []


@pytest.mark.parametrize('fields,expected', (
    (
        None,
        'i18n.display_name AS display, first_name, '
        'id, last_name, user AS username',
    ),
    ('display', 'i18n.display_name AS display'),
    ('first_name,last_name', 'first_name, last_name'),
    (['last_name', 'first_name'], 'last_name, first_name'),
))
def test_sql_utils_generate_select_columns(fields, expected):
    """Test generating columns to use for selection."""
    from anansi import Model, Field, make_context
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_columns

    class User(Model):
        id = Field()
        username = Field(code='user')
        first_name = Field()
        last_name = Field()
        display = Field(i18n_code='display_name', flags={'Translatable'})

    schema = User.__schema__
    if fields:
        context = make_context(fields=fields)
    else:
        context = make_context()

    @singlify
    def quote(*text):
        return text

    sql, _ = generate_select_columns(schema, context, quote=quote)
    assert sql == expected


def test_sql_utils_generate_select_columns_count():
    """Test generating columns to use for selection."""
    from anansi import Model, Field, make_context
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_columns

    class User(Model):
        id = Field()
        username = Field(code='user')
        first_name = Field()
        last_name = Field()
        display = Field(i18n_code='display_name', flags={'Translatable'})

    schema = User.__schema__
    context = make_context(returning='count')

    @singlify
    def quote(*text):
        return text

    sql, _ = generate_select_columns(schema, context, quote=quote)
    assert sql == 'COUNT(*) AS count'


@pytest.mark.parametrize('distinct,expected', (
    (None, ''),
    (True, 'DISTINCT '),
    (['last_name', 'first_name'], 'DISTINCT ON (first_name, last_name) '),
    (['display'], 'DISTINCT ON (i18n.display) ')
))
def test_sql_utils_generate_select_distinct(distinct, expected):
    """Test generating the select distinct SQL text."""
    from anansi import Model, Field, make_context
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_distinct

    class User(Model):
        id = Field()
        username = Field()
        first_name = Field()
        last_name = Field()
        display = Field(flags={'Translatable'})

    schema = User.__schema__
    context = make_context(distinct=distinct)

    @singlify
    def quote(*text):
        return text

    result = generate_select_distinct(schema, context, quote=quote)
    assert result == expected


@pytest.mark.parametrize('order,expected', (
    (None, ''),
    ('+first_name,-last_name', 'ORDER BY first_name ASC, last_name DESC'),
    ('+first_name', 'ORDER BY first_name ASC'),
    ('-last_name', 'ORDER BY last_name DESC'),
))
def test_sql_utils_generate_select_order(order, expected):
    """Test generating the select distinct SQL text."""
    from anansi import Model, Field, make_context
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_order

    class User(Model):
        id = Field()
        username = Field()
        first_name = Field()
        last_name = Field()
        display = Field(flags={'Translatable'})

    schema = User.__schema__
    context = make_context(order_by=order)

    @singlify
    def quote(*text):
        return text

    def resolve(order):
        return order.value.upper()

    result = generate_select_order(
        schema,
        context,
        quote=quote,
        resolve_order=resolve,
    )
    assert result == expected


@pytest.mark.parametrize('field_names,expected_sql,expected_values', (
    ('id', '', []),
    (
        'display',
        'LEFT JOIN test.users_i18n AS i18n '
        'ON (i18n.id = id AND i18n.locale = $1)',
        ['en_US'],
    ),
))
def test_sql_utils_generate_select_translation(
    field_names,
    expected_sql,
    expected_values,
):
    """Test generating the select distinct SQL text."""
    from anansi import Model, Field, make_context
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_translation

    class User(Model):
        id = Field(flags={'Key'})
        username = Field()
        first_name = Field()
        last_name = Field()
        display = Field(flags={'Translatable'})

    schema = User.__schema__
    context = make_context(fields=field_names)
    fields = [schema[field_name] for field_name in field_names.split(',')]

    @singlify
    def quote(*text):
        return text

    sql, values = generate_select_translation(
        schema,
        context,
        fields,
        namespace='test',
        quote=quote,
    )
    assert sql == expected_sql
    assert values == expected_values


@pytest.mark.asyncio
@pytest.mark.parametrize('value,expected_sql,expected_values', (
    ('test', '$1', ['test']),
    (None, 'null', []),
    ([1, 2, 3], '($1, $2, $3)', [1, 2, 3]),
    ((1, 2, 3), '($1, $2, $3)', (1, 2, 3)),
    ({1}, '($1)', {1}),
))
async def test_sql_utils_make_store_value(
    value,
    expected_sql,
    expected_values,
):
    """Test generating the store value."""
    from anansi import Model, Field, Store, make_context
    from anansi.storage.sql.utils import make_store_value

    class User(Model):
        id = Field()
        username = Field()
        display = Field()

    schema = User.__schema__
    context = make_context(store=Store())

    sql, values = await make_store_value(
        schema,
        context,
        value,
    )

    assert sql == expected_sql
    assert values == expected_values


@pytest.mark.asyncio
async def test_sql_utils_make_store_value_for_collection(mocker):
    """Test generating the store value."""
    from anansi import Collection, Model, Field, Store, make_context
    from anansi.storage.sql.utils import make_store_value

    async def select(*args, **kw):
        return 'SELECT * FROM test;', []

    mock_select = mocker.patch(
        'anansi.storage.sql.utils.generate_select_statement',
        side_effect=select,
    )

    class User(Model):
        id = Field()
        username = Field()
        display = Field()

    schema = User.__schema__
    context = make_context(store=Store())

    coll = Collection(model=User)

    sql, values = await make_store_value(
        schema,
        context,
        coll,
    )

    mock_select.assert_called_once()
    assert sql == '(SELECT * FROM test)'
    assert values == []


@pytest.mark.asyncio
async def test_sql_utils_make_store_value_for_model():
    """Test generating the store value."""
    from anansi import Model, Field, Store, make_context
    from anansi.storage.sql.utils import make_store_value

    class User(Model):
        id = Field(flags={'Key'})
        username = Field()
        display = Field()

    schema = User.__schema__
    context = make_context(store=Store())

    record = User({'id': 1})

    sql, values = await make_store_value(
        schema,
        context,
        record,
    )

    assert sql == '$1'
    assert values == [1]


@pytest.mark.asyncio
async def test_sql_utils_make_store_value_for_model_with_multi_key():
    """Test generating the store value."""
    from anansi import Model, Field, Index, Store, make_context
    from anansi.storage.sql.utils import make_store_value

    class UserGroup(Model):
        user_id = Field()
        group_id = Field()

        by_user_and_group = Index(
            ('user_id', 'group_id'),
            flags={'Key'},
        )

    schema = UserGroup.__schema__
    context = make_context(store=Store())

    record = UserGroup({'user_id': 1, 'group_id': 2})

    sql, values = await make_store_value(
        schema,
        context,
        record,
        offset_index=1,
    )

    assert sql == '($2, $3)'
    assert values == [1, 2]


@pytest.mark.asyncio
async def test_sql_utils_make_store_value_for_model_with_literal():
    """Test generating the store value."""
    from anansi import Model, Field, Store, make_context, value_literal
    from anansi.storage.sql.utils import make_store_value

    class User(Model):
        id = Field()

    schema = User.__schema__
    context = make_context(store=Store())

    sql, values = await make_store_value(
        schema,
        context,
        value_literal('test'),
        offset_index=1,
    )

    assert sql == 'test'
    assert values == []


@pytest.mark.asyncio
@pytest.mark.parametrize('where,expected_sql,expected_values', (
    (None, '', []),
    ({}, '', []),
    ({'username': None}, 'username is null', []),
    ({'username': 'john.doe'}, 'username = $1', ['john.doe']),
    (
        {'last_name': 'Doe', 'first_name': 'John'},
        '(last_name = $1 and first_name = $2)',
        ['Doe', 'John']
    ),
))
async def test_sql_utils_generate_select_query(
    where,
    expected_sql,
    expected_values,
):
    """Generate select where statement."""
    from anansi import (
        Model,
        Field,
        Store,
        make_context,
        make_query_from_values,
    )
    from anansi.utils import singlify
    from anansi.storage.sql.utils import generate_select_query

    class User(Model):
        id = Field()
        username = Field()
        first_name = Field()
        last_name = Field()

    @singlify
    def quote(*text):
        return text

    def resolve_query_op(op):
        if op.value == 'and':
            return op.value
        return '='

    if where is not None:
        where = make_query_from_values(where)

    schema = User.__schema__
    context = make_context(where=where, store=Store())

    sql, values = await generate_select_query(
        schema,
        context,
        quote=quote,
        resolve_query_op=resolve_query_op,
    )

    assert sql == expected_sql
    assert values == expected_values
