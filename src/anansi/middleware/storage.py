"""Define storage_middlware class."""
from ..actions import (
    DeleteCollection,
    DeleteRecord,
    FetchCollection,
    FetchCount,
    MakeStorageValue,
    SaveCollection,
    SaveRecord,
)


async def storage_middleware(next):
    """Process middleware actions for a store."""
    async def handler(action):
        action_type = type(action)
        if action_type is DeleteRecord:
            storage = action.context.store.storage
            return await storage.delete_record(
                action.record,
                action.context,
            )

        elif action_type is DeleteCollection:
            storage = action.context.store.storage
            return await storage.delete_collection(
                action.collection,
                action.context,
            )

        elif action_type is FetchCount:
            storage = action.context.store.storage
            return await storage.get_count(
                action.model,
                action.context,
            )

        elif action_type is FetchCollection:
            storage = action.context.store.storage
            return await storage.get_records(
                action.model,
                action.context,
            )

        elif action_type is MakeStorageValue:
            return action.value

        elif action_type is SaveRecord:
            storage = action.context.store.storage
            return await storage.save_record(
                action.record,
                action.context,
            )

        elif action_type is SaveCollection:
            storage = action.context.store.storage
            return await storage.save_collection(
                action.collection,
                action.context,
            )

        else:
            return await next(action)
    return handler
