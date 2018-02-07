"""Define storage_middlware class."""
from ..actions.store import (
    DeleteCollection,
    DeleteRecord,
    GetCount,
    GetRecords,
    MakeStoreValue,
    SaveCollection,
    SaveRecord,
)


def storage_middleware(storage: 'AbstractStorage'):
    """Process middleware actions for a store."""
    async def middleware(next):
        async def handler(action):
            action_type = type(action)
            if action_type is DeleteRecord:
                return await storage.delete_record(
                    action.record,
                    action.context,
                )

            elif action_type is DeleteCollection:
                return await storage.delete_collection(
                    action.collection,
                    action.context,
                )

            elif action_type is GetCount:
                return await storage.get_count(
                    action.model,
                    action.context,
                )

            elif action_type is GetRecords:
                return await storage.get_records(
                    action.model,
                    action.context,
                )

            elif action_type is MakeStoreValue:
                return action.value

            elif action_type is SaveRecord:
                return await storage.save_record(
                    action.record,
                    action.context,
                )

            elif action_type is SaveCollection:
                return await storage.save_collection(
                    action.collection,
                    action.context,
                )

            else:
                return await next(action)
        return handler
    return middleware
