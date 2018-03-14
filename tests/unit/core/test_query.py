"""Tests for the Query class."""
import pytest


def test_query_initialization():
    """Test basic query initialization."""
    from anansi import Query as Q

    q = Q('username')
    assert q.left == 'username'
    assert q.op is Q.Op.Is
    assert q.right is None


def test_query_initialization_with_keywords():
    """Test query initialization with keywords."""
    from anansi import Query as Q

    q = Q('id', model='User', op=Q.Op.IsNot, right=1)
    assert q._model == 'User'
    assert q.left == 'id'
    assert q.op is Q.Op.IsNot
    assert q.right == 1


def test_query_setting_model():
    """Test assigning model to query."""
    from anansi import Model, Query as Q

    class User(Model):
        pass

    q = Q()
    assert q.model is None

    q.model = 'User'
    assert q._model == 'User'
    assert q.model is User

    q.model = User
    assert q._model is User
    assert q.model is User

    q.model = 'Group'
    assert q._model == 'Group'
    assert q.model is None


def test_query_and_joining_two_query_objects():
    """Test AND joining two query objects."""
    from anansi import Query as Q, QueryGroup

    a = Q('username') != 'bob'
    b = Q('username') != 'tom'
    c = a & b

    assert type(c) is QueryGroup
    assert c.op is QueryGroup.Op.And
    assert c.queries[0] is a
    assert c.queries[1] is b


def test_query_or_joining_two_query_objects():
    """Test OR joining two query objects."""
    from anansi import Query as Q, QueryGroup

    a = Q('username') != 'bob'
    b = Q('username') != 'tom'
    c = a | b

    assert type(c) is QueryGroup
    assert c.op is QueryGroup.Op.Or
    assert c.queries[0] is a
    assert c.queries[1] is b


def test_query_joining_an_empty_query_object():
    """Test AND / OR joining an empty query object."""
    from anansi import Query as Q

    a = Q('username') != 'bob'
    b = Q()
    c = a & b
    d = a | b

    assert c is a
    assert d is a


def test_query_and_joining_query_object_into_group():
    """Test AND joining a query object into a group."""
    from anansi import Query as Q, QueryGroup

    a = Q('username') != 'bob'
    b = Q('username') != 'tom'
    c = Q('username') != 'sam'
    d = a & b & c
    e = (a & b) & c
    f = a & (b & c)
    g = (a & b) & (b & c)

    for x in (d, e, f):
        assert type(x) is QueryGroup
        assert x.op is QueryGroup.Op.And
        assert x.queries[0] is a
        assert x.queries[1] is b
        assert x.queries[2] is c

    assert g.op is QueryGroup.Op.And
    assert g.queries[0] is a
    assert g.queries[1] is b
    assert g.queries[2] is b
    assert g.queries[3] is c


def test_query_or_joining_query_object_into_group():
    """Test AND joining a query object into a group."""
    from anansi import Query as Q, QueryGroup

    a = Q('username') != 'bob'
    b = Q('username') != 'tom'
    c = Q('username') != 'sam'
    d = a | b | c
    e = (a | b) | c
    f = a | (b | c)
    g = (a | b) | (b | c)

    for x in (d, e, f):
        assert type(x) is QueryGroup
        assert x.op is QueryGroup.Op.Or
        assert x.queries[0] is a
        assert x.queries[1] is b
        assert x.queries[2] is c

    assert g.op is QueryGroup.Op.Or
    assert g.queries[0] is a
    assert g.queries[1] is b
    assert g.queries[2] is b
    assert g.queries[3] is c


def test_query_nesting():
    """Test AND joining a query object into a group."""
    from anansi import Query as Q, QueryGroup

    a = Q('username') != 'bob'
    b = Q('username') != 'tom'
    c = Q('username') != 'sam'
    d = (a | b) & c
    e = a | (b & c)
    f = (a | b) & (a | c)
    g = (a & b) | (a & c)

    assert d.op is QueryGroup.Op.And
    assert type(d.queries[0]) is QueryGroup
    assert d.queries[0].op is QueryGroup.Op.Or
    assert d.queries[0].queries[0] is a
    assert d.queries[0].queries[1] is b
    assert d.queries[1] is c

    assert e.op is QueryGroup.Op.Or
    assert e.queries[0] is a
    assert type(e.queries[1]) is QueryGroup
    assert e.queries[1].queries[0] is b
    assert e.queries[1].queries[1] is c

    assert f.op is QueryGroup.Op.And
    assert f.queries[0].op is QueryGroup.Op.Or
    assert f.queries[1].op is QueryGroup.Op.Or
    assert f.queries[0].queries[0] is a
    assert f.queries[0].queries[1] is b
    assert f.queries[1].queries[0] is a
    assert f.queries[1].queries[1] is c

    assert g.op is QueryGroup.Op.Or
    assert g.queries[0].op is QueryGroup.Op.And
    assert g.queries[1].op is QueryGroup.Op.And
    assert g.queries[0].queries[0] is a
    assert g.queries[0].queries[1] is b
    assert g.queries[1].queries[0] is a
    assert g.queries[1].queries[1] is c


def test_query_joining_with_blanks():
    """Test joining queries together with blank entries."""
    from anansi import Query as Q

    a = Q() & (Q('username') == 'bob')
    b = (Q('username') == 'bob') & Q()

    assert type(a) is Q
    assert a.left == 'username'
    assert a.right == 'bob'
    assert type(b) is Q
    assert b.left == 'username'
    assert b.right == 'bob'


def test_query_joining_with_none():
    """Test joining queries with None."""
    from anansi import Query as Q

    a = Q('username') == 'bob'
    b = a & None

    assert b is a


def test_query_with_model():
    """Test associating a query with a model."""
    from anansi import Model, Query as Q

    class User(Model):
        pass

    q = Q('id', model=User)
    assert q._model is User
    assert q.model is User

    q = Q('id', model='User')
    assert q._model == 'User'
    assert q.model is User

    q = Q('id')
    assert q.model is None


def test_query_to_dict():
    """Test converting query to dictionary."""
    from anansi import Model, Query as Q

    class User(Model):
        pass

    a = Q('username') == 'john.doe'
    b = Q('username') == Q('display_name')
    c = Q(Q('username', model='User')) == Q('display_name', model=User)

    assert a.to_dict() == {
        'type': 'query',
        'model': None,
        'op': 'is',
        'left': 'username',
        'right': 'john.doe',
    }
    assert b.to_dict() == {
        'type': 'query',
        'model': None,
        'op': 'is',
        'left': 'username',
        'right': {
            'type': 'query',
            'model': None,
            'op': 'is',
            'left': 'display_name',
            'right': None,
        }
    }
    assert c.to_dict() == {
        'type': 'query',
        'model': None,
        'op': 'is',
        'left': {
            'type': 'query',
            'model': 'User',
            'op': 'is',
            'left': 'username',
            'right': None,
        },
        'right': {
            'type': 'query',
            'model': 'User',
            'op': 'is',
            'left': 'display_name',
            'right': None,
        }
    }


@pytest.mark.parametrize('func,op', (
    ('__eq__', 'Is'),
    ('__ne__', 'IsNot'),
    ('is_in', 'IsIn'),
    ('is_not_in', 'IsNotIn'),
    ('matches', 'Matches'),
))
def test_query_operators(func, op):
    """Test query using is_in op."""
    from anansi import Query as Q

    left = 'left'
    right = 'right'

    a = Q(left)
    b = getattr(a, func)(right)
    assert a.left == left
    assert a.right is None
    assert a.op == Q.Op.Is

    assert b.left == left
    assert b.right == right
    assert b.op == Q.Op[op]


def test_query_make_from_values():
    """Test creating a query from a dictionary."""
    from anansi.core.query import make_query_from_values

    q = make_query_from_values({'a': 1, 'b': 2})
    assert q.to_dict() == {
        'type': 'group',
        'op': 'and',
        'queries': [{
            'type': 'query',
            'model': None,
            'left': 'a',
            'op': 'is',
            'right': 1,
        }, {
            'type': 'query',
            'model': None,
            'left': 'b',
            'op': 'is',
            'right': 2,
        }]
    }


def test_query_make_from_values_with_fields():
    """Test creating a query from a dictionary."""
    from anansi import Field
    from anansi.core.query import make_query_from_values

    q = make_query_from_values({
        Field(name='a'): 1,
        Field(name='b'): 2
    })
    assert q.to_dict() == {
        'type': 'group',
        'op': 'and',
        'queries': [{
            'type': 'query',
            'model': None,
            'left': 'a',
            'op': 'is',
            'right': 1,
        }, {
            'type': 'query',
            'model': None,
            'left': 'b',
            'op': 'is',
            'right': 2,
        }]
    }


def test_query_get_left_for_schema():
    """Test getting the left value for a Query."""
    from anansi import Model, Field, Query as Q

    class User(Model):
        id = Field()
        username = Field()

    a = Q('username') == Q('john.doe')
    b = Q('john.doe') == Q('username')

    a_value = a.get_left_for_schema(User.__schema__)
    b_value = b.get_left_for_schema(User.__schema__)

    assert a_value is User.__schema__['username']
    assert b_value == 'john.doe'


def test_query_get_right_for_schema():
    """Test getting the left value for a Query."""
    from anansi import Model, Field, Query as Q

    class User(Model):
        id = Field()
        username = Field()

    a = Q('username') == Q('john.doe')
    b = Q('john.doe') == Q('username')

    a_value = a.get_right_for_schema(User.__schema__)
    b_value = b.get_right_for_schema(User.__schema__)

    assert a_value == 'john.doe'
    assert b_value is User.__schema__['username']
