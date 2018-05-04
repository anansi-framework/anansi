"""Define parser exception classes."""


class ParseError(Exception):
    """Base GraphQL parser exception class."""

    def __init__(self, message=None, value=None, line=None, column=None):
        super().__init__(message)

        self.value = value
        self.line = line
        self.column = column

    def __str__(self) -> str:
        """Convert exception to string."""
        message = super(ParseError, self).__str__()
        if self.line:
            position_info = 'Line %s' % self.line
            if self.column:
                position_info += ', col %s' % self.column
            return '%s: %s' % (position_info, message)
        else:
            return message


class LexerError(ParseError):
    """Error raised during lexer compilation."""

    pass


class SyntaxError(ParseError):
    """Error raised during parsing GraphQL commands."""

    pass


def raise_syntax_error(message: str, token: 'Token'=None):
    """Raise syntax error."""
    if token is None:
        raise SyntaxError(message)

    lexer = token.lexer
    if callable(getattr(lexer, 'find_column', None)):
        column = lexer.find_column(token)
    else:
        column = None

    raise SyntaxError(
        message=message,
        value=token.value,
        line=token.lineno,
        column=column,
    )
