import logging

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.view import OsintView, OsintViewMainData

logger = logging.getLogger(__name__)


class ViewDataFactory(Cacher):
    def init(self):
        super().init()

    def create_view(self, data: OsintViewMainData, owner: str) -> OsintView:
        logger.debug(f"Creating view: {data.name} with owner: {owner}")

        collection = ArangoDBClient().get_collection("osintview")

        doc = data.model_dump(mode='json', by_alias=True, exclude_unset=True)
        doc["owner"] = owner

        meta = collection.insert(doc, return_new=True)
        new_doc = meta["new"]

        instance = OsintView(id=new_doc["_id"], key=new_doc["_key"], rev=new_doc["_rev"], **new_doc)

        # Cache the new instance
        self.set(instance.id, instance.model_dump(mode='json', by_alias=True))

        return instance
