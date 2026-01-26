from typing import Annotated, List, Optional, Tuple, Union

from pydantic import Field

from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer, EVENT_GRAPH_NAME
from omni_python_library.models.osint import Event, Relation


def search_events(
    text: Annotated[
        Optional[str],
        Field(description="Text to search for using vector search against the embedding field."),
    ] = None,
    date_range: Annotated[
        Optional[Tuple[Optional[int], Optional[int]]],
        Field(description="Tuple of (start_timestamp, end_timestamp)."),
    ] = None,
    country_code: Annotated[Optional[str], Field(description="ISO country code to filter by.")] = None,
    limit: Annotated[int, Field(description="Maximum number of events to return.", ge=1, default=50)] = 50,
) -> List[Union[Event, Relation]]:
    """
    Queries events and their connecting relations using Vector Search.

    :param text: Text to search for using vector search against the embedding field.
    :param date_range: Tuple of (start_timestamp, end_timestamp).
    :param country_code: ISO country code to filter by.
    :param limit: Maximum number of events to return.
    :return: A list of Event and Relation objects.
    """
    bind_vars = {"limit": limit}
    filters = []

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
            LET distance = VECTOR_DISTANCE(doc.embedding, @vector, "cosine")
            SORT distance ASC
        """
        bind_vars["vector"] = OsintDataAccessLayer().generate_embedding(text)

    filter_str = "\n".join(filters) if filters else ""

    query = f"""
    LET events = (
        FOR doc IN event
            {filter_str}
            {vector_search}
            LIMIT @limit
            RETURN doc
    )

    LET event_ids = events[*]._id
    LET relations = (
        FOR event IN events
            FOR v, e IN 1..1 ANY event GRAPH '{EVENT_GRAPH_NAME}'
            FILTER e._from IN event_ids AND e._to IN event_ids
            RETURN DISTINCT e
    )

    FOR result IN APPEND(events, relations)
        RETURN result
    """

    return OsintDataAccessLayer().query(query, bind_vars=bind_vars)
