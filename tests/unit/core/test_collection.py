"""Tests for the Collection class."""
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('records,expected_count', (
    ([], 0),
    ([1, 2], 2),
))
async def test_collection_counter(records, expected_count):
    """Test counter function."""
    from anansi import Collection

    coll = Collection(records=records)
    assert hasattr(coll, '_count') is False
    count = await coll.get_count()
    assert hasattr(coll, '_count') is True
    assert count == expected_count
    assert await coll.get_count() == count


@pytest.mark.asyncio
async def test_collection_counter_wihout_store():
    """Test for raising error with empty collection."""
    from anansi import Collection
    from anansi.exceptions import StoreNotFound

    coll = Collection(records=None)
    with pytest.raises(StoreNotFound):
        await coll.get_count()


@pytest.mark.asyncio
async def test_collection_getter():
    """Test collection getter method."""
    from anansi import Collection

    c = Collection(records=[1, 3, 2])
    assert await c.get('first') == 1
    assert await c.get('count') == 3
    assert await c.get('last') == 2
    assert await c.get('records') == [1, 3, 2]


@pytest.mark.asyncio
async def test_collection_nested_getter():
    """Test collection nested getter."""
    from anansi import Model, Collector, Field

    class User(Model):
        username = Field()
        employees = Collector(model='User')

    coll = User.__schema__.collectors['employees']
    c = coll.make_collection(records=[User(values={'username': 'bob'})])
    assert await c.get('first.username') == 'bob'


@pytest.mark.asyncio
@pytest.mark.parametrize('records', (
    [],
))
async def test_collection_with_empty_records(records):
    """Test responses for an empty collection with defined records."""
    from anansi import Collection

    c = Collection(records=records)
    assert await c.get('first') is None
    assert await c.get('last') is None
    assert await c.get('username') == []


@pytest.mark.asyncio
@pytest.mark.parametrize('value,expected', (
    ('tom', ['tom', 'tom']),
    (['jack', 'jill'], ['jack', 'jill']),
))
async def test_collection_setting_values(value, expected):
    """Test setting record values."""
    from anansi import Model, Field, Collection

    class User(Model):
        username = Field()

    coll = Collection(records=[
        User(values={'username': 'bob'}),
        User(values={'username': 'john'})
    ])

    assert await coll.get('username') == ['bob', 'john']
    await coll.set('username', value)
    assert await coll.get('username') == expected


@pytest.mark.xfail(reason='TODO(issue-#11)')
@pytest.mark.asyncio
@pytest.mark.parametrize('value,expected', (
    ('tom', ['tom', 'tom']),
    (['jack', 'jill'], ['jack', 'jill']),
))
async def test_collection_setting_values_from_store(value, expected):
    """Test setting record values."""
    from anansi import Model, Field, Collection

    class User(Model):
        username = Field()

    coll = Collection(model=User)

    await coll.set('username', value)
    assert await coll.get('username') == expected


@pytest.mark.asyncio
async def test_collection_setting_nested_values():
    """Test setting record values."""
    from anansi import Model, Field, Collection

    class User(Model):
        username = Field()
        manager = Field()

    u = User(values={'username': 'bill'})
    coll = Collection(records=[
        User(values={'username': 'bob', 'manager': u}),
        User(values={'username': 'john', 'manager': u})
    ])

    assert await coll.get('manager.username') == ['bill', 'bill']
    await coll.set('manager.username', 'tom')
    assert await coll.get('manager.username') == ['tom', 'tom']


@pytest.mark.asyncio
@pytest.mark.parametrize('key', (
    'count',
    'first',
    'last',
))
async def test_collection_setting_reserved_words_fail(key):
    """Test attempting to set reserved words raises a ReadOnly error."""
    from anansi import Collection
    from anansi.exceptions import ReadOnly

    c = Collection()
    with pytest.raises(ReadOnly):
        await c.set(key, 1)


@pytest.mark.asyncio
async def test_collection_delete():
    """Test deleting record from store."""
    from anansi import Collection, Store

    class Storage:
        async def delete_collection(self, collection, context):
            return await collection.get_count()

    store = Store(storage=Storage())
    coll = Collection(records=[1, 2, 3], store=store)

    assert await coll.delete() == 3


@pytest.mark.asyncio
async def test_collection_save():
    """Test saving record from a store."""
    from anansi import Collection, Store

    class Storage:
        async def save_collection(self, collection, context):
            return []

    store = Store(storage=Storage())
    coll = Collection(records=[1, 2, 3], store=store)

    assert await coll.save() == []


def test_collection_refining():
    """Test refining a collection down by merging contexts."""
    from anansi import Collection, make_context, Query as Q

    q = Q('active') == True  # noqa: E712
    coll = Collection(context=make_context(where=q))
    assert coll.context.where.left == 'active'
    assert coll.context.where.right is True

    q2 = Q('username') == 'bob'
    coll2 = coll.refine(where=q2)
    assert coll.context.where.left == 'active'
    assert coll2.context.where.queries[0].left == 'username'
    assert coll2.context.where.queries[0].right == 'bob'
    assert coll2.context.where.queries[1] is coll.context.where


@pytest.mark.asyncio
async def test_collection_at():
    """Test getting an item from a collection."""
    from anansi import Collection

    coll = Collection()
    with pytest.raises(IndexError):
        await coll.at(0)

    coll = Collection(records=[1])
    assert await coll.at(0) == 1


@pytest.mark.asyncio
async def test_collection_at_from_store(mocker):
    """Test getting a record from the store."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        id = Field()

    async def get_records(model, context):
        return [{'id': 1}]

    store = Store()
    mocker.patch.object(store, 'get_records', side_effect=get_records)

    collection = Collection(model=User, store=store)
    user = await collection.at(0)
    assert await user.get('id') == 1


@pytest.mark.asyncio
async def test_collection_fetch_empty_record(mocker):
    """Test fetching an empty record doesn't raise an error."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        id = Field()
        username = Field()

    async def get_records(model, context):
        return []

    store = Store()
    mocker.patch.object(store, 'get_records', side_effect=get_records)
    collection = Collection(model=User, store=store)
    record = await collection.get_first()
    assert record is None


@pytest.mark.asyncio
async def test_collection_get_first_from_store(mocker):
    """Test fetching an empty record doesn't raise an error."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        id = Field()
        username = Field()

    async def get_records(model, context):
        return [{'id': 1}]

    store = Store()
    mocker.patch.object(store, 'get_records', side_effect=get_records)
    collection = Collection(model=User, store=store)
    record = await collection.get_first()
    assert record is not None


@pytest.mark.asyncio
async def test_collection_get_last_from_store(mocker):
    """Test fetching an empty record doesn't raise an error."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        id = Field()
        username = Field()

    async def get_records(model, context):
        return [{'id': 1}]

    store = Store()
    mocker.patch.object(store, 'get_records', side_effect=get_records)
    collection = Collection(model=User, store=store)
    record = await collection.get_last()
    assert record is not None


@pytest.mark.asyncio
@pytest.mark.parametrize('include,expected,returning', (
    ('count', {'count': 2}, None),
    ('first', {'first': {'id': 1, 'username': 'john.doe'}}, None),
    ('last', {'last': {'id': 2, 'username': 'jane.doe'}}, None),
    (None, {'count': 2}, 'count'),
    (None, [
        {'id': 1, 'username': 'john.doe'},
        {'id': 2, 'username': 'jane.doe'},
    ], None),
    ('records', [
        {'id': 1, 'username': 'john.doe'},
        {'id': 2, 'username': 'jane.doe'},
    ], None),
    ('count,records', {
        'count': 2,
        'records': [
            {'id': 1, 'username': 'john.doe'},
            {'id': 2, 'username': 'jane.doe'},
        ],
    }, None),
    ('count,first,last', {
        'count': 2,
        'first': {'id': 1, 'username': 'john.doe'},
        'last': {'id': 2, 'username': 'jane.doe'},
    }, None),
))
async def test_collection_get_state(include, expected, returning):
    """Test converting a collection to a dictionary state."""
    from anansi import Collection, Field, Model

    class User(Model):
        id = Field()
        username = Field()

    records = [
        User({'id': 1, 'username': 'john.doe'}),
        User({'id': 2, 'username': 'jane.doe'}),
    ]
    collection = Collection(
        records=records,
        include=include,
        returning=returning,
    )
    assert await collection.get_state() == expected


async def test_collection_get_state_from_store(mocker):
    """Test getting a state from a backend store."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        id = Field()
        username = Field()

    async def get_records(model, context):
        return [
            {'id': 1, 'username': 'john.doe'},
            {'id': 2, 'username': 'jane.doe'},
        ]

    store = Store()
    mocker.patch.object(store, 'get_records', side_effect=get_records)
    collection = Collection(
        model=User,
        store=store,
    )
    assert await collection.get_state() == [
        {'id': 1, 'username': 'john.doe'},
        {'id': 2, 'username': 'jane.doe'},
    ]


@pytest.mark.asyncio
async def test_distinct_on_null():
    """Test assertion from distinct call on null collection."""
    from anansi import Collection
    from anansi.exceptions import CollectionIsNull

    with pytest.raises(CollectionIsNull):
        await Collection().distinct('test')


@pytest.mark.asyncio
@pytest.mark.parametrize('keys,value', (
    (
        ('last_name',),
        {'Doe', 'Smith'}
    ),
    (
        ('last_name', 'is_active'),
        {
            ('Doe', True),
            ('Smith', True),
        }
    ),
    (
        ('first_name', 'last_name'),
        {
            ('John', 'Doe'),
            ('Jane', 'Doe'),
            ('John', 'Smith'),
        },
    )
))
async def test_distinct_from_records(keys, value):
    """Test gathering distinct values from a collection."""
    from anansi import Model, Field
    from anansi import Collection

    class User(Model):
        first_name = Field()
        last_name = Field()
        is_active = Field()

    john = User(values={
        'first_name': 'John',
        'last_name': 'Doe',
        'is_active': True,
    })
    jane = User(values={
        'first_name': 'Jane',
        'last_name': 'Doe',
        'is_active': True,
    })
    smith = User(values={
        'first_name': 'John',
        'last_name': 'Smith',
        'is_active': True,
    })

    coll = Collection(records=[john, jane, smith])
    assert await coll.distinct(*keys) == value


@pytest.mark.asyncio
@pytest.mark.parametrize('keys,value,records', (
    (
        ('last_name',),
        set(),
        [],
    ),
    (
        ('last_name',),
        {'Doe', 'Smith'},
        [
            {'last_name': 'Doe'},
            {'last_name': 'Smith'},
        ]
    ),
    (
        ('last_name', 'is_active'),
        {
            ('Doe', True),
            ('Smith', True),
        },
        [
            {'last_name': 'Doe', 'is_active': True},
            {'last_name': 'Smith', 'is_active': True},
        ]
    ),
    (
        ('first_name', 'last_name'),
        {
            ('John', 'Doe'),
            ('Jane', 'Doe'),
            ('John', 'Smith'),
        },
        [
            {'first_name': 'John', 'last_name': 'Doe'},
            {'first_name': 'Jane', 'last_name': 'Doe'},
            {'first_name': 'John', 'last_name': 'Smith'},
        ]
    )
))
async def test_distinct_from_store(keys, value, records, mocker):
    """Test fetching distinct values from the backend store."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        first_name = Field()
        last_name = Field()
        is_active = Field()

    async def get_records(model, context):
        assert context.fields == keys
        return records

    store = Store()
    mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records,
    )

    coll = Collection(model=User, store=store)
    assert await coll.distinct(*keys) == value


@pytest.mark.asyncio
@pytest.mark.parametrize('keys,value', (
    (
        ('last_name',),
        ['Doe', 'Doe', 'Smith'],
    ),
    (
        ('last_name', 'is_active'),
        [
            ('Doe', True),
            ('Doe', True),
            ('Smith', True),
        ],
    ),
    (
        ('first_name', 'last_name'),
        [
            ('John', 'Doe'),
            ('Jane', 'Doe'),
            ('John', 'Smith'),
        ],
    )
))
async def test_gather_from_records(keys, value):
    """Test gathering distinct values from a collection."""
    from anansi import Model, Field
    from anansi import Collection

    class User(Model):
        first_name = Field()
        last_name = Field()
        is_active = Field()

    john = User(values={
        'first_name': 'John',
        'last_name': 'Doe',
        'is_active': True,
    })
    jane = User(values={
        'first_name': 'Jane',
        'last_name': 'Doe',
        'is_active': True,
    })
    smith = User(values={
        'first_name': 'John',
        'last_name': 'Smith',
        'is_active': True,
    })

    coll = Collection(records=[john, jane, smith])
    assert await coll.gather(*keys) == value


@pytest.mark.asyncio
@pytest.mark.parametrize('keys,value,records', (
    (
        ('last_name',),
        [],
        [],
    ),
    (
        ('last_name',),
        ['Doe', 'Doe', 'Smith'],
        [
            {'last_name': 'Doe'},
            {'last_name': 'Doe'},
            {'last_name': 'Smith'},
        ]
    ),
    (
        ('last_name', 'is_active'),
        [
            ('Doe', True),
            ('Doe', True),
            ('Smith', True),
        ],
        [
            {'last_name': 'Doe', 'is_active': True},
            {'last_name': 'Doe', 'is_active': True},
            {'last_name': 'Smith', 'is_active': True},
        ]
    ),
    (
        ('first_name', 'last_name'),
        [
            ('John', 'Doe'),
            ('Jane', 'Doe'),
            ('John', 'Smith'),
        ],
        [
            {'first_name': 'John', 'last_name': 'Doe'},
            {'first_name': 'Jane', 'last_name': 'Doe'},
            {'first_name': 'John', 'last_name': 'Smith'},
        ]
    )
))
async def test_gather_from_store(keys, value, records, mocker):
    """Test fetching distinct values from the backend store."""
    from anansi import Collection, Field, Model, Store

    class User(Model):
        first_name = Field()
        last_name = Field()
        is_active = Field()

    async def get_records(model, context):
        assert context.fields == keys
        return records

    store = Store()
    mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records,
    )

    coll = Collection(model=User, store=store)
    assert await coll.gather(*keys) == value


async def test_collection_update(mocker):
    """Test updating a collection."""
    from anansi import Collection, Field, Model

    class User(Model):
        id = Field()
        username = Field()
        is_active = Field()

    async def save():
        pass

    a = User({'id': 1, 'username': 'john.doe', 'is_active': True})
    b = User({'id': 2, 'username': 'john.doe', 'is_active': False})

    mock_a = mocker.patch.object(a, 'save', side_effect=save)
    mock_b = mocker.patch.object(b, 'save', side_effect=save)

    coll = Collection(records=[a, b])
    await coll.update({'is_active': False})
    mock_a.assert_called_once()
    mock_b.assert_called_once()
    assert await a.get('is_active') is False
    assert await b.get('is_active') is False


@pytest.mark.xfail(reason='TODO(issue-#11)')
@pytest.mark.asyncio
async def test_collection_update_from_store():
    """Test updating a collection directly in the store."""
    from anansi import Collection, Field, Model

    class User(Model):
        id = Field()
        username = Field()
        is_active = Field()

    collection = Collection(model=User)
    await collection.update({'is_active': False})


@pytest.mark.asyncio
async def test_making_records():
    """Test make_records method."""
    from anansi import Field, Model, make_context
    from anansi.core.collection import make_records

    class User(Model):
        id = Field()
        username = Field()

    context = make_context()
    store_records = [{
        'id': 1,
        'username': 'john.doe',
    }, {
        'id': 2,
        'username': 'jane.doe',
    }]
    records = list(make_records(User, store_records, context))
    assert type(records[0]) is User
    assert await records[0].get('id') == 1
    assert await records[1].get('id') == 2


@pytest.mark.asyncio
async def test_making_records_as_data():
    """Test make_records method."""
    from anansi import Field, Model, make_context
    from anansi.core.collection import make_records

    class User(Model):
        id = Field()
        username = Field()

    context = make_context(returning='data')
    store_records = [{
        'id': 1,
        'username': 'john.doe',
    }, {
        'id': 2,
        'username': 'jane.doe',
    }]
    records = list(make_records(User, store_records, context))
    assert type(records[0]) is dict
    assert records[0].get('id') == 1
    assert records[1].get('id') == 2
