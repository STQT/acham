from __future__ import annotations

import logging
from io import BytesIO
from typing import Tuple

from django.core.files.base import ContentFile
from django.core.files.images import ImageFile

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore


logger = logging.getLogger(__name__)

MAX_SIZE_DEFAULT: Tuple[int, int] = (1600, 1600)


def _get_resample_filter():
    if Image is None:
        return None
    return getattr(Image, "Resampling", Image).LANCZOS


def optimize_image(
    image_field: ImageFile,
    *,
    max_size: Tuple[int, int] = MAX_SIZE_DEFAULT,
    quality: int = 75,
    force: bool = False,
) -> bool:
    """
    Optimize an image field in place.

    Returns True if the image was processed successfully, False if skipped or an error occurred.
    """
    if Image is None:
        logger.warning("Pillow is not installed; skipping image optimization.")
        return False

    if not image_field:
        return False

    if not force and not getattr(image_field, "_file", None):
        # No new file assigned; skip optimization.
        return False

    try:
        image_field.open("rb")
    except FileNotFoundError:
        return False

    try:
        image = Image.open(image_field)
    except Exception as exc:  # pragma: no cover - corrupt images
        logger.warning("Failed to open image %s for optimization: %s", image_field.name, exc)
        image_field.close()
        return False

    original_format = (image.format or "JPEG").upper()

    target_format = original_format if original_format in {"JPEG", "JPG", "PNG", "WEBP"} else "JPEG"

    if image.mode in {"P", "RGBA"} and target_format in {"JPEG", "JPG"}:
        image = image.convert("RGB")

    resample = _get_resample_filter()
    if resample and (image.width > max_size[0] or image.height > max_size[1]):
        image.thumbnail(max_size, resample=resample)

    buffer = BytesIO()
    save_kwargs = {"optimize": True}

    if target_format in {"JPEG", "JPG", "WEBP"}:
        save_kwargs["quality"] = quality

    try:
        image.save(buffer, format=target_format, **save_kwargs)
    except OSError:  # pragma: no cover - fallback when optimization unsupported
        buffer = BytesIO()
        image.save(buffer, format=target_format)

    image_field.save(image_field.name, ContentFile(buffer.getvalue()), save=False)
    image_field.close()

    return True

