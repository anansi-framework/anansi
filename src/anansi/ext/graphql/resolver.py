"""Resolves GraphQL documents into anansi records."""
import asyncio


async def resolve_document(
    document: 'anansi.ext.graphql.ast.Document',
    context: 'anansi.Context',
):
    """Resolve GraphQL document."""
    operation = document.definitions[0]
    if operation.name == 'query':
        results = await resolve_query(operation, context)
        if len(results) == 1:
            return results[0]
        return results
    else:
        return []


async def resolve_query(
    query: 'anansi.ext.graphql.ast.Query',
    context: 'anansi.Context',
):
    """Resolve GraphQL query."""
    tasks = []
    for selection in query.selections:
        tasks.append(resolve_selection(selection, context))
    return await asyncio.gather(*tasks)


async def resolve_selection(
    selection: 'anansi.ext.graphql.ast.Node',
    context: 'anansi.Context',
):
    """Resolve root GraphQL query selection."""
    print('select from store:')
    print(selection.name)
    print(selection.arguments)
    print(selection.selections)
    return []
