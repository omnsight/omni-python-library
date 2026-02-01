import logging
from typing import Any, List, Optional, Type, Union

from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import Event, Organization, Person, Relation, Source, Website

logger = logging.getLogger(__name__)


class OsintDataFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_relation(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Relation]:
        return self._get(Relation, id, owner=owner, roles=roles)

    def get_event(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Event]:
        return self._get(Event, id, owner=owner, roles=roles)

    def get_source(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Source]:
        return self._get(Source, id, owner=owner, roles=roles)

    def get_person(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Person]:
        return self._get(Person, id, owner=owner, roles=roles)

    def get_organization(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Organization]:
        return self._get(Organization, id, owner=owner, roles=roles)

    def get_website(self, id: str, owner: str = None, roles: List[str] = []) -> Optional[Website]:
        return self._get(Website, id, owner=owner, roles=roles)

    def _get(
        self,
        model_cls: Type[Union[Relation, Event, Source, Person, Organization, Website]],
        id: str,
        owner: str = None,
        roles: List[str] = [],
    ) -> Optional[Any]:
        logger.debug(f"Getting {id}")
        doc = self._get_from_arango(id, owner=owner, roles=roles)
        if doc:
            return model_cls(**doc)
        return None
