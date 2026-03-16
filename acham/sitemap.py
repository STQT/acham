from __future__ import annotations

from datetime import date
from typing import Iterable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from acham.products.models import Collection, Product


def _iter_language_codes() -> list[str]:
    codes: Iterable[str]
    codes = getattr(settings, "MODELTRANSLATION_LANGUAGES", None) or [c for c, _ in settings.LANGUAGES]
    return [str(c).lower() for c in codes]


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def sitemap_xml(request: HttpRequest) -> HttpResponse:
    """
    Minimal dynamic sitemap for Google Search Console.

    Frontend routes live on the main domain, so we emit absolute URLs pointing to:
    - https://acham.uz/{i18n}/products/{slug}
    - https://acham.uz/{i18n}/collections/{slug}
    """

    base = "https://acham.uz"
    lang_codes = _iter_language_codes()

    urls: list[tuple[str, date | None]] = []

    # Collections
    for c in Collection.objects.filter(is_active=True).only(
        "updated_at",
        "slug_ru",
        "slug_en",
        "slug_uz",
    ):
        for lang in lang_codes:
            slug = getattr(c, f"slug_{lang}", None)
            if slug:
                urls.append((f"{base}/{lang}/collections/{slug}", c.updated_at.date() if c.updated_at else None))

    # Products
    for p in Product.objects.filter(is_available=True).only(
        "updated_at",
        "slug_ru",
        "slug_en",
        "slug_uz",
    ):
        for lang in lang_codes:
            slug = getattr(p, f"slug_{lang}", None)
            if slug:
                urls.append((f"{base}/{lang}/products/{slug}", p.updated_at.date() if p.updated_at else None))

    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in urls:
        parts.append("<url>")
        parts.append(f"<loc>{_xml_escape(loc)}</loc>")
        if lastmod:
            parts.append(f"<lastmod>{lastmod.isoformat()}</lastmod>")
        parts.append("</url>")
    parts.append("</urlset>")

    xml = "\n".join(parts) + "\n"
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")

