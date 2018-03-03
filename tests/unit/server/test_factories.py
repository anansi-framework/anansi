"""Test server factories."""
from aiohttp.web import HTTPForbidden
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('exception,status,expected', (
    (
        HTTPForbidden(),
        403,
        b'{"error": "HTTPForbidden", "description": "Forbidden"}'
    ),
    (
        RuntimeError(),
        500,
        b'{"error": "UnknownServerException", '
        b'"description": "Unknown server error."}',
    ),
))
async def test_error_response(exception, status, expected):
    """Test error response generation."""
    from anansi.server.factories import error_response
    response = error_response(exception)
    assert response.status == status
    assert response.body == expected
