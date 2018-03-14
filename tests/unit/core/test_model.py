"""Model class tests."""
import pytest


def test_model_definition():
    """Test the User model has a schema object."""
    from anansi import Model, Field

    class User(Model):
        id = Field()

    assert User.__schema__ is not None


def test_model_definition_with_mixins():
    """Test defining a model that uses a mixin."""
    from anansi import Model, Field, Collector, Index, Reference

    class CreationMixin:
        created_by = Field()
        created_at = Field()

        created_by_ref = Reference()

        creations = Collector()
        by_created_by = Index()

        def get_value(self):
            return 1

        def get_value_sum(self):
            return super().get_value_sum() + 1

    class UpdateMixin:
        updated_by = Field()
        updated_at = Field()

        def get_value(self):
            return 2

        def get_value_sum(self):
            return 1

    class Page(CreationMixin, UpdateMixin, Model):
        text = Field()

    class Comment(CreationMixin, UpdateMixin, Model):
        text = Field()

        def get_value(self):
            return super().get_value() + 5

        def get_value_sum(self):
            return 1

    p_schema = Page.__schema__
    c_schema = Comment.__schema__

    assert len(p_schema.local_collectors) == 1
    assert len(p_schema.local_indexes) == 1
    assert len(p_schema.local_references) == 1
    assert len(p_schema.local_fields) == 5
    assert len(c_schema.local_fields) == 5
    assert len(c_schema.local_references) == 1

    assert p_schema.fields['created_by'] is c_schema.fields['created_by']
    assert p_schema.fields['updated_by'] is c_schema.fields['updated_by']
    assert p_schema.fields['text'] is not c_schema.fields['created_by']

    page = Page()
    comment = Comment()

    assert page.get_value() == 1
    assert page.get_value_sum() == 2

    assert comment.get_value() == 6
    assert comment.get_value_sum() == 1


def test_model_definition_with_inheritance():
    """Test defining a model that uses inheritance."""
    from anansi import Model, Field, Collector, Index

    class User(Model):
        id = Field()
        username = Field()
        password = Field()

        login_attempts = Collector()

        by_username = Index()

    class Employee(User):
        badge = Field()
        manager = Field()

    u_schema = User.__schema__
    e_schema = Employee.__schema__

    assert len(u_schema.local_fields) == 3
    assert len(u_schema.fields) == 3
    assert len(u_schema.local_collectors) == 1
    assert len(u_schema.collectors) == 1
    assert len(u_schema.local_indexes) == 1
    assert len(u_schema.indexes) == 1
    assert len(e_schema.local_fields) == 2
    assert len(e_schema.fields) == 5
    assert len(e_schema.local_collectors) == 0
    assert len(e_schema.collectors) == 1
    assert len(e_schema.local_indexes) == 0
    assert len(e_schema.indexes) == 1

    assert e_schema.fields['id'] is u_schema.fields['id']


def test_model_definition_with_abstraction():
    """Test defining a model with an abstract base class."""
    from anansi import Model, Field

    class AbstractUser(Model):
        __abstract__ = True

        id = Field()
        username = Field()
        password = Field()

    class Account(AbstractUser):
        badge = Field()

    class Employee(AbstractUser):
        badge = Field()
        manager = Field()

    u_schema = AbstractUser.__schema__
    a_schema = Account.__schema__
    e_schema = Employee.__schema__

    assert u_schema is None
    assert a_schema is not None
    assert e_schema is not None

    assert len(e_schema.local_fields) == 5
    assert len(e_schema.fields) == 5
    assert len(a_schema.local_fields) == 4
    assert len(a_schema.local_fields) == 4

    assert e_schema.fields['id'] is a_schema.fields['id']
    assert e_schema.fields['badge'] is not a_schema.fields['badge']


def test_model_definition_with_key():
    """Test defining a model with a single key."""
    from anansi import Model, Field

    class User(Model):
        id = Field(flags={'Key'})

    assert User.__schema__.key_fields == [User.__schema__.fields['id']]


def test_model_definition_with_multiple_keys():
    """Test defining a model with multiple keys."""
    from anansi import Model, Field, Index

    class User(Model):
        first_name = Field()
        last_name = Field()

        by_first_and_last_name = Index(
            ('first_name', 'last_name'),
            flags={'Key'}
        )

    assert User.__schema__.key_fields == [
        User.__schema__.fields['first_name'],
        User.__schema__.fields['last_name']
    ]


@pytest.mark.asyncio
async def test_model_definition_with_getters():
    """Test a model with custom field getters."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        first_name = Field()
        last_name = Field()
        display_name = Field(flags=Field.Flags.Virtual)

        @display_name.getter
        async def get_display_name(self):
            values = await self.gather('first_name', 'last_name')
            return '{} {}'.format(*values)

    u = User(values={'first_name': 'John', 'last_name': 'Doe'})
    assert await u.get('display_name') == 'John Doe'


@pytest.mark.asyncio
async def test_model_definition_with_virtual_decorator():
    """Test a model with custom field getters."""
    from anansi import Collector, Collection, Model, Field, virtual

    class User(Model):
        id = Field()
        first_name = Field()
        last_name = Field()

        @virtual(Field)
        async def display_name(self):
            values = await self.gather('first_name', 'last_name')
            return '{} {}'.format(*values)

        @virtual(Collector)
        async def groups(self):
            return Collection(records=[])

    u = User(values={'first_name': 'John', 'last_name': 'Doe'})
    assert await u.get('display_name') == 'John Doe'
    assert await u.get('groups.count') == 0


@pytest.mark.asyncio
async def test_model_initialization_with_values():
    """Test model creation using values."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        username = Field()

    user = User(values={'id': 1, 'username': 'bob'})
    assert await user.gather('id', 'username') == [1, 'bob']
    assert user.local_changes == {
        'id': (None, 1),
        'username': (None, 'bob')
    }
    user.mark_loaded()
    assert await user.gather('id', 'username') == [1, 'bob']
    assert user.local_changes == {}


@pytest.mark.asyncio
async def test_model_initialization_with_state():
    """Test model initialization with state."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        username = Field()

    user = User(state={'id': 1, 'username': 'bob'})
    assert await user.gather('id', 'username') == [1, 'bob']
    assert user.local_changes == {}


@pytest.mark.asyncio
async def test_model_initialization_with_nested_values():
    """Test model initialization with nested values."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        username = Field()
        manager = Field()

    bob = User(values={'username': 'bob'})
    tom = User(values={'username': 'tom', 'manager': bob})

    assert await tom.get('manager.username') == 'bob'


@pytest.mark.asyncio
async def test_model_initialization_with_nested_state():
    """Test model initialization with nested values."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        username = Field()
        manager = Field()

    bob = User(state={'username': 'bob'})
    tom = User(state={'username': 'tom', 'manager': bob})

    assert await tom.get('manager.username') == 'bob'


@pytest.mark.asyncio
async def test_model_initialization_with_nested_collections_by_state():
    """Test model initialization with nested values."""
    from anansi import Model, Field, Collector

    class User(Model):
        id = Field()
        username = Field()
        employees = Collector(model='User')

    user = User(state={
        'id': 1,
        'username': 'bob',
        'employees': [{
            'id': 2,
            'username': 'tom'
        }, {
            'id': 3,
            'username': 'john'
        }]
    })

    assert await user.get('employees.count') == 2
    assert set(await user.get('employees.username')) == {'tom', 'john'}


@pytest.mark.asyncio
async def test_model_initialization_with_nested_collections_by_values():
    """Test model initialization with nested values."""
    from anansi import Model, Field, Collector

    class User(Model):
        id = Field()
        username = Field()
        employees = Collector(model='User')

    user = User(values={
        'id': 1,
        'username': 'bob',
        'employees': [{
            'id': 2,
            'username': 'tom'
        }, {
            'id': 3,
            'username': 'john'
        }]
    })

    assert await user.get('employees.count') == 2
    assert set(await user.get('employees.username')) == {'tom', 'john'}


@pytest.mark.asyncio
async def test_model_initialization_with_reference():
    """Test initializing a model with reference."""
    from anansi import Model, Field, Reference

    class User(Model):
        id = Field()
        username = Field()
        manager_id = Field(refers_to='User.id')
        manager = Reference(model='User', source='manager_id')

    jane = User(values={
        'id': 2,
        'username': 'jane.doe',
        'manager_id': None,
        'manager': None,
    })
    john = User(values={
        'id': 1,
        'username': 'john.doe',
        'manager_id': 2,
        'manager': jane
    })
    assert await john.get('manager') is jane


def test_model_searching():
    """Test searching model for others by name."""
    from anansi import Model

    class A(Model):
        pass

    class B(Model):
        pass

    class C(A):
        pass

    assert Model.find_model('A') is A
    assert Model.find_model('B') is B
    assert Model.find_model('C') is C
    assert A.find_model('B') is None
    assert A.find_model('C') is C


@pytest.mark.asyncio
async def test_model_get_value(make_users):
    """Test getting simple values work."""
    from anansi.exceptions import FieldNotFound

    bob = make_users('bob')

    assert await bob.get('id') == 1
    assert await bob.get_value('id') == 1

    with pytest.raises(FieldNotFound):
        assert await bob.get('id2') is None
    with pytest.raises(FieldNotFound):
        assert await bob.get_value('id2') is None


@pytest.mark.asyncio
async def test_model_gather_values(make_users):
    """Test gathering multiple values at one time."""
    bob = make_users('bob')
    assert await bob.gather('id', 'username') == [1, 'bob']


@pytest.mark.asyncio
async def test_model_get_nested_value(make_users):
    """Test getting nested properties."""
    john, jane = make_users('john', 'jane')
    await john.set('manager', jane)
    assert await john.get('manager.username') == 'jane'


@pytest.mark.asyncio
async def test_model_get_errors(make_users):
    """Test getting failures."""
    from anansi.exceptions import (
        CollectorNotFound,
        ReferenceNotFound,
    )
    john = make_users('john')
    with pytest.raises(CollectorNotFound):
        await john.get_collection('users')
    with pytest.raises(ReferenceNotFound):
        await john.get_reference('parent')


@pytest.mark.asyncio
async def test_model_get_key():
    """Test getting keys."""
    from anansi import Field, Index, Model

    class User(Model):
        id = Field(flags={'Key'})

    class UserGroup(Model):
        group_id = Field()
        user_id = Field()
        by_group_and_user = Index(['group_id', 'user_id'], flags={'Key'})

    u = User({'id': 1})
    ug = UserGroup({'group_id': 1, 'user_id': 2})

    assert await u.get_key() == 1
    assert await ug.get_key() == [1, 2]


@pytest.mark.asyncio
async def test_model_get_key_dict():
    """Test getting a key dictionary."""
    from anansi import Field, Index, Model

    class User(Model):
        id = Field(flags={'Key'})

    class UserGroup(Model):
        group_id = Field()
        user_id = Field()
        by_group_and_user = Index(['group_id', 'user_id'], flags={'Key'})

    u = User({'id': 1})
    ug = UserGroup({'group_id': 1, 'user_id': 2})

    assert await u.get_key_dict() == {'id': 1}
    assert await ug.get_key_dict() == {'group_id': 1, 'user_id': 2}


@pytest.mark.asyncio
async def test_model_gather_nested_values(make_users):
    """Test gathering multiple values which can be nested."""
    john, jane = make_users('john', 'jane')
    await john.set('manager', jane)
    result = await john.gather('username', 'manager.username')
    assert result == ['john', 'jane']


@pytest.mark.asyncio
async def test_model_modification(make_users):
    """Test modifying records."""
    bob = make_users('bob')
    assert await bob.get('username') == 'bob'
    await bob.set('username', 'tom')
    assert await bob.get('username') == 'tom'
    assert bob.local_changes == {'username': ('bob', 'tom')}


@pytest.mark.asyncio
async def test_model_modification_reset(make_users):
    """Test resetting record clears changes."""
    bob = make_users('bob')
    assert await bob.get('username') == 'bob'
    await bob.set('username', 'tom')
    assert await bob.get('username') == 'tom'
    assert bob.local_changes == {'username': ('bob', 'tom')}
    await bob.reset()
    assert bob.local_changes == {}


@pytest.mark.asyncio
async def test_model_modification_reset_by_change(make_users):
    """Test resetting record clears changes."""
    bob = make_users('bob')
    assert await bob.get('username') == 'bob'
    await bob.set('username', 'tom')
    assert await bob.get('username') == 'tom'
    assert bob.local_changes == {'username': ('bob', 'tom')}
    await bob.set('username', 'bob')
    assert bob.local_changes == {}


@pytest.mark.asyncio
async def test_model_modification_by_update(make_users):
    """Test update modifies multiple fields."""
    bob = make_users('bob')
    assert await bob.gather('id', 'username') == [1, 'bob']
    await bob.update({'id': 2, 'username': 'tom'})
    assert await bob.gather('id', 'username') == [2, 'tom']


@pytest.mark.asyncio
async def test_model_set_collection():
    """Test assigning a value to a collection."""
    from anansi import Collector, Collection, Model

    class User(Model):
        employees = Collector(model='User')

    a = User()
    b = User()
    c = Collection(records=[a])
    await b.set('employees', c)
    assert await b.get('employees') is c


@pytest.mark.asyncio
async def test_model_set_reference():
    """Test assigning a value to a collection."""
    from anansi import Field, Model, Reference

    class User(Model):
        id = Field()
        manager_id = Field(refers_to='User.id')
        manager = Reference(model='User', source='manager_id')

    a = User()
    b = User()
    await b.set('manager', a)
    assert await b.get('manager') is a


@pytest.mark.asyncio
async def test_model_modification_with_nesting(make_users):
    """Test update nested properties."""
    bob, sam = make_users('bob', 'sam')
    await bob.set('manager', sam)
    assert await bob.get('manager.username') == 'sam'
    await bob.set('manager.username', 'sammy')
    assert await bob.get('manager.username') == 'sammy'
    assert await sam.get('username') == 'sammy'


@pytest.mark.asyncio
async def test_model_modification_with_custom_setter():
    """Test update with custom setter method."""
    from anansi import Model, Field, virtual

    class User(Model):
        first_name = Field()
        last_name = Field()

        @virtual(Field)
        async def display_name(self):
            first_name, last_name = await self.gather(
                'first_name',
                'last_name'
            )
            return '{} {}'.format(first_name, last_name)

        @display_name.setter
        async def set_display_name(self, name):
            first_name, _, last_name = name.partition(' ')
            await self.set('first_name', first_name)
            await self.set('last_name', last_name)

    u = User(values={'first_name': 'John', 'last_name': 'Smith'})
    assert await u.get('display_name') == 'John Smith'
    await u.set('display_name', 'Jane Doe')
    assert await u.get('display_name') == 'Jane Doe'
    assert set(u.local_changes.keys()) == {'first_name', 'last_name'}


@pytest.mark.asyncio
async def test_model_save():
    """Test saving a model."""
    from anansi import Model, Field, Store

    class Storage:
        async def save_record(self, record, context):
            return {'id': 1}

    store = Store(storage=Storage())

    class User(Model):
        id = Field()
        username = Field()
        password = Field()

    u = User(values={'username': 'bob'}, store=store)
    assert await u.save() is True
    assert await u.gather('id', 'username') == [1, 'bob']


@pytest.mark.asyncio
async def test_model_save_without_modification():
    """Test save without modifications."""
    from anansi import Model, Field, Store

    class Storage:
        async def save_record(self, record, context):
            return {'id': 1}

    store = Store(storage=Storage())

    class User(Model):
        id = Field()
        username = Field()

    u = User(state={'username': 'bob'}, store=store)
    assert await u.save() is False
    await u.set('username', 'tom')
    assert await u.save() is True
    assert await u.gather('id', 'username') == [1, 'tom']


@pytest.mark.asyncio
async def test_model_save_read_only():
    """Test saving read-only models raises an error."""
    from anansi import Model
    from anansi.exceptions import ReadOnly

    class UserView(Model):
        __view__ = True

    u = UserView()
    with pytest.raises(ReadOnly):
        await u.save()


@pytest.mark.asyncio
async def test_model_delete():
    """Test deleting a model."""
    from anansi import Model, Store

    class Storage:
        async def delete_record(self, record, context):
            return 'deleted'

    store = Store(storage=Storage())

    class User(Model):
        pass

    u = User(store=store)
    assert await u.delete() == 'deleted'


@pytest.mark.asyncio
async def test_model_delete_read_only():
    """Test saving read-only models raises an error."""
    from anansi import Model
    from anansi.exceptions import ReadOnly

    class UserView(Model):
        __view__ = True

    u = UserView()
    with pytest.raises(ReadOnly):
        await u.delete()


@pytest.mark.asyncio
async def test_model_create():
    """Test creating a new model."""
    from anansi import Model, Field, Store

    class Storage:
        async def save_record(self, record, context):
            return {'id': 1}

    store = Store(storage=Storage())

    class User(Model):
        id = Field()
        username = Field()
        password = Field()

    user = await User.create({'username': 'jdoe'}, store=store)
    assert await user.gather('id', 'username') == [1, 'jdoe']


@pytest.mark.asyncio
async def test_model_create_view_read_only():
    """Test creating a new model."""
    from anansi import Model
    from anansi.exceptions import ReadOnly

    class UserView(Model):
        __view__ = True

    with pytest.raises(ReadOnly):
        await UserView.create({'username': 'jdoe'})


@pytest.mark.asyncio
async def test_model_select_collection():
    """Test selecting a collection from a model."""
    from anansi import Model, Field, Query as Q

    class User(Model):
        id = Field()

    coll = await User.select(where=Q('id') == 1)
    assert coll.model is User
    assert coll.context.where.left == 'id'
    assert coll.context.where.right == 1


@pytest.mark.asyncio
async def test_model_ensure_exists(mocker):
    """Test ensuring a record exists in the store."""
    from anansi import Model, Field

    class User(Model):
        id = Field()
        username = Field()
        first_name = Field()
        last_name = Field()

    values = {'username': 'john.doe'}
    defaults = {'first_name': 'John', 'last_name': 'Doe'}

    async def save():
        pass

    async def fetch(values, **context):
        return None

    mock_fetch = mocker.patch.object(User, 'fetch', side_effect=fetch)
    mock_save = mocker.patch.object(User, 'save', side_effect=save)

    user = await User.ensure_exists(values, defaults=defaults)

    mock_fetch.assert_called_with(values)
    mock_save.assert_called_once()

    results = await user.gather('username', 'first_name', 'last_name')
    assert results == ['john.doe', 'John', 'Doe']


def test_model_make_key_query_runtime_error():
    """Test making a key query raises index error."""
    from anansi import Model, Field

    class User(Model):
        id = Field(flags={'Key'})

    with pytest.raises(RuntimeError):
        User.make_key_query((1, 2))


@pytest.mark.asyncio
async def test_model_make_key_query_single_key():
    """Test making fetch query with single key."""
    from anansi import Model, Field

    class User(Model):
        id = Field(flags={'Key'})
        username = Field()

    key_fields = User.__schema__.key_fields
    assert key_fields == [User.__schema__['id']]
    query = User.make_key_query((1,))
    assert query.left == 'id'
    assert query.op == query.Op.Is
    assert query.right == 1


def test_model_make_key_query_multiple_keys():
    """Test making fetch query with multiple keys."""
    from anansi import Field, Index, Model

    class UserGroup(Model):
        user_id = Field()
        group_id = Field()
        by_user_and_group = Index(['user_id', 'group_id'], flags={'Key'})

    query = UserGroup.make_fetch_query((1, 2))
    assert query.queries[0].left == 'user_id'
    assert query.queries[0].right == 1
    assert query.queries[1].left == 'group_id'
    assert query.queries[1].right == 2


def test_model_make_keyable_query():
    """Test making a query off keyable fields."""
    from anansi import Model, Field

    class User(Model):
        id = Field(flags={'Key'})
        username = Field(flags={'Keyable'})

    query = User.make_keyable_query('john.doe')
    assert query.queries[0].left == 'id'
    assert query.queries[0].right == 'john.doe'
    assert query.queries[1].left == 'username'
    assert query.queries[1].right == 'john.doe'


@pytest.mark.asyncio
async def test_model_fetch(mocker):
    """Test fetching records."""
    from anansi import Model, Field, Store

    class User(Model):
        id = Field(flags={'Key'})

    async def get_records(model, context):
        return []

    store = Store()
    mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records,
    )
    record = await User.fetch(1, store=store)
    assert record is None
