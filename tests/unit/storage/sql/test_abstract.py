"""Test abstract sql storage class."""
import pytest

CREATE_RECORD_SQL = '''
INSERT INTO `test`.`contents` (
   `code`, `title`
)
VALUES($1, $2);
'''

CREATE_I18N_RECORD_SQL = '''
INSERT INTO `test`.`contents` (
   `code`
)
VALUES($1);
INSERT INTO `test`.`contents_i18n` (
   `title`, `locale`
)
VALUES($2, $3);
'''

DELETE_COLLECTION_SQL = '''
DELETE FROM `test`.`contents`
WHERE `id` in ($1, $2);
'''

DELETE_RECORD_SQL = '''
DELETE FROM `test`.`contents`
WHERE `id`=$1;
'''

DELETE_I18N_RECORD_SQL = '''
DELETE FROM `test`.`contents_i18n`
WHERE `id`=$2;
DELETE FROM `test`.`contents`
WHERE `id`=$1;
'''

GET_COUNT_SQL = '''
SELECT COUNT(*) AS `count`
FROM `test`.`contents`
WHERE `id` IN ($1, $2);
'''

GET_RECORDS_SQL = '''
SELECT `code`, `id`, `title`
FROM `test`.`contents`
WHERE `id` IN ($1, $2);
'''

UPDATE_RECORD_SQL = '''
UPDATE `test`.`contents` SET
   `code`=$1, `title`=$2
WHERE `id` = $3;
'''

UPDATE_I18N_RECORD_SQL = '''
UPDATE `test`.`contents` SET
   `code`=$1
WHERE `id` = $2;
UPDATE `test`.`contents_i18n` SET
    `title`=$3
WHERE `id` = $4, `locale` = $5;
'''


@pytest.fixture
def mock_sql_storage():
    """Define mock SQL storage class."""
    from anansi.storage.sql.abstract import AbstractSqlStorage

    class TestSqlStorage(AbstractSqlStorage):
        async def execute(self, sql, *args, method='execute', connection=None):
            pass

    return TestSqlStorage(default_namespace='test')


def test_abstract_sql_is_abstract():
    """Ensure that the abstract storage class cannot be instantiated."""
    from anansi.storage.sql.abstract import AbstractSqlStorage

    with pytest.raises(TypeError):
        AbstractSqlStorage()


@pytest.mark.asyncio
async def test_abstract_sql_create_record(
    mock_sql_storage,
    mocker,
):
    """Test create_record method."""
    from anansi import Model, Field, make_context

    class Content(Model):
        id = Field()
        code = Field()
        title = Field()

    async def create(schema, context, changes):
        pass

    mock_create = mocker.patch.object(
        mock_sql_storage,
        'create_standard_record',
        side_effect=create,
    )

    record = Content()
    context = make_context()
    assert await mock_sql_storage.create_record(record, context) == {}
    mock_create.assert_not_called()

    await record.set('title', 'testing')
    await record.set('code', 'testing')
    await mock_sql_storage.create_record(record, context)

    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_sql_create_record_with_translations(
    mock_sql_storage,
    mocker,
):
    """Test create_record method."""
    from anansi import Model, Field, make_context

    class Content(Model):
        id = Field()
        code = Field()
        title = Field(flags={'Translatable'})

    async def create(schema, context, changes, i18n_changes):
        pass

    mock_create = mocker.patch.object(
        mock_sql_storage,
        'create_i18n_record',
        side_effect=create,
    )

    record = Content()
    context = make_context()
    assert await mock_sql_storage.create_record(record, context) == {}
    mock_create.assert_not_called()
    await record.set('title', 'testing')
    await record.set('code', 'testing')
    await mock_sql_storage.create_record(record, context)
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_sql_create_i18n_record(mock_sql_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field()
        code = Field()
        title = Field(flags={'Translatable'})

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    await mock_sql_storage.create_i18n_record(
        Content.__schema__,
        make_context(),
        {'code': 'test'},
        {'title': 'Test'},
    )

    mock_execute.assert_called_with(
        CREATE_I18N_RECORD_SQL.strip(),
        'test',
        'Test',
        'en_US',
        connection=None,
        method='fetch',
    )


@pytest.mark.asyncio
async def test_abstract_sql_create_standard_record(mock_sql_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field()
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    await mock_sql_storage.create_standard_record(
        Content.__schema__,
        make_context(),
        {'code': 'test', 'title': 'Test'},
    )

    mock_execute.assert_called_with(
        CREATE_RECORD_SQL.strip(),
        'test',
        'Test',
        connection=None,
        method='fetch',
    )


@pytest.mark.xfail(reason='backend not implemented')
@pytest.mark.asyncio
async def test_abstract_sql_delete_collection(mock_sql_storage, mocker):
    """Test deleting a collection from sql."""
    from anansi import Model, Field, Query as Q, make_context

    async def execute(*args, **kwargs):
        return 'DELETED 2'

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    q = Q('id').is_in([1, 2])

    result = await mock_sql_storage.delete_collection(
        Content,
        make_context(where=q),
    )

    mock_execute.assert_called_with(
        DELETE_COLLECTION_SQL.strip(),
        1,
        2,
        connection=None,
        method='fetch',
    )
    assert result == 2


@pytest.mark.asyncio
async def test_abstract_sql_delete_record(mock_sql_storage, mocker):
    """Test deleting a collection from sql."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return 'DELETED 1'

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    result = await mock_sql_storage.delete_record(
        Content({'id': 1}),
        make_context(),
    )

    mock_execute.assert_called_with(
        DELETE_RECORD_SQL.strip(),
        1,
        connection=None,
    )
    assert result == 1


@pytest.mark.asyncio
async def test_abstract_sql_delete_record_with_translation(
    mock_sql_storage,
    mocker,
):
    """Test deleting a collection from sql."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return 'DELETED 1'

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field(flags={'Translatable'})

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    result = await mock_sql_storage.delete_record(
        Content({'id': 1}),
        make_context(),
    )

    mock_execute.assert_called_with(
        DELETE_I18N_RECORD_SQL.strip(),
        1,
        1,
        connection=None,
    )
    assert result == 1


@pytest.mark.asyncio
async def test_abstract_sql_get_count(mock_sql_storage, mocker):
    """Test get_count method."""
    from anansi import Model, Field, Query as Q, make_context

    async def execute(*args, **kwargs):
        return [{'count': 2}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    q = Q('id').is_in([1, 2])

    result = await mock_sql_storage.get_count(
        Content,
        make_context(where=q),
    )

    mock_execute.assert_called_with(
        GET_COUNT_SQL.strip(),
        1,
        2,
        connection=None,
        method='fetch',
    )
    assert result == 2


@pytest.mark.asyncio
async def test_abstract_sql_get_records(mock_sql_storage, mocker):
    """Test get_records method."""
    from anansi import Model, Field, Query as Q, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'a'}, {'id': 2, 'code': 'b'}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    q = Q('id').is_in([1, 2])

    result = await mock_sql_storage.get_records(
        Content,
        make_context(where=q),
    )

    mock_execute.assert_called_with(
        GET_RECORDS_SQL.strip(),
        1,
        2,
        connection=None,
        method='fetch',
    )
    assert result == [{'code': 'a', 'id': 1}, {'code': 'b', 'id': 2}]


@pytest.mark.asyncio
async def test_abstract_sql_update_record(
    mock_sql_storage,
    mocker,
):
    """Update standard record."""
    from anansi import Model, Field, make_context

    class Content(Model):
        id = Field()
        code = Field()
        title = Field()

    async def update(record, context, changes):
        pass

    mock_update = mocker.patch.object(
        mock_sql_storage,
        'update_standard_record',
        side_effect=update,
    )

    record = Content(state={'id': 1, 'title': 'test', 'code': 'test'})
    context = make_context()

    await record.set('title', 'testing')
    await record.set('code', 'testing')
    await mock_sql_storage.update_record(record, context)

    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_sql_save_record(
    mock_sql_storage,
    mocker,
):
    """Save record."""
    from anansi import Model, Field, make_context

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field(flags={'Translatable'})

    async def action(record, context):
        pass

    mock_create = mocker.patch.object(
        mock_sql_storage,
        'create_record',
        side_effect=action,
    )

    mock_update = mocker.patch.object(
        mock_sql_storage,
        'update_record',
        side_effect=action,
    )

    a = Content(state={'id': 1}, values={'code': 'Test'})
    b = Content(values={'code': 'Test'})

    context = make_context()

    assert not a.is_new
    assert b.is_new

    mock_create.assert_not_called()
    mock_update.assert_not_called()

    await mock_sql_storage.save_record(a, context)
    await mock_sql_storage.save_record(b, context)

    mock_create.assert_called_once()
    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_sql_update_record_with_translation(
    mock_sql_storage,
    mocker,
):
    """Update standard record."""
    from anansi import Model, Field, make_context

    class Content(Model):
        id = Field()
        code = Field()
        title = Field(flags={'Translatable'})

    async def update(record, context, changes, i18n_changes):
        pass

    mock_update = mocker.patch.object(
        mock_sql_storage,
        'update_i18n_record',
        side_effect=update,
    )

    record = Content(state={'id': 1, 'title': 'test', 'code': 'test'})
    context = make_context()

    await record.set('title', 'testing')
    await record.set('code', 'testing')
    await mock_sql_storage.update_record(record, context)

    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_abstract_sql_update_standard_record(mock_sql_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    record = Content(state={'id': 1})

    await mock_sql_storage.update_standard_record(
        record,
        make_context(),
        {'code': 'test', 'title': 'Test'},
    )

    mock_execute.assert_called_with(
        UPDATE_RECORD_SQL.strip(),
        'test',
        'Test',
        1,
        connection=None,
        method='fetch',
    )


@pytest.mark.asyncio
@pytest.mark.xfail(reason='not implemented yet')
async def test_abstract_sql_update_i18n_record(mock_sql_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field(flags={'Translatable'})

    mock_execute = mocker.patch.object(
        mock_sql_storage,
        'execute',
        side_effect=execute,
    )

    record = Content(state={'id': 1})

    await mock_sql_storage.update_i18n_record(
        record,
        make_context(),
        {'code': 'test', 'title': 'Test'},
    )

    mock_execute.assert_called_with(
        UPDATE_I18N_RECORD_SQL.strip(),
        'test',
        'Test',
        1,
        connection=None,
        method='fetch',
    )


def test_abstract_sql_quote():
    """Test quoting strings."""
    from anansi.storage.sql.abstract import AbstractSqlStorage

    result = '.'.join(
        AbstractSqlStorage.quote('test', 'words')
    )
    assert AbstractSqlStorage.quote('test') == '`test`'
    assert result == '`test`.`words`'


@pytest.mark.parametrize('order,expected', (
    ('Asc', 'ASC'),
    ('Desc', 'DESC'),
))
def test_abstract_sql_resolve_order(order, expected):
    """Test order resolution."""
    from anansi import Ordering
    from anansi.storage.sql.abstract import AbstractSqlStorage

    order = Ordering[order]
    assert AbstractSqlStorage.resolve_order(order) == expected


@pytest.mark.parametrize('op,expected', (
    ('After', '>'),
    ('And', 'AND'),
    ('Before', '<'),
    ('Contains', 'LIKE'),
    ('ContainsInsensitive', 'ILIKE'),
    ('GreaterThan', '>'),
    ('GreaterThanOrEqual', '>='),
    ('Is', '='),
    ('IsIn', 'IN'),
    ('IsNot', '!='),
    ('IsNotIn', 'NOT IN'),
    ('LessThan', '<'),
    ('LessThanOrEqual', '<='),
    ('Matches', '~'),
    ('Or', 'OR'),
))
def test_abstract_sql_resolve_query_op(op, expected):
    """Test order resolution."""
    from anansi import Query, QueryGroup
    from anansi.storage.sql.abstract import AbstractSqlStorage

    try:
        op = Query.Op[op]
    except KeyError:
        op = QueryGroup.Op[op]
    assert AbstractSqlStorage.resolve_query_op(op) == expected
