from typing import Annotated, List, Union

from pydantic import Field

from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website


def search_entity_neighborhood(
    entity_id: Annotated[str, Field(description="The ID of the entity to start the search from.")],
    limit: Annotated[
        int, Field(description="Maximum number of entities to return.", ge=1, default=50)
    ] = 50,
) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
    """
    Searches for all types of entities 1 edge away from the given entity ID.

    :param entity_id: The ID of the entity to start the search from.
    :param limit: Maximum number of entities to return.
    :return: A list of entities found 1 edge away.
    """
    dal = OsintDataAccessLayer()

    # AQL Query
    # We use event_related_view to find edges connected to the entity,
    # and then find the entities on the other side.
    query = f"""
    LET edges = (
        FOR doc IN event_related_view
            SEARCH doc._from == @entity_id OR doc._to == @entity_id
            RETURN doc
    )

    LET neighbor_ids = UNIQUE(
        FOR e IN edges
            RETURN e._from == @entity_id ? e._to : e._from
    )

    LET neighbors = (
        FOR doc IN event_related_view
            SEARCH doc._id IN neighbor_ids
            LIMIT @limit
            RETURN doc
    )

    FOR result IN APPEND(edges, neighbors)
        RETURN result
    """

    return dal.query(query, bind_vars={"entity_id": entity_id, "limit": limit})
