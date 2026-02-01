import logging
from typing import List, Optional, Union

from omni_python_library.clients import ArangoDBClient, OpenAIClient
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
from omni_python_library.utils import EntityNameConstant, InternalError, LLMConstant

logger = logging.getLogger(__name__)


class OsintDataFactory(ArangoOperator):
    def init(self):
        super().init()

    def create_relation(self, data: RelationMainData, owner: str) -> Relation:
        logger.debug(f"Creating relation: {data} with owner: {owner}")
        src_col_name, _ = ArangoDBClient().parse_id(data.from_id)
        to_col_name, _ = ArangoDBClient().parse_id(data.to_id)
        collection = ArangoDBClient().get_edge_collection(
            name=data.name,
            from_coll=src_col_name,
            to_coll=to_col_name,
        )

        doc = self._create_in_arango(
            collection,
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            owner=owner,
        )
        return Relation(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            from_id=doc["_from"],
            to_id=doc["_to"],
            **doc,
        )

    def create_event(self, data: EventMainData, owner: str) -> Event:
        logger.debug(f"Creating event: {data} with owner: {owner}")
        parts = [data.title, data.description, data.type]
        if data.location:
            parts.append(str(data.location.model_dump()))
        text = " ".join([str(p) for p in parts if p])
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.EVENT),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding=self.generate_embedding(text),
            owner=owner,
        )
        return Event(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_source(self, data: SourceMainData, owner: str) -> Source:
        logger.debug(f"Creating source: {data} with owner: {owner}")
        text = f"{data.title} {data.description} {data.name} {data.url}"
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.SOURCE),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding=self.generate_embedding(text),
            owner=owner,
        )
        return Source(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_person(self, data: PersonMainData, owner: str) -> Person:
        logger.debug(f"Creating person: {data} with owner: {owner}")
        aliases = " ".join(data.aliases) if data.aliases else ""
        text = f"{data.name} {data.role} {data.nationality} {aliases}"
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.PERSON),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding=self.generate_embedding(text),
            owner=owner,
        )
        return Person(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_organization(self, data: OrganizationMainData, owner: str) -> Organization:
        logger.debug(f"Creating organization: {data} with owner: {owner}")
        tags = " ".join(data.tags) if data.tags else ""
        text = f"{data.name} {data.type} {tags}"
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.ORGANIZATION),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding=self.generate_embedding(text),
            owner=owner,
        )
        return Organization(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def create_website(self, data: WebsiteMainData, owner: str) -> Website:
        logger.debug(f"Creating website: {data} with owner: {owner}")
        text = f"{data.title} {data.description} {data.url}"
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.WEBSITE),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            embedding=self.generate_embedding(text),
            owner=owner,
        )
        return Website(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )

    def generate_embedding(self, text: Optional[str]) -> Union[List[float] | None]:
        client_tuple = OpenAIClient().get_client(LLMConstant.EMBEDDING)
        if not client_tuple or not text:
            return None

        client, model = client_tuple
        if not client:
            return None

        try:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            raise InternalError("Error generating embedding") from e
