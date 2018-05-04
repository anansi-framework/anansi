"""GraphQL Abstract Syntax Tree classes."""
from typing import Any, List


class Node:
    """Base tree class."""

    def __eq__(self, other):
        """Compare equality between two nodes, comparing type and values."""
        return (
            type(other) is type(self) and
            vars(other) == vars(self)
        )


class Document(Node):
    """Root Document node class."""

    def __init__(self, definitions: List[Node]=None):
        self.definitions = definitions or []


class Definition(Node):
    """Base Definition node class type."""

    pass


class FragmentDefinition(Definition):
    """FragmentDefinition node class type."""

    def __init__(
        self,
        name: str,
        type_condition: str,
        *,
        directives: list=None,
        selections: List[Node],
    ):
        self.name = name
        self.type_condition = type_condition
        self.selections = selections
        self.directives = directives or []


class OperationDefinition(Definition):
    """OperationDefinition node class type."""

    def __init__(
        self,
        selections: List[Node],
        *,
        directives: list=None,
        name: str=None,
        variable_definitions: list=None,
    ):
        self.selections = selections
        self.name = name
        self.variable_definitions = variable_definitions or []
        self.directives = directives or []


class Query(OperationDefinition):
    """Define Query operation class type.

    In shorthand notation (when document contains only one query without
    variable definitions or directives) query can be anonymous.
    """

    def __init__(
        self,
        selections: List[Node],
        *,
        directives: str=None,
        name: str='query',
        variable_definitions: str=None,
    ):
        super().__init__(
            selections,
            name=name,
            variable_definitions=variable_definitions,
            directives=directives,
        )


class Mutation(OperationDefinition):
    """Define base Mutation operation class type."""

    pass


class Selection(Node):
    """Define base Selection node class type."""

    pass


class Field(Selection):
    """Define Field selection class type."""

    def __init__(
        self,
        name: str,
        *,
        alias: str=None,
        arguments: list=None,
        directives: list=None,
        selections: list=None,
    ):
        self.name = name
        self.alias = alias
        self.arguments = arguments or []
        self.directives = directives or []
        self.selections = selections or []


class FragmentSpread(Selection):
    """Define FragmentSpread selection node."""

    def __init__(
        self,
        name: str,
        *,
        directives: list=None,
    ):
        self.name = name
        self.directives = directives or []


class InlineFragment(Selection):
    """Define InlineFragment selection node."""

    def __init__(
        self,
        type_condition: str,
        selections: List[Node],
        *,
        directives: list=None,
    ):
        self.type_condition = type_condition
        self.selections = selections
        self.directives = directives or []


class Argument(Node):
    """Define Argument node class type."""

    def __init__(
        self,
        name: str,
        value: Any,
    ):
        self.name = name
        self.value = value


class Value(Node):
    """Value node class type."""

    def __init__(self, value: Any):
        self.value = value


class VariableDefinition(Value):
    """VariableDefinition class type."""

    def __init__(
        self,
        name: str,
        type: str,
        *,
        default_value: Any=None,
        value: Any=None,
    ):
        super().__init__(value)

        self.default_value = default_value
        self.name = name
        self.type = type


class Variable(Value):
    """Variable class type."""

    def __init__(
        self,
        name: str,
        *,
        value: Any=None,
    ):
        super().__init__(value)

        self.name = name


class Directive(Node):
    """Directive node class type."""

    def __init__(
        self,
        name: str,
        *,
        arguments: list=None,
    ):
        self.arguments = arguments or []
        self.name = name


class NodeType(Node):
    """Define Type node class type."""

    pass


class NamedType(NodeType):
    """Define NamedType node class type."""

    def __init__(self, name: str):
        self.name = name


class ListType(NodeType):
    """Define ListType node class type."""

    def __init__(self, type: NodeType):
        self.type = type


class NonNullType(NodeType):
    """Define NotNull node class type."""

    def __init__(self, type: NodeType):
        self.type = type


class TypeCondition(NamedType):
    """Define TypeCondition class type."""

    pass
