import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app import models

class TestLennyAssistantBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")

    def test_session_lifecycle(self):
        # 1. Create session
        response = self.client.post("/sessions", json={"metadata": {"test": True}})
        self.assertEqual(response.status_code, 201)
        session_data = response.json()
        self.assertIn("id", session_data)
        self.assertEqual(session_data["metadata"]["test"], True)
        
        session_id = session_data["id"]
        
        # 2. Get session details
        response = self.client.get(f"/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        get_data = response.json()
        self.assertEqual(get_data["id"], session_id)
        self.assertEqual(len(get_data["messages"]), 0)

        # 3. Send chat message (Testing fallback logic when similarity is below threshold)
        # Since we have only 234 chunks (or some other count), we can test sending a random string that won't match any growth content
        response = self.client.post(
            f"/sessions/{session_id}/chat",
            json={"message": "What is the capital of France?", "provider": "ollama", "mode": "standard"}
        )
        self.assertEqual(response.status_code, 200)
        chat_data = response.json()
        self.assertEqual(chat_data["content"], "I do not have grounded information on this topic in the ingested transcripts.")
        self.assertEqual(len(chat_data["citations"]), 0)
        
        # 4. Verify chat is preserved in session history
        response = self.client.get(f"/sessions/{session_id}")
        self.assertEqual(response.status_code, 200)
        history_data = response.json()
        self.assertEqual(len(history_data["messages"]), 2)  # 1 user message, 1 assistant message
        self.assertEqual(history_data["messages"][0]["role"], "user")
        self.assertEqual(history_data["messages"][1]["role"], "assistant")

    def test_session_not_found(self):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/sessions/{fake_uuid}")
        self.assertEqual(response.status_code, 404)
        
        response = self.client.post(
            f"/sessions/{fake_uuid}/chat",
            json={"message": "hello", "provider": "ollama", "mode": "standard"}
        )
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
