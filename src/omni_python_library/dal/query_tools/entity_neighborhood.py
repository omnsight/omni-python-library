from typing import Annotated, List, Union

from pydantic import Field

from omni_python_library.dal.osint_data_access_layer import EVENT_RELATED_GRAPH_NAME, OsintDataAccessLayer
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website


def search_entity_neighborhood(
    entity_id: Annotated[str, Field(description="The ID of the entity to start the search from.")],
    limit: Annotated[int, Field(description="Maximum number of entities to return.", ge=1, default=50)] = 50,
) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
    """
    Searches for all types of entities 1 edge away from the given entity ID.

    :param entity_id: The ID of the entity to start the search from.
    :param limit: Maximum number of entities to return.
    :return: A list of entities found 1 edge away.
    """
    query = f"""
    FOR v, e IN 1..1 ANY @entity_id GRAPH '{EVENT_RELATED_GRAPH_NAME}'
        LIMIT @limit
        RETURN v
    """

    return OsintDataAccessLayer().query(query, bind_vars={"entity_id": entity_id, "limit": limit})
