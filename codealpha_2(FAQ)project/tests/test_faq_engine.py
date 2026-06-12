import unittest
from pathlib import Path

from faq_engine import FAQMatcher


class FAQMatcherTests(unittest.TestCase):
    def setUp(self):
        data_path = Path(__file__).resolve().parents[1] / "data" / "faqs.json"
        self.matcher = FAQMatcher.from_json(data_path)

    def test_tracks_order_question(self):
        result = self.matcher.answer("Where is my shipment?")
        self.assertIn("tracking", result["answer"].lower())

    def test_returns_question(self):
        result = self.matcher.answer("What is your return policy?")
        self.assertIn("30 days", result["answer"])

    def test_payment_question(self):
        result = self.matcher.answer("Why did my payment fail?")
        self.assertIn("network issues", result["answer"])

    def test_empty_question(self):
        result = self.matcher.answer("")
        self.assertEqual(result["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
