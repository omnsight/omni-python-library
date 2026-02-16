import logging
from typing import List, Union

from omni_python_library.dal.osint.fetcher import OsintDataFetcher
from omni_python_library.models import (
    Event,
    EventMainData,
    Organization,
    OrganizationMainData,
    Permissive,
    Person,
    PersonMainData,
    Relation,
    RelationMainData,
    Source,
    SourceMainData,
    Website,
    WebsiteMainData,
)

logger = logging.getLogger(__name__)


class OsintDataMutator(OsintDataFetcher):
    def init(self):
        super().init()

    def update_relation(
        self,
        id: str,
        data: Union[RelationMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Relation:
        logger.debug(f"Updating relation {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Relation(**updated)

    def update_event(
        self,
        id: str,
        data: Union[EventMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Event:
        logger.debug(f"Updating event {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding_fields=["title", "description"],
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Event(**updated)

    def update_source(
        self,
        id: str,
        data: Union[SourceMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Source:
        logger.debug(f"Updating source {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding_fields=["title", "description", "name", "url"],
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Source(**updated)

    def update_person(
        self,
        id: str,
        data: Union[PersonMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Person:
        logger.debug(f"Updating person {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding_fields=["name", "role", "nationality"],
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Person(**updated)

    def update_organization(
        self,
        id: str,
        data: Union[OrganizationMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Organization:
        logger.debug(f"Updating organization {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding_fields=["name", "type", "tags"],
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Organization(**updated)

    def update_website(
        self,
        id: str,
        data: Union[WebsiteMainData, Permissive],
        owner: str = None,
        roles: List[str] = [],
        in_pending: bool = False,
    ) -> Website:
        logger.debug(f"Updating website {id} with data {data}")
        updated = self._update_in_arango(
            id,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding_fields=["title", "description", "url"],
            owner=owner,
            roles=roles,
            in_pending=in_pending,
        )
        return Website(**updated)
