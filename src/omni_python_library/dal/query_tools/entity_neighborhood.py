from typing import List, Union

from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models import Event, Organization, Person, Relation, Source, Website
from omni_python_library.utils import ArangoDBConstant


def search_entity_neighborhood(
    entity_id: str,
    limit: int = 50,
    in_pending: bool = False,
) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
    """
    Searches for all types of entities 1 edge away from the given entity ID.

    :param entity_id: The ID of the entity to start the search from.
    :param limit: Maximum number of entities to return.
    :return: A list of entities found 1 edge away.
    """
    query = f"""
    FOR v, e IN 1..1 ANY @entity_id GRAPH '{ArangoDBConstant.EVENT_RELATED_GRAPH}'
        LIMIT @limit
        RETURN v
    """

    return OsintDataAccessLayer().query(
        query, bind_vars={"entity_id": entity_id, "limit": limit}, in_pending=in_pending
    )
