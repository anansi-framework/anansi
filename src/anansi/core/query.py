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
        left: str='',
        *,
        model: Union[str, Type['Model']]='',
        op: QueryOp=QueryOp.Is,
        right: Any=None,
    ):
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

    def get_left_for_schema(self, schema: 'Schema') -> Any:
        """Return the left value for a given schema."""
        try:
            field = schema.fields[self.left]
        except KeyError:
            pass
        else:
            return field
        return self.left

    def get_model(self) -> Type['Model']:
        """Return model type associated with this query, if any."""
        if type(self._model) is str:
            from .model import Model
            return Model.find_model(self._model)
        return self._model

    def get_right_for_schema(self, schema: 'Schema') -> Any:
        """Return the left value for a given schema."""
        if (
            type(self.right) is Query and
            self.right.right is None and
            self.right.op is Query.Op.Is
        ):
            try:
                field = schema.fields[self.right.left]
            except KeyError:
                pass
            else:
                return field
        return self.right

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

    def to_dict(self):
        """Return the query as a dictionary."""
        left = self.left
        right = self.right

        if hasattr(left, 'to_dict'):
            left = left.to_dict()
        if hasattr(right, 'to_dict'):
            right = right.to_dict()

        if self._model and type(self._model) != str:
            model_name = self._model.__schema__.name
        elif self._model:
            model_name = self._model
        else:
            model_name = None

        out = {
            'type': 'query',
            'model': model_name,
            'op': self.op.value,
            'left': left,
            'right': right,
        }
        return out

    model = property(get_model, set_model)


def make_query_from_values(values: dict) -> Query:
    """Make a query from the given values."""
    q = Query()
    for field, value in values.items():
        if type(field) is str:
            q &= Query(field) == value
        else:
            q &= Query(field.name) == value
    return q
