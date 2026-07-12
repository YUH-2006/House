import os
import tempfile
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

import train_bot
from . import views
from .models import Property


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


class ImportPropertiesCommandTests(TestCase):
    def test_import_properties_from_csv(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", suffix=".csv", delete=False) as handle:
            handle.write("title,address,price,area,description\nNhà đẹp,123 Nguyễn Văn Cừ,2500000000,80,Nhà mới xây\n")
            csv_path = handle.name

        try:
            out = StringIO()
            call_command("import_properties", csv_path, "--limit", "1", stdout=out)

            self.assertEqual(Property.objects.count(), 1)
            property_obj = Property.objects.get()
            self.assertEqual(property_obj.tieu_de, "Nhà đẹp")
            self.assertEqual(property_obj.gia, Decimal("2500000000"))
            self.assertEqual(property_obj.dien_tich, 80.0)
            self.assertIn("Nhà mới xây", property_obj.mo_ta)
            self.assertTrue(property_obj.hinh_anh.name)
        finally:
            os.remove(csv_path)


class TrainBotHelpersTests(SimpleTestCase):
    def test_parse_external_listing_csv(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", suffix=".csv", delete=False) as handle:
            handle.write("title,price,url\nBán nhà 80m2 3 PN 2 tỷ,2000000000,https://example.com\n")
            csv_path = handle.name

        try:
            df = train_bot.load_external_listing_csv(csv_path, source_name="nhatot_data.csv")
            self.assertEqual(len(df), 1)
            self.assertAlmostEqual(df.iloc[0]["dien_tich"], 80.0)
            self.assertEqual(df.iloc[0]["so_phong_ngu"], 3)
            self.assertAlmostEqual(df.iloc[0]["gia_ban"], 2000.0)
        finally:
            os.remove(csv_path)
