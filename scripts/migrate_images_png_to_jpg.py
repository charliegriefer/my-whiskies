import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import io
import sys

import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageOps

DISPLAY_MAX = 1600
JPEG_QUALITY = 85
CACHE_CONTROL = "public, max-age=31536000"


def s3_exists(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def make_resized_jpg(png_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(png_bytes))
    img = ImageOps.exif_transpose(img)

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((DISPLAY_MAX, DISPLAY_MAX), resample=Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out.getvalue()


def main(*, dry_run: bool, delete_png: bool) -> int:
    # Import app/db/models inside so this script runs in your app env
    from mywhiskies.app import create_app
    from mywhiskies.extensions import db
    from mywhiskies.models.bottle import BottleImage
    from mywhiskies.services.bottle.image import get_s3_config

    app = create_app()
    s3 = boto3.client("s3")

    converted = 0
    skipped = 0
    missing_png = 0
    deleted = 0
    errors = 0

    with app.app_context():
        bucket, key_prefix, _ = get_s3_config()

        q = db.session.query(BottleImage).order_by(
            BottleImage.bottle_id, BottleImage.sequence
        )

        for bi in q.yield_per(200):
            bottle_id = bi.bottle_id
            seq = bi.sequence

            png_key = f"{key_prefix}/{bottle_id}_{seq}.png"
            jpg_key = f"{key_prefix}/{bottle_id}_{seq}.jpg"

            if s3_exists(s3, bucket, jpg_key):
                skipped += 1
                continue

            if not s3_exists(s3, bucket, png_key):
                missing_png += 1
                print(f"[MISSING PNG] s3://{bucket}/{png_key}")
                continue

            try:
                obj = s3.get_object(Bucket=bucket, Key=png_key)
                png_bytes = obj["Body"].read()

                jpg_bytes = make_resized_jpg(png_bytes)

                if dry_run:
                    print(
                        f"[DRY RUN] Would write s3://{bucket}/{jpg_key} ({len(jpg_bytes)} bytes)"
                    )
                else:
                    s3.put_object(
                        Bucket=bucket,
                        Key=jpg_key,
                        Body=jpg_bytes,
                        ContentType="image/jpeg",
                        CacheControl=CACHE_CONTROL,
                    )
                    converted += 1
                    print(f"[OK] Wrote s3://{bucket}/{jpg_key}")

                    if delete_png:
                        s3.delete_object(Bucket=bucket, Key=png_key)
                        deleted += 1
                        print(f"[OK] Deleted s3://{bucket}/{png_key}")

            except Exception as e:
                errors += 1
                print(f"[ERROR] bottle_id={bottle_id} seq={seq}: {e}", file=sys.stderr)

    print("\n--- Summary ---")
    print(f"converted:   {converted}")
    print(f"skipped:     {skipped} (jpg already exists)")
    print(f"missing_png: {missing_png}")
    print(f"deleted_png: {deleted}")
    print(f"errors:      {errors}")

    return 0 if errors == 0 else 2


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    delete_png = "--delete-png" in sys.argv

    if delete_png and dry_run:
        print(
            "Refusing to --delete-png during dry run. Use: --apply --delete-png",
            file=sys.stderr,
        )
        raise SystemExit(2)

    raise SystemExit(main(dry_run=dry_run, delete_png=delete_png))
