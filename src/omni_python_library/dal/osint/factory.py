import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import (
    Event,
    EventMainData,
    Organization,
    OrganizationMainData,
    Person,
    PersonMainData,
    Relation,
    RelationMainData,
    Source,
    SourceMainData,
    Website,
    WebsiteMainData,
)
from omni_python_library.utils import EntityNameConstant

logger = logging.getLogger(__name__)


class OsintDataFactory(ArangoOperator):
    def init(self):
        super().init()

    def create_relation(
        self, data: RelationMainData, owner: str, roles: List[str], in_pending: bool = False
    ) -> Relation:
        logger.debug(f"Creating relation: {data} with owner: {owner}")
        src_col_name, _ = ArangoDBClient().parse_id(data.from_id)
        to_col_name, _ = ArangoDBClient().parse_id(data.to_id)
        collection = ArangoDBClient().get_edge_collection(
            name=data.name,
            from_coll=src_col_name,
            to_coll=to_col_name,
        )

        if in_pending:
            doc = self._create_in_arango(
                collection,
                {"name": data.name, "from_id": data.from_id, "to_id": data.to_id},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                collection,
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                owner=owner,
                roles=roles,
            )

        return Relation(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            from_id=doc["_from"],
            to_id=doc["_to"],
            **doc,
        )

    def create_event(self, data: EventMainData, owner: str, roles: List[str], in_pending: bool = False) -> Event:
        logger.debug(f"Creating event: {data} with owner: {owner}")
        if in_pending:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.EVENT),
                {"title": data.title},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.EVENT),
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                embedding_fields=["title", "description"],
                owner=owner,
                roles=roles,
            )
        return Event(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_source(self, data: SourceMainData, owner: str, roles: List[str], in_pending: bool = False) -> Source:
        logger.debug(f"Creating source: {data} with owner: {owner}")
        if in_pending:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.SOURCE),
                {"title": data.title},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.SOURCE),
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                embedding_fields=["title", "description", "name", "url"],
                owner=owner,
                roles=roles,
            )
        return Source(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_person(self, data: PersonMainData, owner: str, roles: List[str], in_pending: bool = False) -> Person:
        logger.debug(f"Creating person: {data} with owner: {owner}")
        if in_pending:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.PERSON),
                {"name": data.name},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.PERSON),
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                embedding_fields=["name", "role", "nationality"],
                owner=owner,
                roles=roles,
            )
        return Person(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_organization(
        self, data: OrganizationMainData, owner: str, roles: List[str], in_pending: bool = False
    ) -> Organization:
        logger.debug(f"Creating organization: {data} with owner: {owner}")
        if in_pending:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.ORGANIZATION),
                {"name": data.name},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.ORGANIZATION),
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                embedding_fields=["name", "type", "tags"],
                owner=owner,
                roles=roles,
            )
        return Organization(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_website(self, data: WebsiteMainData, owner: str, roles: List[str], in_pending: bool = False) -> Website:
        logger.debug(f"Creating website: {data} with owner: {owner}")
        if in_pending:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.WEBSITE),
                {"url": data.url},
                owner=owner,
                roles=roles,
                pending_data=data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )
        else:
            doc = self._create_in_arango(
                ArangoDBClient().get_collection(EntityNameConstant.WEBSITE),
                data.model_dump(mode="json", by_alias=True, exclude_unset=True),
                embedding_fields=["title", "description", "url"],
                owner=owner,
                roles=roles,
            )
        return Website(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )
