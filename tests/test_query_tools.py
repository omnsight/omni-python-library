import unittest
from unittest.mock import MagicMock, patch

from omni_python_library.dal.query_tools.event_search import search_events
from omni_python_library.dal.query_tools.entity_neighborhood import search_entity_neighborhood

class TestQueryTools(unittest.TestCase):
    
    @patch("omni_python_library.dal.query_tools.event_search.OsintDataAccessLayer")
    def test_search_events(self, mock_dal_cls):
        mock_dal = mock_dal_cls.return_value
        mock_dal.generate_embedding.return_value = [0.1, 0.2]
        mock_dal.query.return_value = []
        
        # Test with text
        search_events(text="test", limit=10)
        
        args, kwargs = mock_dal.query.call_args
        query = args[0]
        bind_vars = kwargs['bind_vars']
        
        self.assertIn("SORT COSINE_DISTANCE(doc.embedding, @vector) ASC", query)
        self.assertIn("LIMIT @limit", query)
        self.assertEqual(bind_vars['vector'], [0.1, 0.2])
        self.assertEqual(bind_vars['limit'], 10)
        
        # Test with filters
        search_events(country_code="US", date_range=(100, 200))
        args, kwargs = mock_dal.query.call_args
        query = args[0]
        bind_vars = kwargs['bind_vars']
        self.assertIn("doc.location.country_code == @country_code", query)
        self.assertIn("doc.happened_at >= @start", query)
        self.assertEqual(bind_vars['country_code'], "US")
        self.assertEqual(bind_vars['start'], 100)
        self.assertEqual(bind_vars['limit'], 50) # Default

    @patch("omni_python_library.dal.query_tools.entity_neighborhood.OsintDataAccessLayer")
    def test_search_entity_neighborhood(self, mock_dal_cls):
        mock_dal = mock_dal_cls.return_value
        
        search_entity_neighborhood("id/123", limit=5)
        
        args, kwargs = mock_dal.query.call_args
        query = args[0]
        bind_vars = kwargs['bind_vars']
        
        self.assertIn("event_related_view", query)
        self.assertIn("SEARCH doc._from == @entity_id OR doc._to == @entity_id", query)
        self.assertIn("LIMIT @limit", query)
        self.assertEqual(bind_vars['limit'], 5)

if __name__ == "__main__":
    unittest.main()
