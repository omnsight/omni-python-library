import logging
from typing import Any, List, Optional, Type, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.openai import OpenAIClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.osint import (
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
from omni_python_library.utils.config_registry import LLMConstant

logger = logging.getLogger(__name__)


class OsintDataFactory(Cacher):
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

        relation_data = Relation(**data.model_dump(exclude_unset=True), owner=owner)

        meta = collection.insert(relation_data.model_dump(by_alias=True, exclude_unset=True), return_new=True)
        new_doc = meta["new"]
        new_data = Relation(
            id=new_doc["_id"],
            key=new_doc["_key"],
            rev=new_doc["_rev"],
            from_id=new_doc["_from"],
            to_id=new_doc["_to"],
            **new_doc,
        )
        # Cache the new instance
        self.set(new_data.id, new_data.model_dump(by_alias=True))

        return new_data

    def create_event(self, data: EventMainData, owner: str) -> Event:
        parts = [data.title, data.description, data.type]
        if data.location:
            parts.append(str(data.location.model_dump()))
        text = " ".join([str(p) for p in parts if p])

        return self._create(
            Event,
            Event(**data.model_dump(exclude_unset=True), owner=owner),
            text,
        )

    def create_source(self, data: SourceMainData, owner: str) -> Source:
        text = f"{data.title} {data.description} {data.name} {data.url}"

        return self._create(
            Source,
            Source(**data.model_dump(exclude_unset=True), owner=owner),
            text,
        )

    def create_person(self, data: PersonMainData, owner: str) -> Person:
        aliases = " ".join(data.aliases) if data.aliases else ""
        text = f"{data.name} {data.role} {data.nationality} {aliases}"

        return self._create(
            Person,
            Person(**data.model_dump(exclude_unset=True), owner=owner),
            text,
        )

    def create_organization(self, data: OrganizationMainData, owner: str) -> Organization:
        tags = " ".join(data.tags) if data.tags else ""
        text = f"{data.name} {data.type} {tags}"

        return self._create(
            Organization,
            Organization(**data.model_dump(exclude_unset=True), owner=owner),
            text,
        )

    def create_website(self, data: WebsiteMainData, owner: str) -> Website:
        text = f"{data.title} {data.description} {data.url}"
        return self._create(
            Website,
            Website(**data.model_dump(exclude_unset=True), owner=owner),
            text,
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
        except Exception:
            logger.exception("Error generating embedding")
            return None

    def _create(
        self,
        model_cls: Type[Union[Event, Source, Person, Organization, Website]],
        data: Union[Event, Source, Person, Organization, Website],
        text: Optional[str] = None,
    ) -> Any:
        collection = ArangoDBClient().get_collection(model_cls.__name__.lower())
        logger.debug(f"Creating {collection.name}: {data} with owner: {data.owner}")

        # Generate embedding
        embedding = self.generate_embedding(text)

        # Insert into Arango
        doc = data.model_dump(by_alias=True, exclude_unset=True)
        if embedding:
            doc["embedding"] = embedding

        meta = collection.insert(doc, return_new=True)
        new_doc = meta["new"]

        instance = model_cls(id=new_doc["_id"], key=new_doc["_key"], rev=new_doc["_rev"], **new_doc)

        # Cache the new instance
        self.set(instance.id, instance.model_dump(by_alias=True))

        return instance
