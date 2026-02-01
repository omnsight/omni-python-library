import logging
from typing import Any, List, Optional, Type, Union

from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import Event, Organization, Person, Relation, Source, Website

logger = logging.getLogger(__name__)


class OsintDataFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_relation(self, id: str) -> Optional[Relation]:
        return self._get(Relation, id)

    def get_event(self, id: str) -> Optional[Event]:
        return self._get(Event, id)

    def get_source(self, id: str) -> Optional[Source]:
        return self._get(Source, id)

    def get_person(self, id: str) -> Optional[Person]:
        return self._get(Person, id)

    def get_organization(self, id: str) -> Optional[Organization]:
        return self._get(Organization, id)

    def get_website(self, id: str) -> Optional[Website]:
        return self._get(Website, id)

    def _get(
        self, model_cls: Type[Union[Relation, Event, Source, Person, Organization, Website]], id: str
    ) -> Optional[Any]:
        logger.debug(f"Getting {id}")
        doc = self._get_from_arango(id)
        if doc:
            return model_cls(**doc)
        return None
