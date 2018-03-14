"""Define SQL based backend engines for testing."""

from .engines import postgres

SQL_ENGINES = {
    'postgres': postgres
}
