import csv
import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from properties.models import Property


class Command(BaseCommand):
    help = "Import properties from a CSV file into the Django database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", nargs="?", default="")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        if not csv_file:
            raise CommandError("Please provide a CSV file path")

        if not os.path.exists(csv_file):
            raise CommandError(f"CSV file not found: {csv_file}")

        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(username="importer", password="123456")

        with open(csv_file, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            imported = 0

            for row in reader:
                if options["limit"] and imported >= options["limit"]:
                    break

                title = (row.get("title") or row.get("tieu_de") or "").strip()
                address = (row.get("address") or row.get("dia_chi") or "").strip()
                price_raw = (row.get("price") or row.get("gia") or "0").strip()
                area_raw = (row.get("area") or row.get("dien_tich") or "0").strip()
                description = (row.get("description") or row.get("mo_ta") or "").strip()

                if not title:
                    continue

                try:
                    price = Decimal(str(price_raw).replace(".", "").replace(",", ""))
                except Exception:
                    price = Decimal("0")

                try:
                    area = float(area_raw)
                except Exception:
                    area = 0.0

                image_name = "properties/default.jpg"
                if not default_storage.exists(image_name):
                    placeholder = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
                    default_storage.save(image_name, ContentFile(placeholder))

                Property.objects.get_or_create(
                    tieu_de=title,
                    defaults={
                        "loai_nha": "NP",
                        "dia_chi": address or "Địa chỉ chưa cập nhật",
                        "gia": price,
                        "dien_tich": area,
                        "mo_ta": description or "Không có mô tả",
                        "hinh_anh": image_name,
                        "nguoi_dang": user,
                    },
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {imported} properties from {csv_file}"))
