from unittest.mock import patch
from django.test import SimpleTestCase
from . import views


class GeminiReplyTests(SimpleTestCase):
    @patch("properties.views.requests.post")
    def test_get_gemini_reply_uses_rest_api(self, mock_post):
        class DummyResponse:
            status_code = 200

            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "Xin chào"}]}}]}

            text = "{}"

        mock_post.return_value = DummyResponse()

        with patch.object(views, "GEMINI_API_KEY", "dummy-key"):
            reply = views.get_gemini_reply("hello")

        self.assertEqual(reply, "Xin chào")
        self.assertTrue(mock_post.called)
