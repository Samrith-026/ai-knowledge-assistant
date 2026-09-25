import unittest

from app.cache import build_cache_key


class CacheKeyTests(unittest.TestCase):
    def test_key_normalizes_case_and_surrounding_whitespace(self):
        self.assertEqual(
            build_cache_key("  How does retrieval work?  "),
            build_cache_key("how does retrieval work?"),
        )

    def test_key_does_not_include_the_question_text(self):
        key = build_cache_key("private question text")
        self.assertTrue(key.startswith("rag:answer:"))
        self.assertNotIn("private question text", key)


if __name__ == "__main__":
    unittest.main()
