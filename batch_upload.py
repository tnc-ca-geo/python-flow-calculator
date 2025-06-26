from pathlib import Path
import tempfile
import boto3
import py7zr
from botocore.exceptions import ClientError

BUCKET = "upstream-ffm"
ARCHIVE_DIR = Path("/home/nathan/Desktop/ffc_unimpaired_data")
EXTRACT_PATTERNS = ("*.7z",)

def upload_file(local_path: Path, bucket: str, key: str) -> None:
    s3 = boto3.client("s3")
    try:
        s3.upload_file(str(local_path), bucket, key)
        print(f"✔  {local_path.name} ➜ s3://{bucket}/{key}")
    except ClientError as exc:
        print(f"✖  Failed to upload {local_path.name}: {exc}")

def main():
    archives = [p for pattern in EXTRACT_PATTERNS for p in ARCHIVE_DIR.glob(pattern)]
    if not archives:
        print("No archives found.")
        return

    for archive in archives:
        print(f"Extracting {archive.name} ...")
        archive_stem = archive.stem

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            try:
                with py7zr.SevenZipFile(archive) as z:
                    z.extractall(path=tmp_path)
            except Exception as exc:
                print(f"⚠ Failed to extract {archive.name}: {exc}")
                continue

            for file in tmp_path.rglob("*"):
                if file.is_file():
                    # Replace "combined_" prefix if present
                    if file.name.startswith("combined_"):
                        new_filename = file.name.replace("combined_", f"{archive_stem}_", 1)
                    else:
                        new_filename = f"{archive_stem}_{file.name}"

                    upload_file(file, BUCKET, new_filename)

if __name__ == "__main__":
    main()
