from typing import Annotated, List, Optional, Tuple, Union

from pydantic import Field

from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
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
    country_code: Annotated[
        Optional[str], Field(description="ISO country code to filter by.")
    ] = None,
    limit: Annotated[
        int, Field(description="Maximum number of events to return.", ge=1, default=50)
    ] = 50,
) -> List[Union[Event, Relation]]:
    """
    Queries events and their connecting relations using ArangoSearch and Vector Search.

    :param text: Text to search for using vector search against the embedding field.
    :param date_range: Tuple of (start_timestamp, end_timestamp).
    :param country_code: ISO country code to filter by.
    :param limit: Maximum number of events to return.
    :return: A list of Event and Relation objects.
    """
    dal = OsintDataAccessLayer()
    bind_vars = {"limit": limit}
    filters = []

    sort_clause = "SORT doc.happened_at DESC"
    if text:
        embedding = dal.generate_embedding(text)
        if embedding:
            bind_vars["vector"] = embedding
            sort_clause = "SORT COSINE_DISTANCE(doc.embedding, @vector) ASC"

    if country_code:
        filters.append("doc.location.country_code == @country_code")
        bind_vars["country_code"] = country_code

    if date_range:
        start, end = date_range
        if start is not None:
            filters.append("doc.happened_at >= @start")
            bind_vars["start"] = start
        if end is not None:
            filters.append("doc.happened_at <= @end")
            bind_vars["end"] = end

    filter_str = " AND ".join(filters) if filters else "TRUE"

    query = f"""
    LET events = (
        FOR doc IN event_view
            SEARCH {filter_str}
            {sort_clause}
            LIMIT @limit
            RETURN doc
    )

    LET event_ids = events[*]._id

    LET relations = (
        FOR doc IN event_view
            SEARCH doc._from IN event_ids AND doc._to IN event_ids
            RETURN doc
    )

    FOR result IN APPEND(events, relations)
        RETURN result
    """

    return dal.query(query, bind_vars=bind_vars)
