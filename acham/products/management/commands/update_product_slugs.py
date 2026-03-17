from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction
from slugify import slugify

from acham.products.models import Product


@dataclass(frozen=True)
class _SlugSpec:
    slug_field: str
    source_fields: tuple[str, ...]


SPECS: tuple[_SlugSpec, ...] = (
    _SlugSpec("slug_en", ("name", "color")),
    _SlugSpec("slug_ru", ("name_ru", "color_ru")),
    _SlugSpec("slug_uz", ("name_uz", "color_uz")),
)


class Command(BaseCommand):
    help = "Rebuild multilingual product slugs from translated name+color fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print how many slugs would change without saving.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recompute and overwrite existing slug values (default: only fill missing/blank).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of products processed (for testing).",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]
        limit: int | None = options["limit"]

        existing = self._load_existing_slugs()

        processed = 0
        changed_products = 0
        changed_fields_total = 0

        qs = Product.objects.all().order_by("id")
        if limit is not None:
            qs = qs[: max(0, limit)]

        for product in qs.iterator():
            processed += 1
            update_fields: list[str] = []

            for spec in SPECS:
                current = getattr(product, spec.slug_field, None) or ""
                if (not force) and current.strip():
                    # Keep existing non-empty slug unless explicitly forced.
                    existing[spec.slug_field].add(current)
                    continue

                candidate_base = self._build_base(product, spec.source_fields)
                candidate = self._make_unique(
                    base=candidate_base,
                    used=existing[spec.slug_field],
                    max_length=Product._meta.get_field(spec.slug_field).max_length or 200,
                )

                if candidate != current:
                    setattr(product, spec.slug_field, candidate)
                    update_fields.append(spec.slug_field)

            if update_fields:
                changed_products += 1
                changed_fields_total += len(update_fields)
                if not dry_run:
                    with transaction.atomic():
                        product.save(update_fields=update_fields)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: processed={processed}, products_to_change={changed_products}, fields_to_change={changed_fields_total}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: processed={processed}, updated_products={changed_products}, updated_fields={changed_fields_total}"
            )
        )

    def _load_existing_slugs(self) -> dict[str, set[str]]:
        existing: dict[str, set[str]] = {spec.slug_field: set() for spec in SPECS}

        values = Product.objects.values_list(*(spec.slug_field for spec in SPECS))
        for row in values.iterator():
            for idx, spec in enumerate(SPECS):
                value = row[idx]
                if value:
                    existing[spec.slug_field].add(value)

        return existing

    def _build_base(self, product: Product, source_fields: tuple[str, ...]) -> str:
        parts: list[str] = []
        for field_name in source_fields:
            value = getattr(product, field_name, None)
            if value is None:
                continue
            value_str = str(value).strip()
            if value_str:
                parts.append(value_str)

        joined = " ".join(parts).strip()
        if not joined:
            # Fallback that is stable and always unique after suffixing logic.
            joined = f"product-{product.pk}"

        # python-slugify transliterates Cyrillic -> Latin by default, which is usually
        # preferable for URLs and avoids empty slugs.
        return slugify(joined)

    def _make_unique(self, base: str, used: set[str], max_length: int) -> str:
        base = (base or "").strip("-").strip()
        if not base:
            base = "product"

        def clamp(value: str) -> str:
            return value[:max_length] if len(value) > max_length else value

        candidate = clamp(base)
        if candidate and candidate not in used:
            used.add(candidate)
            return candidate

        # If collision, append "-2", "-3", ... ensuring max_length.
        n = 2
        while True:
            suffix = f"-{n}"
            trimmed_base = base
            if len(trimmed_base) + len(suffix) > max_length:
                trimmed_base = trimmed_base[: max(1, max_length - len(suffix))]
                trimmed_base = trimmed_base.rstrip("-")
            candidate = f"{trimmed_base}{suffix}"
            candidate = clamp(candidate)
            if candidate not in used:
                used.add(candidate)
                return candidate
            n += 1

