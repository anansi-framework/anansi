"""Define GraphQL ply lexer."""
from decimal import Decimal
from ply.lex import TOKEN
import ply.lex as lex

from .exceptions import LexerError


LINE_TERMINATORS = '\n\r\u2028\u2029'

RE_ESCAPED_CHAR = r'\\[\"\\/bfnrt]'
RE_ESCAPED_UNICODE = r'\\u[0-9A-Fa-f]{4}'
RE_EXPONENT_PART = r'[eE][\+-]?[0-9]+'
RE_FRACTION_PART = r'\.[0-9]+'
RE_INT_VALUE = r'(-?0|-?[1-9][0-9]*)'
RE_LINE_TERMINATORS = r'\n\r\u2028\u2029'

RE_NEWLINE = r'[{}]+'.format(RE_LINE_TERMINATORS)
RE_STRING_CHAR = r'[^\"\\{}]'.format(RE_LINE_TERMINATORS)


class GraphQLLexer:
    """GraphQL lexer with PLY interface."""

    def __init__(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)
        self._lexer.lineno = 1
        self.text = ''

    def __iter__(self):
        """Define iterator interface."""
        t = self.token()
        while t:
            yield t

    def input(self, s: str) -> 'GraphQLLexer':
        """Process text input."""
        self._lexer.lineno = 1
        self._lexer.input(s)
        self.text = s
        return self

    def token(self) -> 'Token':
        """Return current token position."""
        return self._lexer.token()

    def find_column(self, t: str) -> int:
        """Return token position in current text, starting from 1."""
        cr = max(
            self.text.rfind(l, 0, t.lexpos)
            for l in LINE_TERMINATORS
        )
        if cr == -1:
            return t.lexpos + 1
        return t.lexpos - cr

    tokens = [
        'AT',
        'BANG',
        'BRACE_L',
        'BRACE_R',
        'BRACKET_L',
        'BRACKET_R',
        'COLON',
        'DOLLAR',
        'EQUALS',
        'FALSE',
        'FLOAT_VALUE',
        'FRAGMENT',
        'INT_VALUE',
        'MUTATION',
        'NAME',
        'NULL',
        'ON',
        'PAREN_L',
        'PAREN_R',
        'QUERY',
        'SPREAD',
        'STRING_VALUE',
        'TRUE',
    ]

    t_ignore = ' \t\v\f\u00A0,'
    t_ignore_COMMENT = r'\#[^{}]*'.format(RE_LINE_TERMINATORS)

    t_AT = '@'
    t_BANG = '!'
    t_BRACE_L = r'\{'
    t_BRACE_R = r'\}'
    t_BRACKET_L = r'\['
    t_BRACKET_R = r'\]'
    t_COLON = ':'
    t_DOLLAR = r'\$'
    t_EQUALS = '='
    t_FALSE = r'\bfalse\b'
    t_FRAGMENT = r'\bfragment\b'
    t_MUTATION = r'\bmutation\b'
    t_NAME = r'[_A-Za-z][_0-9A-Za-z]*'
    t_NULL = r'\bnull\b'
    t_ON = r'\bon\b'
    t_PAREN_L = r'\('
    t_PAREN_R = r'\)'
    t_QUERY = r'\bquery\b'
    t_SPREAD = r'\.{3}'
    t_TRUE = r'\btrue\b'

    def t_error(self, t: 'Token') -> 'Token':
        """Process token error."""
        raise LexerError(
            message='Illegal character {}'.format(repr(t.value[0])),
            value=t.value,
            line=t.lineno,
            column=self.find_column(t),
        )

    @TOKEN(RE_NEWLINE)
    def t_newline(self, t: 'Token') -> 'Token':
        """Return NEWLINE token."""
        t.lexer.lineno += len(t.value)
        return

    @TOKEN(r'\"({})*\"'.format('|'.join((
        RE_ESCAPED_CHAR,
        RE_ESCAPED_UNICODE,
        RE_STRING_CHAR
    ))))
    def t_STRING_VALUE(self, t: 'Token') -> 'Token':
        """Create STRING token, stripping off leading and trailing quotes."""
        t.value = t.value[1:-1]
        return t

    @TOKEN('|'.join((
        RE_INT_VALUE + RE_FRACTION_PART + RE_EXPONENT_PART,
        RE_INT_VALUE + RE_FRACTION_PART,
        RE_INT_VALUE + RE_EXPONENT_PART,
    )))
    def t_FLOAT_VALUE(self, t: 'Token') -> 'Token':
        """Create FLOAT token, converting to a Decimal value."""
        t.value = Decimal(t.value)
        return t

    @TOKEN(RE_INT_VALUE)
    def t_INT_VALUE(self, t: 'Token') -> 'Token':
        """Return INT value, converting token to integer."""
        t.value = int(t.value)
        return t
