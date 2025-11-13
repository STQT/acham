from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from acham.products.models import Collection, ProductShot
from acham.utils.image_processing import optimize_image, MAX_SIZE_DEFAULT


class Command(BaseCommand):
    help = "Optimize stored collection and product images for faster delivery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-size",
            type=int,
            default=MAX_SIZE_DEFAULT[0],
            help="Maximum width/height in pixels (default: %(default)s).",
        )
        parser.add_argument(
            "--quality",
            type=int,
            default=75,
            help="Quality parameter for JPEG/WEBP images (1-95, default: %(default)s).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of images processed per model (for testing).",
        )

    def handle(self, *args, **options):
        max_size = options["max_size"]
        quality = options["quality"]
        limit = options["limit"]
        max_size_tuple = (max_size, max_size)

        total_collections = self._optimize_collections(max_size_tuple, quality, limit)
        total_shots = self._optimize_product_shots(max_size_tuple, quality, limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Optimization complete. Collections: {total_collections}, product shots: {total_shots}."
            )
        )

    def _optimize_collections(self, max_size, quality, limit=None):
        processed = 0
        queryset = Collection.objects.exclude(image="").iterator()

        for collection in queryset:
            if limit is not None and processed >= limit:
                break

            if not collection.image:
                continue

            with transaction.atomic():
                changed = optimize_image(
                    collection.image,
                    max_size=max_size,
                    quality=quality,
                    force=True,
                )
                if changed:
                    collection.save(update_fields=["image"])
                    processed += 1

        return processed

    def _optimize_product_shots(self, max_size, quality, limit=None):
        processed = 0
        queryset = ProductShot.objects.exclude(image="").iterator()

        for shot in queryset:
            if limit is not None and processed >= limit:
                break

            if not shot.image:
                continue

            with transaction.atomic():
                changed = optimize_image(
                    shot.image,
                    max_size=max_size,
                    quality=quality,
                    force=True,
                )
                if changed:
                    shot.save(update_fields=["image"])
                    processed += 1

        return processed

