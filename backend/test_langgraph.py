import unittest
import asyncio
from backend.graph.state import IncidentState
from backend.graph.nodes.fusion import fusion_node
from backend.models.signal import NormalizedSignal, SignalLocation

class TestLangGraphNodes(unittest.IsolatedAsyncioTestCase):
    async def test_fusion_node_new_cluster(self):
        signal = NormalizedSignal(
            signal_id="sig_test_1234",
            source_type="social",
            source_name="Twitter",
            location=SignalLocation(lat=31.5204, lng=74.3587, area_name="Test Area"),
            timestamp="2026-05-17T00:00:00Z",
            raw_content="Test message",
            credibility_score=0.8
        )
        state: IncidentState = {
            "signal": signal,
            "active_incidents": [],
            "incident_id": None,
            "context": None,
            "credibility_report": None,
            "classification": None,
            "allocation_plan": None,
            "simulations": [],
            "messages": None,
            "status": "detecting",
            "retraction_message": None,
            "errors": [],
            "agent_traces": []
        }
        
        result = await fusion_node(state)
        
        self.assertIn("context", result)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], "inc_candidate_1234")
        self.assertTrue(result["context"].is_new_incident)

if __name__ == '__main__':
    unittest.main()
