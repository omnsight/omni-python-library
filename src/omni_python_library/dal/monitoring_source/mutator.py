import logging
import time

from omni_python_library.dal.monitoring_source.fetcher import MonitoringSourceFetcher
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models import MonitoringSource, MonitoringSourceMainData, RelationMainData
from omni_python_library.utils import NotFoundError

logger = logging.getLogger(__name__)


class MonitoringSourceDataMutator(MonitoringSourceFetcher):
    def init(self):
        super().init()

    def update_monitoring_source(self, id: str, data: MonitoringSourceMainData) -> MonitoringSource:
        logger.debug(f"Updating monitoring source {id} with data {data}")
        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True))
        return MonitoringSource(**updated)

    def connect_monitoring_source_to_view(self, view_id: str, monitoring_source_id: str) -> MonitoringSource:
        logger.debug(f"Connecting monitoring source {monitoring_source_id} to view {view_id}")
        ms = self.get_monitoring_source(monitoring_source_id)
        if not ms:
            raise NotFoundError(f"Monitoring Source {monitoring_source_id} not found")

        # Fetch view to get owner
        view = ViewDataAccessLayer().get_view(view_id)
        if not view:
            raise NotFoundError(f"View {view_id} not found")

        relation_data = RelationMainData(
            name="includes",
            from_id=monitoring_source_id,
            to_id=view_id,
            created_at=int(time.time() * 1000),
        )

        OsintDataAccessLayer().create_relation(relation_data, owner=view.owner)

        return ms
