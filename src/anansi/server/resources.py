"""Define Model resource endpoints."""
from typing import Callable, Type
import logging

from .factories import (
    model_route_handler,
    record_route_handler,
)
from .utils import (
    dump_collection,
    dump_record,
    get_values_from_request,
)

log = logging.getLogger(__name__)


def add_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    context_factory: Callable=None,
    path: str=None,
    permits: dict=None,
):
    """Add resource for anansi models."""
    model_path = path or '/{}'.format(model.__schema__.resource_name)
    record_path = '{}/{{key}}'.format(model_path)

    add_record_resource(
        app,
        model,
        context_factory=context_factory,
        path=record_path,
        permits=permits,
    )
    add_model_resource(
        app,
        model,
        context_factory=context_factory,
        path=model_path,
        permits=permits,
    )


def add_model_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    context_factory: Callable=None,
    path: str=None,
    permits: dict=None,
):
    """Add resource endpoint for anansi model."""
    permits = permits or {}
    path = path or '/{}/'.format(model.__schema__.resource_name)

    resource = app.router.add_resource(path)
    resource.add_route('GET', get_records(
        model,
        context_factory=context_factory,
        permit=permits.get('GET')
    ))
    resource.add_route('POST', create_record(
        model,
        context_factory=context_factory,
        permit=permits.get('POST')
    ))
    resource.add_route('PATCH', update_records(
        model,
        context_factory=context_factory,
        permit=permits.get('PATCH'),
    ))
    resource.add_route('PUT', update_records(
        model,
        context_factory=context_factory,
        permit=permits.get('PUT'),
    ))

    return resource


def add_record_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    context_factory: Callable=None,
    path: str=None,
    permits: dict=None,
):
    """Add resource endpoint for aiob records."""
    permits = permits or {}
    path = path or '/{}/{{key}}'.format(model.__schema__.resource_name)

    resource = app.router.add_resource(path)
    resource.add_route('DELETE', delete_record(
        model,
        context_factory=context_factory,
        permit=permits.get('DELETE'),
    ))
    resource.add_route('GET', get_record(
        model,
        context_factory=context_factory,
        permit=permits.get('GET'),
    ))
    resource.add_route('PATCH', update_record(
        model,
        context_factory=context_factory,
        permit=permits.get('PATCH'),
    ))
    resource.add_route('PUT', update_record(
        model,
        context_factory=context_factory,
        permit=permits.get('PUT')
    ))


@model_route_handler
async def create_record(
    model: Type['Model'],
    context: 'orb.Context'=None,
) -> dict:
    """Create a new record based on request values."""
    values = await get_values_from_request(
        context.scope['request'],
        model,
    )
    record = model(values, context=context)
    await record.save()
    return await dump_record(record)


@record_route_handler
async def delete_record(record, context=None):
    """Handle DELETE request for a record."""
    await record.delete()
    return {'status': 'ok'}


@model_route_handler
async def get_records(
    model: Type['Model'],
    context: 'orb.Context'=None,
) -> list:
    """Handle GET endpoint for models."""
    collection = model.select(context=context)
    return await dump_collection(collection)


@record_route_handler
async def get_record(record: 'Model', context: 'orb.Context'=None) -> dict:
    """Serialize a record and return it."""
    return await dump_record(record)


@record_route_handler
async def update_record(record: 'Model', context: 'orb.Context'=None) -> dict:
    """Update a record in the database and return it."""
    values = await get_values_from_request(
        context.scope['request'],
        type(record),
    )
    await record.update(values)
    await record.save()
    return await dump_record(record)


@model_route_handler
async def update_records(
    model: Type['Model'],
    context: 'orb.Context'=None,
) -> list:
    """Update a set of records to a set of values."""
    values = await get_values_from_request(
        context.scope['request'],
        model,
    )
    collection = model.select(context=context)
    await collection.update(values)
    return await dump_collection(collection)
