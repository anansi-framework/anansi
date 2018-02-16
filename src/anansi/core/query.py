"""Define Query class type."""

from enum import Enum
from typing import Any, Type, Union


class QueryOp(Enum):
    """Query operators."""

    After = 'after'
    Before = 'before'
    Between = 'between'
    Contains = 'contains'
    ContainsInsensitive = 'contains_insensitive'
    DoesNotMatch = 'does_not_match'
    DoesNotStartwith = 'does_not_start_with'
    DoesNotEndWith = 'does_not_end_with'
    Endswith = 'endswith'
    Is = 'is'
    IsIn = 'is_in'
    IsNot = 'is_not'
    IsNotIn = 'is_not_in'
    GreaterThan = 'greater_than'
    GreaterThanOrEqual = 'greater_than_or_equal'
    LessThan = 'less_than'
    LessThanOrEqual = 'less_than_or_equal'
    Matches = 'matches'
    Startswith = 'startswith'


class Query:
    """Python query language builder."""

    Op = QueryOp

    def __init__(
        self,
        *args,
        left: str='',
        model: Union[str, Type['Model']]='',
        op: QueryOp=QueryOp.Is,
        right: Any=None,
    ):
        if len(args) == 1:
            arg = args[0]
            if type(arg) is tuple:
                model, left = arg
            else:
                left = arg
        elif len(args) > 1:
            msg = 'Query() takes 0-1 positional arguments but {} was given'
            raise TypeError(msg.format(len(args)))

        self._model = model
        self.left = left
        self.op = op
        self.right = right

    def __and__(
        self,
        other: Union['Query', 'QueryGroup'],
    ) -> Union['Query', 'QueryGroup']:
        """Join query with another."""
        from .query_group import make_query_group, QueryGroupOp
        return make_query_group(self, other, QueryGroupOp.And)

    def __eq__(self, other: Any) -> 'Query':
        """Set op to Is and right to other."""
        return self.clone({'op': QueryOp.Is, 'right': other})

    def __ne__(self, other: Any) -> 'Query':
        """Set op to IsNot and right to other."""
        return self.clone({'op': QueryOp.IsNot, 'right': other})

    def __or__(
        self,
        other: Union['Query', 'QueryGroup'],
    ) -> Union['Query', 'QueryGroup']:
        """Join query with another."""
        from .query_group import make_query_group, QueryGroupOp
        return make_query_group(self, other, QueryGroupOp.Or)

    def clone(self, values: dict=None):
        """Copy current query and return new object."""
        defaults = {
            'model': self._model,
            'left': self.left,
            'op': self.op,
            'right': self.right,
        }
        defaults.update(values or {})
        return type(self)(**defaults)

    def get_model(self) -> Type['Model']:
        """Return model type associated with this query, if any."""
        if type(self._model) is str:
            from .model import Model
            return Model.find_model(self._model)
        return self._model

    def is_in(self, values: Union[list, tuple, 'Collection']) -> 'Query':
        """Set op to IsIn and right to the values."""
        return self.clone({'op': QueryOp.IsIn, 'right': values})

    def is_not_in(self, values: Union[list, tuple, 'Collection']) -> 'Query':
        """Set op to IsNotIn and right to the values."""
        return self.clone({'op': QueryOp.IsNotIn, 'right': values})

    @property
    def is_null(self) -> bool:
        """Return whether or not this query object is null."""
        return not(self.left or self.model)

    def matches(self, query: str) -> 'Query':
        """Set op to Matches and right to query."""
        return self.clone({'op': QueryOp.Matches, 'right': query})

    def set_model(self, model: Union[str, Type['Model']]):
        """Set model type instance for this query."""
        self._model = model

    model = property(get_model, set_model)


def make_query_from_dict(values: dict) -> Query:
    """Make a query from the given values."""
    q = Query()
    for field, value in values.items():
        if type(field) is str:
            q &= Query(field) == value
        else:
            q &= Query(field.name) == value
    return q
