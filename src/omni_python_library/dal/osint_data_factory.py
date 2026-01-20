from typing import Any, Optional, Type, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.openai import OpenAIClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website


class OsintDataFactory(Cacher):
    def init(self):
        super().init()

    def create_relation(self, data: Relation) -> Relation:
        src_col_name, _ = ArangoDBClient().parse_id(data.from_id)
        to_col_name, _ = ArangoDBClient().parse_id(data.to_id)
        collection = ArangoDBClient().get_edge_collection(
            name=data.name,
            from_coll=src_col_name,
            to_coll=to_col_name,
        )
        meta = collection.insert(data.model_dump(by_alias=True), return_new=True)
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

    def create_event(self, data: Event) -> Event:
        parts = [data.title, data.description, data.type]
        if data.location:
            parts.append(str(data.location.model_dump()))
        text = " ".join([str(p) for p in parts if p])
        return self._create(Event, data, text)

    def create_source(self, data: Source) -> Source:
        text = f"{data.title} {data.description} {data.name} {data.url}"
        return self._create(Source, data, text)

    def create_person(self, data: Person) -> Person:
        aliases = " ".join(data.aliases) if data.aliases else ""
        text = f"{data.name} {data.role} {data.nationality} {aliases}"
        return self._create(Person, data, text)

    def create_organization(self, data: Organization) -> Organization:
        tags = " ".join(data.tags) if data.tags else ""
        text = f"{data.name} {data.type} {tags}"
        return self._create(Organization, data, text)

    def create_website(self, data: Website) -> Website:
        text = f"{data.title} {data.description} {data.url}"
        return self._create(Website, data, text)

    def _generate_embedding(self, text: Optional[str]):
        client, model = OpenAIClient().get_client("embedding")
        if not client or not text:
            return None

        try:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def _create(
        self,
        model_cls: Type[Union[Event, Source, Person, Organization, Website]],
        data: Union[Event, Source, Person, Organization, Website],
        text: Optional[str] = None,
    ) -> Any:
        collection = ArangoDBClient().get_collection(model_cls.__name__)

        # Generate embedding
        embedding = self._generate_embedding(text)

        # Insert into Arango
        doc = data.model_dump(by_alias=True)
        if embedding:
            doc["embedding"] = embedding

        meta = collection.insert(doc, return_new=True)
        new_doc = meta["new"]

        instance = model_cls(id=new_doc["_id"], key=new_doc["_key"], rev=new_doc["_rev"], **new_doc)

        # Cache the new instance
        self.set(instance.id, instance.model_dump(by_alias=True))

        return instance
