"""Test Postgres SQL backend."""
import pytest

CREATE_RECORD_SQL = '''
INSERT INTO "public"."contents" (
   "code", "title"
)
VALUES($1, $2)
RETURNING *;
'''

CREATE_I18N_RECORD_SQL = '''
WITH standard AS (
   INSERT INTO "public"."contents" (
       "code"
   )
   VALUES($1)
   RETURNING *
), i18n AS (
   INSERT INTO "public"."contents_i18n" (
       "title", "locale", "id"
   )
   SELECT $2, $3, standard."id" FROM standard
   RETURNING *
)
SELECT standard.*, i18n.* FROM standard, i18n;
'''


@pytest.fixture
def mock_pg_storage():
    """Define mock SQL storage class."""
    from anansi.storage.sql.postgres import Postgres
    return Postgres()


def test_postgres_base_configuration():
    """Test basic configuration for storage."""
    from anansi.storage.sql.postgres import Postgres

    storage = Postgres()
    assert storage.default_namespace == 'public'
    assert storage.port == 5432


@pytest.mark.asyncio
async def test_postgres_create_standard_record(mock_pg_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field()

    mock_execute = mocker.patch.object(
        mock_pg_storage,
        'execute',
        side_effect=execute,
    )

    await mock_pg_storage.create_standard_record(
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


@pytest.mark.asyncio
async def test_postgres_create_i18n_record(mock_pg_storage, mocker):
    """Test create a new internationalization record."""
    from anansi import Model, Field, make_context

    async def execute(*args, **kwargs):
        return [{'id': 1, 'code': 'test', 'title': 'Test'}]

    class Content(Model):
        id = Field(flags={'Key'})
        code = Field()
        title = Field(flags={'Translatable'})

    mock_execute = mocker.patch.object(
        mock_pg_storage,
        'execute',
        side_effect=execute,
    )

    await mock_pg_storage.create_i18n_record(
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
async def test_postgres_execute(mock_pg_storage, mocker):
    """Test getting a connection pool."""
    from anansi.storage.sql.postgres import Postgres

    class Transaction:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def transaction(self):
            return Transaction()

        async def execute(self, sql, *args):
            return 'executed', sql, args

        async def fetch(self, sql, *args):
            return 'fetched', sql, args

        async def raise_(self, sql, *args):
            raise RuntimeError()

    class Pool:
        def acquire(self):
            return Connection()

    async def get_pool(*args, **kw):
        return Pool()

    mocker.patch('asyncpg.create_pool', side_effect=get_pool)
    kw = {
        'database': 'testing',
        'host': '255.255.255.0',
        'password': 'p@ss',
        'port': 1234,
    }
    pg = Postgres(username='user', use_pool=True, **kw)

    result = await pg.execute('test')
    assert result == ('executed', 'test', tuple())

    result = await pg.execute('test', 1, 2)
    assert result == ('executed', 'test', (1, 2))

    result = await pg.execute('test', method='fetch')
    assert result == ('fetched', 'test', tuple())

    conn = Connection()
    result = await pg.execute('test', connection=conn)
    assert result == ('executed', 'test', tuple())

    with pytest.raises(RuntimeError):
        await pg.execute('test', method='raise_')

    with pytest.raises(RuntimeError):
        await pg.execute('test', method='raise_', connection=conn)


@pytest.mark.asyncio
async def test_postgres_get_pool(mock_pg_storage, mocker):
    """Test getting a connection pool."""
    from anansi.storage.sql.postgres import Postgres

    async def async_mock(*args, **kw):
        return {'id': 1}

    mock_pool = mocker.patch('asyncpg.create_pool', side_effect=async_mock)
    kw = {
        'database': 'testing',
        'host': '255.255.255.0',
        'password': 'p@ss',
        'port': 1234,
        'loop': 'test',
    }
    pg = Postgres(
        username='user',
        min_pool_size=5,
        max_pool_size=10,
        **kw,
    )
    pool = await pg.get_pool()
    mock_pool.assert_called_once()
    mock_pool.assert_called_with(
        user='user',
        min_size=5,
        max_size=10,
        **kw,
    )
    pool2 = await pg.get_pool()
    assert pool is pool2
    mock_pool.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_get_connection(mock_pg_storage, mocker):
    """Test getting a connection pool."""
    from anansi.storage.sql.postgres import Postgres

    class Connection:
        async def close(self):
            pass

    async def async_mock(*args, **kw):
        return Connection()

    mock_connect = mocker.patch('asyncpg.connect', side_effect=async_mock)
    kw = {
        'database': 'testing',
        'host': '255.255.255.0',
        'password': 'p@ss',
        'port': 1234,
        'loop': 'test',
    }
    pg = Postgres(
        username='user',
        **kw,
    )
    async with pg.get_connection():
        mock_connect.assert_called_with(
            user='user',
            **kw,
        )
        mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_connection_closing(mocker):
    """Test closing postgres connections."""
    from anansi.storage.sql.postgres import Postgres

    class Pool:
        async def close(self):
            pass

    async def close():
        pass

    pool = Pool()
    mock_close = mocker.patch.object(pool, 'close', side_effect=close)

    pg = Postgres(pool=pool)
    await pg.close()
    mock_close.assert_called_once()


def test_postgres_quote():
    """Test quoting strings."""
    from anansi.storage.sql.postgres import Postgres

    result = '.'.join(
        Postgres.quote('test', 'words')
    )
    assert Postgres.quote('test') == '"test"'
    assert result == '"test"."words"'
