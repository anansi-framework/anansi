"""Tests for the Context class."""
import pytest


def test_context_creation():
    """Test creating an empty context."""
    from anansi import make_context, ReturnType
    from anansi.core.context import DEFAULT_LOCALE

    context = make_context()
    assert context.distinct is None
    assert context.fields is None
    assert context.locale is DEFAULT_LOCALE
    assert context.limit is None
    assert context.namespace is None
    assert context.order_by is None
    assert context.page is None
    assert context.page_size is None
    assert context.where is None
    assert context.returning is ReturnType.Records
    assert context.scope == {}
    assert context.start is None
    assert context.timezone is None


def test_context_merging():
    """Test merging two contexts together."""
    from anansi import (
        make_context,
        Query as Q,
        QueryGroup,
        Ordering,
    )

    a = make_context(
        distinct='a',
        fields='a,b',
        locale='en_US',
        limit=5,
        order_by='+a,-b',
        scope={'a': 1},
        where=Q('a') == 1,
    )
    b = make_context(
        context=a,
        distinct='b',
        fields=['b', 'c', 'd'],
        locale='fr_FR',
        limit=None,
        scope={'b': 2},
        where=Q('b') != 1,
    )

    assert b.order_by == [('a', Ordering.Asc), ('b', Ordering.Desc)]
    assert b.fields == ['b', 'c', 'd', 'a']
    assert b.scope == {'a': 1, 'b': 2}
    assert type(b.where) == QueryGroup
    assert len(b.where.queries) == 2
    assert b.distinct == {'a', 'b'}
    assert b.locale == 'fr_FR'
    assert b.limit is None


@pytest.mark.parametrize('base,distinct,result', (
    (None, None, None),
    (None, True, True),
    (True, None, True),
    (None, 'a', {'a'}),
    (None, ['a'], {'a'}),
    (None, ('a',), {'a'}),
    ('a', 'b', {'a', 'b'}),
    ('a,b', 'c,d', {'a', 'b', 'c', 'd'}),
    ('a', True, {'a'}),
    (True, 'a', {'a'}),
))
def test_context_distinct(base, distinct, result):
    """Test merging distinct field."""
    from anansi import make_context
    base_context = make_context(distinct=base)
    test_context = make_context(distinct=distinct, context=base_context)
    assert test_context.distinct == result


def test_context_limiting():
    """Test basic context limiting options."""
    from anansi import make_context

    context = make_context(start=10, limit=10)
    assert context.page is None
    assert context.page_size is None
    assert context.start == 10
    assert context.limit == 10

    context.start = 20
    context.limit = 20

    assert context.start == 20
    assert context.limit == 20


def test_context_page_limiting():
    """Test page based context limiting options."""
    from anansi import make_context

    context = make_context(
        page=2,
        page_size=100
    )

    assert context.page == 2
    assert context.page_size == 100
    assert context.start == 100
    assert context.limit == 100

    context.start = 20
    context.limit = 20

    assert context.start == 100
    assert context.limit == 100


@pytest.mark.parametrize('options,base_context,expected', (
    ({'include': 'a,b,b.c'}, None, {'a': {}, 'b': {'c': {}}}),
    ({'fields': 'a,b.c,b.d,b.e.f'}, None, {'b': {'e': {}}}),
    ({'include': 'a', 'fields': 'a.b'}, None, {'a': {}}),
    ({'include': 'a'}, {'include': 'b'}, {'a': {}, 'b': {}}),
    ({'include': ['a', 'c']}, {'include': 'b'}, {'a': {}, 'b': {}, 'c': {}}),
    ({'include': ('a', 'c')}, {'include': 'b'}, {'a': {}, 'b': {}, 'c': {}}),
))
def test_context_inclusion(options, base_context, expected):
    """Test including references from the context."""
    from anansi import make_context

    if base_context:
        options['context'] = make_context(**base_context)
    context = make_context(**options)
    assert context.include == expected


@pytest.mark.parametrize(
    ','.join((
        'schema_namespace',
        'context_namespace',
        'store_namespace',
        'default_namespace',
        'expected_namespace',
    )),
    (
        ('', '', '', '', ''),
        ('', '', '', 'a', 'a'),
        ('', '', 'b', 'a', 'b'),
        ('', 'c', 'b', 'a', 'c'),
        ('d', 'c', 'b', 'a', 'd'),
    )
)
def test_context_resolve_namespace(
    schema_namespace,
    context_namespace,
    store_namespace,
    default_namespace,
    expected_namespace,
):
    """Test resolving of namespaces."""
    from anansi import Schema, Store, make_context
    from anansi.core.context import resolve_namespace

    schema = Schema(namespace=schema_namespace)
    store = Store(namespace=store_namespace)
    context = make_context(store=store, namespace=context_namespace)

    result = resolve_namespace(schema, context, default=default_namespace)
    assert result == expected_namespace
