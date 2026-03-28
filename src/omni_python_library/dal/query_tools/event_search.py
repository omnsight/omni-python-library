from typing import List, Optional, Tuple, Union

from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import Event, Relation
from omni_python_library.utils.config import ArangoDBConstant


def search_events(
    owner: str,
    roles: List[str],
    text: Optional[str] = None,
    date_range: Optional[Tuple[Optional[int], Optional[int]]] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    in_pending: bool = False,
) -> List[Union[Event, Relation]]:
    """
    Queries events and their connecting relations using Vector Search.

    :param text: Text to search for using vector search against the embedding field.
    :param date_range: Tuple of (start_timestamp, end_timestamp).
    :param country_code: ISO country code to filter by.
    :param limit: Maximum number of events to return.
    :param offset: The number of documents to skip.
    :param owner: The owner of the documents to filter by.
    :param roles: The roles to filter by.
    :return: A list of Event and Relation objects.
    """
    bind_vars = {"limit": limit, "offset": offset, "owner": owner, "roles": roles}
    filters = ["FILTER doc.owner == @owner OR (FOR r IN @roles FILTER r IN doc.read LIMIT 1 RETURN true)[0]"]

    if country_code:
        filters.append("FILTER doc.location.country_code == @country_code")
        bind_vars["country_code"] = country_code

    if date_range:
        start, end = date_range
        if start is not None:
            filters.append("FILTER doc.happened_at >= @start")
            bind_vars["start"] = start
        if end is not None:
            filters.append("FILTER doc.happened_at <= @end")
            bind_vars["end"] = end

    vector_search = ""
    if text:
        vector_search = """
            SORT APPROX_NEAR_COSINE(doc.embedding, @vector) DESC
        """
        bind_vars["vector"] = OsintDataAccessLayer().generate_embedding(text)

    filter_str = "\n".join(filters)

    query = f"""
    LET events = (
        FOR doc IN event
            {filter_str}
            {vector_search}
            LIMIT @offset, @limit
            RETURN doc
    )

    LET event_ids = events[*]._id
    LET relations = (
        FOR id IN event_ids
            FOR v, e IN 1..1 ANY id GRAPH '{ArangoDBConstant.EVENT_GRAPH}'
                FILTER e._from IN event_ids AND e._to IN event_ids
                RETURN DISTINCT e
    )

    RETURN {{ nodes: events, edges: relations }}
    """

    return OsintDataAccessLayer().query(query, bind_vars=bind_vars, in_pending=in_pending)
