import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Ensure the app imports successfully by adding the directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

class TestServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")


    @patch('server.get_terminal_approval')
    @patch('server.get_credentials')
    @patch('server.append_to_doc')
    def test_append_to_doc_approved(self, mock_append, mock_get_creds, mock_approve):
        mock_approve.return_value = True
        mock_get_creds.return_value = MagicMock()
        mock_append.return_value = {"mock_response": "ok"}

        response = self.client.post("/append_to_doc", json={
            "doc_id": "test_doc_123",
            "content": "hello world"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "response": {"mock_response": "ok"}})
        mock_approve.assert_called_once_with("Append to Google Doc", {"doc_id": "test_doc_123", "content": "hello world"})
        mock_append.assert_called_once()

    @patch('server.get_terminal_approval')
    def test_append_to_doc_rejected(self, mock_approve):
        mock_approve.return_value = False

        response = self.client.post("/append_to_doc", json={
            "doc_id": "test_doc_123",
            "content": "hello world"
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Action rejected by user")

    @patch('server.get_terminal_approval')
    @patch('server.get_credentials')
    @patch('server.create_email_draft')
    def test_create_email_draft_approved(self, mock_create_draft, mock_get_creds, mock_approve):
        mock_approve.return_value = True
        mock_get_creds.return_value = MagicMock()
        mock_create_draft.return_value = {"mock_response": "ok"}

        response = self.client.post("/create_email_draft", json={
            "to": "test@example.com",
            "subject": "Hello",
            "body": "Hi there"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "response": {"mock_response": "ok"}})
        mock_approve.assert_called_once_with("Create Gmail Draft", {"to": "test@example.com", "subject": "Hello", "body": "Hi there"})
        mock_create_draft.assert_called_once()

    @patch('server.get_terminal_approval')
    def test_create_email_draft_rejected(self, mock_approve):
        mock_approve.return_value = False

        response = self.client.post("/create_email_draft", json={
            "to": "test@example.com",
            "subject": "Hello",
            "body": "Hi there"
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Action rejected by user")

    @patch('server.get_credentials')
    @patch('server.append_to_doc')
    @patch.dict(os.environ, {"BYPASS_APPROVAL_KEY": "secret_key_123"})
    def test_append_to_doc_bypass_approved(self, mock_append, mock_get_creds):
        mock_get_creds.return_value = MagicMock()
        mock_append.return_value = {"mock_response": "ok"}

        response = self.client.post(
            "/append_to_doc",
            json={
                "doc_id": "test_doc_123",
                "content": "hello world"
            },
            headers={"X-Approval-Key": "secret_key_123"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "response": {"mock_response": "ok"}})
        mock_append.assert_called_once()

    @patch('server.get_credentials')
    @patch('server.create_email_draft')
    @patch.dict(os.environ, {"BYPASS_APPROVAL_KEY": "secret_key_123"})
    def test_create_email_draft_bypass_approved(self, mock_create_draft, mock_get_creds):
        mock_get_creds.return_value = MagicMock()
        mock_create_draft.return_value = {"mock_response": "ok"}

        response = self.client.post(
            "/create_email_draft",
            json={
                "to": "test@example.com",
                "subject": "Hello",
                "body": "Hi there"
            },
            headers={"X-Approval-Key": "secret_key_123"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "response": {"mock_response": "ok"}})
        mock_create_draft.assert_called_once()

if __name__ == '__main__':
    unittest.main()
