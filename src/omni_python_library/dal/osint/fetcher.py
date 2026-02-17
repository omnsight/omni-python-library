import logging
from typing import Any, List, Optional, Type, Union

from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import Event, Organization, Person, Relation, Source, Website

logger = logging.getLogger(__name__)


class OsintDataFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_relation(self, id: str, owner: str, roles: List[str], in_pending: bool = False) -> Optional[Relation]:
        return self._get(Relation, id, owner=owner, roles=roles, in_pending=in_pending)

    def get_event(self, id: str, owner: str, roles: List[str], in_pending: bool = False) -> Optional[Event]:
        return self._get(Event, id, owner=owner, roles=roles, in_pending=in_pending)

    def get_source(self, id: str, owner: str, roles: List[str], in_pending: bool = False) -> Optional[Source]:
        return self._get(Source, id, owner=owner, roles=roles, in_pending=in_pending)

    def get_person(self, id: str, owner: str, roles: List[str], in_pending: bool = False) -> Optional[Person]:
        return self._get(Person, id, owner=owner, roles=roles, in_pending=in_pending)

    def get_organization(
        self, id: str, owner: str, roles: List[str], in_pending: bool = False
    ) -> Optional[Organization]:
        return self._get(Organization, id, owner=owner, roles=roles, in_pending=in_pending)

    def get_website(self, id: str, owner: str, roles: List[str], in_pending: bool = False) -> Optional[Website]:
        return self._get(Website, id, owner=owner, roles=roles, in_pending=in_pending)

    def _get(
        self,
        model_cls: Type[Union[Relation, Event, Source, Person, Organization, Website]],
        id: str,
        owner: str,
        roles: List[str],
        in_pending: bool = False,
    ) -> Optional[Any]:
        logger.debug(f"Getting {id}")
        doc = self._get_from_arango(id, owner=owner, roles=roles, in_pending=in_pending)
        if doc:
            return model_cls(**doc)
        return None
