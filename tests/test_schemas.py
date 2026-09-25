import unittest

from pydantic import ValidationError

from app.schemas import AskRequest, AskResponse


class SchemaTests(unittest.TestCase):
    def test_ask_request_requires_a_nontrivial_question(self):
        with self.assertRaises(ValidationError):
            AskRequest(question="hi")

        self.assertEqual(
            AskRequest(question="How does retrieval work?").question,
            "How does retrieval work?",
        )

    def test_ask_response_accepts_answer_and_citations(self):
        response = AskResponse(
            answer="The result is in the policy. [Source 1]",
            sources=[
                {
                    "document_name": "policy.txt",
                    "chunk_index": 0,
                    "content": "Policy excerpt",
                    "distance": 0.12,
                }
            ],
        )
        self.assertEqual(response.sources[0].document_name, "policy.txt")
        self.assertEqual(response.sources[0].distance, 0.12)


if __name__ == "__main__":
    unittest.main()
