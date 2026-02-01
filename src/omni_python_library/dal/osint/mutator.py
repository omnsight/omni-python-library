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
        self, id: str, data: Union[RelationMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Relation:
        logger.debug(f"Updating relation {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Relation(**updated)

    def update_event(
        self, id: str, data: Union[EventMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Event:
        logger.debug(f"Updating event {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Event(**updated)

    def update_source(
        self, id: str, data: Union[SourceMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Source:
        logger.debug(f"Updating source {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Source(**updated)

    def update_person(
        self, id: str, data: Union[PersonMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Person:
        logger.debug(f"Updating person {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Person(**updated)

    def update_organization(
        self, id: str, data: Union[OrganizationMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Organization:
        logger.debug(f"Updating organization {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Organization(**updated)

    def update_website(
        self, id: str, data: Union[WebsiteMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> Website:
        logger.debug(f"Updating website {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return Website(**updated)
