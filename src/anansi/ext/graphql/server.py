"""Registers endpoints for GraphQL support within the server."""
from aiohttp.web import json_response
from anansi.ext.graphql import (
    GraphQL,
    ParseError,
    resolve_document,
)
from anansi.server import (
    error_response,
    make_context_from_request,
)
from anansi.utils.json import dumps
import logging

log = logging.getLogger(__name__)
parser = GraphQL()


async def post_graphql(request: 'aiohttp.Request') -> 'aiohttp.Response':
    """Process GraphQL request."""
    json = await request.json()
    try:
        gql = json['query']
    except KeyError as exc:
        return error_response(exc, status=400)

    try:
        document = parser.parse(gql)
    except ParseError as exc:
        log.exception('Failed to parse query.')
        return error_response(exc, status=400)

    context = await make_context_from_request(request)
    response = await resolve_document(document, context)
    return json_response(response, dumps=dumps)


def setup(app: 'aiohttp.UrlDispatcher'):
    """Configure the GraphQL server API endpoint."""
    config = app['anansi.config']
    url = config.get('graphql.url', '/graphql')
    route = app.router.add_route('POST', url, post_graphql)

    try:
        cors = app['aiohttp_cors']
    except KeyError:
        pass
    else:
        cors.add(route)
