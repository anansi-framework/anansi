"""Test schema class."""
import pytest


@pytest.mark.parametrize('kwargs,values', (
    ({}, {}),
    (
        {'name': 'UserGroup'},
        {
            'label': 'User Group',
            'resource_name': 'user_groups',
            'i18n_name': 'user_groups_i18n',
        },
    ),
    (
        {
            'name': 'UserGroup',
            'label': 'User group',
            'resource_name': 'usergroups',
            'i18n_name': 'usergroups_i18n',
        },
        {},
    ),
))
def test_schema_initialization(kwargs, values):
    """Test basic schema initialization."""
    from anansi import Schema

    default_props = {
        'collectors': {},
        'fields': {},
        'i18n_name': '',
        'indexes': {},
        'inherits': None,
        'key_fields': [],
        'label': '',
        'local_collectors': {},
        'local_fields': {},
        'local_indexes': {},
        'local_references': {},
        'name': '',
        'namespace': '',
        'references': {},
        'resource_name': '',
    }
    expected = {}
    expected.update(default_props)
    expected.update(kwargs)
    expected.update(values)

    schema = Schema(**kwargs)
    for key in default_props:
        assert getattr(schema, key) == expected[key]


def test_schema_object_definitions():
    """Test defining a schema with objects."""
    from anansi import (
        Collector,
        Field,
        Index,
        Reference,
        Schema,
    )

    by_username = Index(name='by_username')
    groups = Collector(name='groups')
    id_ = Field(name='id')
    role = Reference(name='role')
    username = Field(name='username')

    schema = Schema(
        collectors={'groups': groups},
        fields={'id': id_, 'username': username},
        indexes={'by_username': by_username},
        references={'role': role},
    )

    assert schema['by_username'] is by_username
    assert schema['groups'] is groups
    assert schema['id'] is id_
    assert schema['role'] is role
    with pytest.raises(KeyError):
        assert schema['display_name']

    assert schema.get('by_username') is by_username
    assert schema.get('display_name') is None
    assert schema.get('groups') is groups
    assert schema.get('id') is id_
    assert schema.get('role') is role

    assert schema.local_collectors == {'groups': groups}
    assert schema.local_fields == {'id': id_, 'username': username}
    assert schema.local_indexes == {'by_username': by_username}
    assert schema.local_references == {'role': role}


def test_schema_object_definitions_with_inheritance():
    """Test defining a schema with objects."""
    from anansi import (
        Collector,
        Field,
        Index,
        Reference,
        Schema,
    )

    by_username = Index(name='by_username')
    groups = Collector(name='groups')
    id_ = Field(name='id')
    role = Reference(name='role')
    username = Field(name='username')

    base_schema = Schema(
        collectors={'groups': groups},
        fields={'id': id_, 'username': username},
        indexes={'by_username': by_username},
        references={'role': role},
    )

    schema = Schema(inherits=[base_schema])

    assert schema['by_username'] is by_username
    assert schema['groups'] is groups
    assert schema['id'] is id_
    assert schema['role'] is role
    with pytest.raises(KeyError):
        assert schema['display_name']

    assert schema.get('by_username') is by_username
    assert schema.get('display_name') is None
    assert schema.get('groups') is groups
    assert schema.get('id') is id_
    assert schema.get('role') is role

    assert schema.local_collectors == {}
    assert schema.local_fields == {}
    assert schema.local_indexes == {}
    assert schema.local_references == {}


def test_schema_with_i18n():
    """Test schema definition with translatable fields."""
    from anansi import Field, Schema

    id_ = Field()
    title = Field(flags={'Translatable'})
    schema = Schema(
        fields={'id': id_, 'title': title}
    )

    assert schema.has_translations is True
    assert schema.translatable_fields == [title]
