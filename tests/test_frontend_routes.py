import os
import unittest
from unittest.mock import Mock, patch

# These route tests import the app without calling any external AI services.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("OPENAI_API_KEY", "ci-placeholder-not-a-real-key")
os.environ.setdefault("OPENAI_MODEL", "ci-test-model")

from fastapi.responses import FileResponse
from app.main import list_documents, root


class FrontendAndLibraryRouteTests(unittest.TestCase):
    def test_home_route_serves_the_frontend(self):
        response = root()
        self.assertIsInstance(response, FileResponse)
        self.assertTrue(str(response.path).endswith("frontend/index.html"))

    def test_document_list_returns_names_and_chunk_counts(self):
        session = Mock()
        query = session.query.return_value
        query.group_by.return_value = query
        query.order_by.return_value = query
        query.all.return_value = [("guide.txt", 3), ("reference.pdf", 2)]

        with patch("app.main.SessionLocal", return_value=session):
            response = list_documents()

        self.assertEqual(
            response,
            {
                "documents": [
                    {"filename": "guide.txt", "chunks": 3},
                    {"filename": "reference.pdf", "chunks": 2},
                ]
            },
        )
        session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()