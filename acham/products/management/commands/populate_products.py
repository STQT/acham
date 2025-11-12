import io
import random
from decimal import Decimal
from typing import Iterable

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from acham.products.models import Collection, Product, ProductShot

DEFAULT_IMAGE_QUERIES = [
    "fashion portrait",
    "designer clothing",
    "luxury apparel",
    "handbag studio",
]

COLLECTION_NAMES = [
    "Ethereal Evening",
    "Urban Ritual",
    "Celestial Daywear",
    "Nomad Craft",
    "Modern Heritage",
]

MATERIALS = [
    "Organic Cotton",
    "Silk",
    "Cashmere",
    "Linen",
    "Recycled Wool",
    "Leather",
    "Bamboo Blend",
]

COLORS = [
    "Ivory",
    "Charcoal",
    "Amber",
    "Oat",
    "Midnight Blue",
    "sage",
    "Terracotta",
]

SHORT_DESCRIPTIONS = [
    "Tailored silhouette with contemporary detailing",
    "Hand-finished texture inspired by artisan craft",
    "Layer-friendly essential with architectural lines",
    "Statement piece with sculptural volume",
]

CARE_INSTRUCTIONS = [
    "Dry clean only. Steam at low temperature.",
    "Hand wash cold, reshape while damp, lay flat to dry.",
    "Machine wash delicate cycle, use mild detergent, air dry.",
]


class Command(BaseCommand):
    """Populate demo collections and products with Unsplash imagery."""

    help = "Populate collections/products with demo data and Unsplash images"

    def add_arguments(self, parser):
        parser.add_argument("--collections", type=int, default=3, help="Number of collections to ensure exist")
        parser.add_argument("--products", type=int, default=20, help="Number of products to create")
        parser.add_argument(
            "--query",
            action="append",
            default=None,
            help="Custom Unsplash query (use multiple --query flags to supply several).",
        )
        parser.add_argument(
            "--replace-images",
            action="store_true",
            help="Re-download images for products even if they already have shots.",
        )

    def handle(self, *args, **options):
        access_key = settings.UNSPLASH_ACCESS_KEY
        if not access_key:
            raise CommandError("UNSPLASH_ACCESS_KEY is not configured. Set it in your environment before running this command.")

        queries = options["query"] or DEFAULT_IMAGE_QUERIES
        num_collections = max(1, options["collections"])
        num_products = max(1, options["products"])
        replace_images = options["replace_images"]

        self.stdout.write(self.style.NOTICE("Creating collections"))
        collections = self.ensure_collections(num_collections)
        self.stdout.write(self.style.SUCCESS(f"Collections ready: {Collection.objects.count()}"))

        created = 0
        with transaction.atomic():
            for _ in range(num_products):
                product = self.create_product(random.choice(collections))
                self.fetch_and_attach_images(product, queries, access_key, force_replace=replace_images)
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} products with images."))

    def ensure_collections(self, amount: int) -> list[Collection]:
        collections = list(Collection.objects.all())
        idx = 0
        while len(collections) < amount:
            name = COLLECTION_NAMES[idx % len(COLLECTION_NAMES)]
            slug = f"collection-{Collection.objects.count() + 1}"
            collection = Collection.objects.create(
                name=name,
                slug=slug,
                **self.translation_kwargs({"name": name}),
            )
            collections.append(collection)
            idx += 1
        return collections

    def create_product(self, collection: Collection) -> Product:
        size = random.choice(Product.ProductSize.values)
        product_type = random.choice(Product.ProductType.values)
        price = Decimal(random.randrange(15000, 150000)) / 100
        name = f"{collection.name} #{random.randint(100, 999)}"
        material = random.choice(MATERIALS)
        color = random.choice(COLORS)
        short_description = random.choice(SHORT_DESCRIPTIONS)
        detailed_description = "\n".join(random.sample(SHORT_DESCRIPTIONS, k=2))
        care_instructions = random.choice(CARE_INSTRUCTIONS)

        product = Product.objects.create(
            collection=collection,
            name=name,
            size=size,
            material=material,
            type=product_type,
            color=color,
            short_description=short_description,
            detailed_description=detailed_description,
            care_instructions=care_instructions,
            price=price,
            is_available=random.choice([True, True, False]),
            **self.translation_kwargs(
                {
                    "name": name,
                    "material": material,
                    "color": color,
                    "short_description": short_description,
                    "detailed_description": detailed_description,
                    "care_instructions": care_instructions,
                }
            ),
        )
        return product

    def fetch_and_attach_images(
        self,
        product: Product,
        queries: Iterable[str],
        access_key: str,
        force_replace: bool = False,
        required_count: int = 3,
    ) -> None:
        if product.shots.exists() and not force_replace:
            return

        product.shots.all().delete()
        shots_to_create = max(required_count, 3)
        queries_list = list(queries)

        for idx in range(shots_to_create):
            query = random.choice(queries_list)
            data = self.request_unsplash_photo(query, access_key)

            image_url = data["urls"].get("full") or data["urls"].get("regular")
            if not image_url:
                continue

            alt_text = data.get("alt_description") or data.get("description") or product.name
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            file_content = self.ensure_jpeg(ContentFile(response.content))
            filename = f"unsplash-{data['id']}-{idx}.jpg"

            shot = ProductShot(
                product=product,
                alt_text=alt_text or product.name,
                is_primary=idx == 0,
                order=idx,
            )
            shot.image.save(filename, file_content, save=True)

    def ensure_jpeg(self, content: ContentFile) -> ContentFile:
        try:
            image = Image.open(io.BytesIO(content.read()))
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Unable to process image: {exc}") from exc

        if image.format and image.format.lower() == "jpeg":
            content.seek(0)
            return content

        converted = io.BytesIO()
        if image.mode in {"RGBA", "P"}:
            image = image.convert("RGB")
        image.save(converted, format="JPEG", quality=90)
        return ContentFile(converted.getvalue())

    def request_unsplash_photo(self, query: str, access_key: str) -> dict:
        endpoint = "https://api.unsplash.com/photos/random"
        headers = {"Authorization": f"Client-ID {access_key}"}
        params = {"query": query, "count": 1, "orientation": "portrait"}

        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            payload = payload[0]
        if not isinstance(payload, dict):
            raise CommandError("Unexpected response from Unsplash API")
        return payload

    def translation_kwargs(self, field_values: dict[str, str]) -> dict[str, str]:
        languages = getattr(settings, "MODELTRANSLATION_LANGUAGES", ("en",))
        translations: dict[str, str] = {}
        for field, value in field_values.items():
            for language in languages:
                translations[f"{field}_{language}"] = value
        return translations
