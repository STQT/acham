import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    help = "Upload all local MEDIA_ROOT files to Cloudflare R2 (via default storage)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List files that would be uploaded, without uploading.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite files in R2 if they already exist.",
        )

    def handle(self, *args, **options):  # noqa: ARG002
        if not getattr(settings, "R2_ENABLED", False):
            raise CommandError("R2 is not enabled. Set R2_ENABLED=true and configure R2_* env vars.")

        try:
            import storages  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            raise CommandError("django-storages is required. Install django-storages and boto3.") from exc

        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            raise CommandError(f"MEDIA_ROOT does not exist: {media_root}")

        local_fs = FileSystemStorage(location=str(media_root))
        dry_run: bool = bool(options["dry_run"])
        overwrite: bool = bool(options["overwrite"])

        uploaded = 0
        skipped = 0
        errors = 0

        for root, _, files in os.walk(media_root):
            for filename in files:
                local_path = Path(root) / filename
                rel_path = local_path.relative_to(media_root).as_posix()

                try:
                    if default_storage.exists(rel_path) and not overwrite:
                        skipped += 1
                        continue

                    if dry_run:
                        self.stdout.write(rel_path)
                        continue

                    with local_fs.open(rel_path, "rb") as f:
                        default_storage.save(rel_path, File(f))

                    uploaded += 1
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    self.stderr.write(f"ERROR uploading {rel_path}: {exc}")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run complete."))
            return

        if errors:
            raise CommandError(f"Upload finished with errors. Uploaded={uploaded} Skipped={skipped} Errors={errors}")

        self.stdout.write(self.style.SUCCESS(f"Upload complete. Uploaded={uploaded} Skipped={skipped}"))
