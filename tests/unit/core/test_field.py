"""Tests for the Field class."""
import pytest


def test_field_definition():
    """Test defining a field."""
    from anansi import Field

    f = Field(name='name')
    assert f.name == 'name'
    assert f.code == 'name'
    assert f.label == 'Name'
    assert f.flags == f.Flags(0)
    assert f.default is None


def test_field_ordering():
    """Test ordering of a field by name."""
    from anansi import Field

    a = Field(name='a')
    b = Field(name='b')

    assert a < b < 'c'


@pytest.mark.asyncio
async def test_field_assertions():
    """Test basic field assertions."""
    from anansi import Field

    a = Field()
    await a.assert_valid(None)

    b = Field(flags={'Required'})
    await b.assert_valid(False)
    await b.assert_valid(0)
    with pytest.raises(AssertionError):
        await b.assert_valid(None)

    c = Field(data_type=str)
    await c.assert_valid('test')
    with pytest.raises(AssertionError):
        await c.assert_valid(b'test')

    def sync_validator(field, value):
        assert bool(value)

    async def async_validator(field, value):
        assert bool(value)

    d = Field(validator=sync_validator)
    await d.assert_valid(True)
    with pytest.raises(AssertionError):
        await d.assert_valid(False)

    e = Field(validator=async_validator)
    await e.assert_valid(True)
    with pytest.raises(AssertionError):
        await e.assert_valid(False)


def test_field_label_generation():
    """Test default label options."""
    from anansi import Field

    f = Field(name='first_name')
    assert f.name == 'first_name'
    assert f.label == 'First Name'


def test_field_label_override():
    """Test setting label values."""
    from anansi import Field

    f = Field(name='first_name', label='First')
    assert f.name == 'first_name'
    assert f.label == 'First'
    f.label = 'First name'
    assert f.label == 'First name'


def test_field_flags():
    """Test setting field flags on initialization."""
    from anansi import Field

    f = Field(flags=Field.Flags.Unique | Field.Flags.Required)
    assert f.test_flag(Field.Flags.Unique)
    assert f.test_flag(Field.Flags.Unique | Field.Flags.Required)


def test_field_flags_from_set():
    """Test setting field flags on initialization."""
    from anansi import Field

    f = Field(flags={'Unique', 'Required'})
    assert f.test_flag(Field.Flags.Unique)
    assert f.test_flag(Field.Flags.Unique | Field.Flags.Required)


def test_field_code_overrides():
    """Test defining a field with overrides."""
    from anansi import Field

    f = Field(name='created_by', code='created_by_id')
    assert f.name == 'created_by'
    assert f.code == 'created_by_id'
    assert f.i18n_code == 'created_by_id'

    f = Field(
        name='created_by',
        code=lambda x: '{}_id'.format(x.name),
        i18n_code='id',
    )
    assert f.name == 'created_by'
    assert f.code == 'created_by_id'
    assert f.i18n_code == 'id'

    f.code = 'created'
    f.i18n_code = 'created'
    assert f.code == 'created'
    assert f.i18n_code == 'created'


def test_field_default_overrides():
    """Test getting field default override values."""
    from anansi import Field

    f = Field(default=1)
    assert f.default == 1

    f = Field(name='created', default=lambda x: x.name)
    assert f.default == 'created'

    f.default = 10
    assert f.default == 10


def test_field_getter_method():
    """Test field getter methods."""
    from anansi import Field

    f = Field(name='testing', gettermethod=lambda x: x)
    assert f.gettermethod(f) is f

    @f.getter
    def get_value(field):
        return field.name

    assert f.gettermethod(f) == f.name


def test_field_query_method():
    """Test field query methods."""
    from anansi import Field

    f = Field(name='testing', querymethod=lambda x: x)
    assert f.querymethod(f) is f

    @f.query
    def get_value(field):
        return field.name

    assert f.querymethod(f) == f.name


def test_field_setter_method():
    """Test field setter methods."""
    from anansi import Field

    f = Field(name='testing', settermethod=lambda x: x)
    assert f.settermethod(f) is f

    @f.setter
    def get_value(field):
        return field.name

    assert f.settermethod(f) == f.name


def test_field_refers_to():
    """Test field referencing."""
    from anansi import Field, Model
    from anansi.exceptions import ModelNotFound

    class Role(Model):
        id = Field()

    class User(Model):
        id = Field()
        role_id = Field(refers_to='Role.id')
        group_id = Field(refers_to='Group.id')

    u_id = User.__schema__['id']
    u_role_id = User.__schema__['role_id']
    u_group_id = User.__schema__['group_id']
    r_id = Role.__schema__['id']

    assert u_id.refers_to_model is None
    assert u_id.refers_to_field is None

    assert u_role_id.refers_to_model is Role
    assert u_role_id.refers_to_field is r_id

    with pytest.raises(ModelNotFound):
        assert u_group_id.refers_to_model is None

    with pytest.raises(ModelNotFound):
        assert u_group_id.refers_to_field is None
