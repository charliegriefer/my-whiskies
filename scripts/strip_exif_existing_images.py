"""
One-off script to strip EXIF data from all existing bottle images in S3.

Downloads each image, re-saves through Pillow (which drops EXIF via convert("RGB")),
and re-uploads in place. Processes both the display bucket and the full-res pro bucket.

Run on the EC2 instance (prod environment):
    source .venv/bin/activate
    CONFIG=prod python scripts/strip_exif_existing_images.py

Dry-run mode (lists keys, no uploads):
    CONFIG=prod python scripts/strip_exif_existing_images.py --dry-run
"""

import argparse
import io

import boto3
from PIL import Image, ImageOps

BUCKET = "my-whiskies-pics"
DISPLAY_KEY = "prod"
FULL_KEY = "prod-pro-full"
JPEG_QUALITY = 85
FULL_JPEG_QUALITY = 95


def strip_exif(data: bytes, quality: int, progressive: bool = False) -> bytes:
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    else:
        img = img.convert("RGB")
    out = io.BytesIO()
    kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
    if progressive:
        kwargs["progressive"] = True
    img.save(out, **kwargs)
    return out.getvalue()


def process_prefix(s3, prefix: str, quality: int, progressive: bool, dry_run: bool) -> tuple[int, int]:
    paginator = s3.get_paginator("list_objects_v2")
    processed = 0
    skipped = 0

    for page in paginator.paginate(Bucket=BUCKET, Prefix=f"{prefix}/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".jpg"):
                skipped += 1
                continue
            if dry_run:
                print(f"  [dry-run] {key}")
                processed += 1
                continue
            response = s3.get_object(Bucket=BUCKET, Key=key)
            original = response["Body"].read()
            stripped = strip_exif(original, quality=quality, progressive=progressive)
            s3.put_object(
                Body=stripped,
                Bucket=BUCKET,
                Key=key,
                ContentType="image/jpeg",
                CacheControl="public, max-age=31536000",
            )
            saved = len(original) - len(stripped)
            print(f"  {key}  ({len(original):,} → {len(stripped):,} bytes, saved {saved:,})")
            processed += 1

    return processed, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="List keys without re-uploading")
    args = parser.parse_args()

    s3 = boto3.client("s3")

    print(f"\nDisplay images ({DISPLAY_KEY}/):")
    d_proc, d_skip = process_prefix(s3, DISPLAY_KEY, JPEG_QUALITY, progressive=True, dry_run=args.dry_run)

    print(f"\nFull-res images ({FULL_KEY}/):")
    f_proc, f_skip = process_prefix(s3, FULL_KEY, FULL_JPEG_QUALITY, progressive=False, dry_run=args.dry_run)

    print(f"\nDone. Processed {d_proc + f_proc} images, skipped {d_skip + f_skip} non-JPEG files.")
    if args.dry_run:
        print("(dry-run — no files were modified)")


if __name__ == "__main__":
    main()
