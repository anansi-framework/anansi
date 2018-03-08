"""Tests for the Reference class type."""
import pytest


def test_reference_definition():
    """Test defining a Reference object on a model."""
    from anansi import Model, Field, Reference

    class Page(Model):
        id = Field(flags={'Key'})
        parent_id = Field(refers_to='Page.id')
        parent = Reference(model='Page', source='parent_id')

    schema = Page.__schema__
    assert schema['parent_id'].refers_to_model is Page
    assert schema['parent_id'].refers_to_field is schema['id']
    assert schema['parent'].model is Page
    assert schema['parent'].source == 'parent_id'


def test_reference_without_source_field():
    """Test loading a Reference object on initialization."""
    from anansi import Model, Field, Reference

    class User(Model):
        id = Field(flags={'Key'})
        username = Field()
        first_name = Field()
        last_name = Field()

    class Comment(Model):
        id = Field(flags={'Key'})
        text = Field()
        user = Reference(model='User')

    schema = Comment.__schema__

    assert schema['user'].model is User
    assert schema['user'].source is None


@pytest.mark.asyncio
async def test_reference_loading():
    """Test instantiating a model with a reference."""
    from anansi import Model, Field, Reference

    class User(Model):
        id = Field()
        username = Field()
        first_name = Field()
        last_name = Field()

    class Comment(Model):
        id = Field()
        text = Field()
        user_id = Field(refers_to='User.id')
        user = Reference(model='User', source='user_id')

    comment = Comment(values={
        'id': 1,
        'text': 'Hello, World',
        'user_id': 1,
        'user': {
            'id': 1,
            'username': 'jdoe',
            'first_name': 'John',
            'last_name': 'Doe'
        }
    })

    assert await comment.get('id') == 1
    assert await comment.get('text') == 'Hello, World'
    assert type(await comment.get('user')) is User
    assert await comment.get('user_id') == 1
    assert await comment.get('user.id') == 1
    assert await comment.get('user.username') == 'jdoe'


@pytest.mark.asyncio
async def test_reference_nested_loading():
    """Test loading nested references."""
    from anansi import Model, Field, Reference

    class Role(Model):
        id = Field()
        name = Field()

    class User(Model):
        id = Field()
        username = Field()
        role_id = Field(refers_to='User.id')
        role = Reference(model='Role', source='role_id')

    class Comment(Model):
        id = Field()
        text = Field()
        user_id = Field(refers_to='User.id')
        user = Reference(model='User', source='user_id')

    comment = Comment(state={
        'id': 1,
        'text': 'Hello, World',
        'user': {
            'id': 1,
            'username': 'jdoe',
            'role': {
                'id': 1,
                'name': 'admin'
            }
        }
    })

    values = await comment.gather(
        'text',
        'user.username',
        'user.role.name'
    )

    assert ['Hello, World', 'jdoe', 'admin'] == values


@pytest.mark.asyncio
async def test_reference_loading_from_store(mocker):
    """Test loading reference from store."""
    from anansi import Store, Model, Field, Reference

    class Role(Model):
        id = Field()
        name = Field()

    class User(Model):
        id = Field()
        username = Field()
        role_id = Field(refers_to='Role.id')
        role = Reference(model='Role', source='role_id')

    class Comment(Model):
        id = Field()
        text = Field()
        user_id = Field(refers_to='User.id')
        user = Reference(model='User', source='user_id')

    comment = Comment(state={
        'id': 1,
        'text': 'Hello, world',
        'user_id': 1
    })

    async def get_records(model, context):
        if model is User:
            return [{
                'id': 1,
                'username': 'jdoe',
                'role_id': 1
            }]
        elif model is Role:
            return [{
                'id': 1,
                'name': 'admin'
            }]
        return []

    store = Store()
    mock_getter = mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records
    )

    with store:
        assert await comment.get('user_id') == 1
        assert mock_getter.call_count == 0
        assert await comment.get('user.id') == 1
        assert mock_getter.call_count == 1
        assert await comment.get('user.username') == 'jdoe'
        assert mock_getter.call_count == 1
        values = await comment.gather('user.role.id', 'user.role.name')
        assert values == [1, 'admin']
        assert mock_getter.call_count == 2


@pytest.mark.asyncio
async def test_reference_loading_from_store_without_source_value(mocker):
    """Test loading reference from store."""
    from anansi import Store, Model, Field, Reference

    class Role(Model):
        id = Field()
        name = Field()

    class User(Model):
        id = Field()
        username = Field()
        role_id = Field(refers_to='Role.id')
        role = Reference(model='Role', source='role_id')

    class Comment(Model):
        id = Field()
        text = Field()
        user_id = Field(refers_to='User.id')
        user = Reference(model='User', source='user_id')

    comment = Comment(state={
        'id': 1,
        'text': 'Hello, world',
        'user_id': 1
    })

    async def get_records(model, context):
        if model is User:
            return [{
                'id': 1,
                'username': 'jdoe'
            }]
        elif model is Role:
            return [{
                'id': 1,
                'name': 'admin'
            }]
        return []

    store = Store()
    mock_getter = mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records
    )

    with store:
        assert await comment.get('user_id') == 1
        assert mock_getter.call_count == 0
        assert await comment.get('user.id') == 1
        assert mock_getter.call_count == 1
        assert await comment.get('user.username') == 'jdoe'
        assert mock_getter.call_count == 1
        values = await comment.gather('user.role.id', 'user.role.name')
        assert values == [None, None]
        assert mock_getter.call_count == 1


@pytest.mark.asyncio
async def test_reference_nested_loading_from_store(mocker):
    """Test loading reference from store."""
    from anansi import Store, Model, Field, Reference

    class Role(Model):
        id = Field()
        name = Field()

    class User(Model):
        id = Field()
        username = Field()
        role_id = Field(refers_to='Role.id')
        role = Reference(model='Role', source='role_id')

    class Comment(Model):
        id = Field()
        text = Field()
        user_id = Field(refers_to='User.id')
        user = Reference(model='User', source='user_id')

    comment = Comment(state={
        'id': 1,
        'text': 'Hello, world',
        'user_id': 1
    })

    async def get_records(model, context):
        if model is User:
            return [{
                'id': 1,
                'username': 'jdoe',
                'role_id': 1,
                'role': {
                    'id': 1,
                    'name': 'admin'
                }
            }]
        elif model is Role:
            return [{
                'id': 1,
                'name': 'admin'
            }]
        return []

    store = Store()
    mock_getter = mocker.patch.object(
        store,
        'get_records',
        side_effect=get_records
    )

    with store:
        assert await comment.get('user_id') == 1
        assert mock_getter.call_count == 0
        assert await comment.get('user.id') == 1
        assert mock_getter.call_count == 1
        assert await comment.get('user.username') == 'jdoe'
        assert mock_getter.call_count == 1
        values = await comment.gather('user.role.id', 'user.role.name')
        assert values == [1, 'admin']
        assert mock_getter.call_count == 1


def test_reference_virtual_overrides():
    """Test reference overridding."""
    from anansi import Reference

    ref = Reference()

    @ref.getter
    async def get_value(**context):
        pass

    @ref.setter
    async def set_value(**context):
        pass

    assert ref.gettermethod is get_value
    assert ref.settermethod is set_value


def test_reference_setting_model():
    """Test reference model setting."""
    from anansi import Model, Reference

    class User(Model):
        pass

    ref = Reference()
    assert ref._model is None
    assert ref.model is None

    ref = Reference(model='User')
    assert ref._model == 'User'
    assert ref.model is User

    ref = Reference(model=User)
    assert ref._model is User
    assert ref.model is User

    ref = Reference()
    ref.model = 'User'
    assert ref._model == 'User'
    assert ref.model is User
