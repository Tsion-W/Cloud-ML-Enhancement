from __future__ import annotations
from pathlib import Path

def _cfg_section(cfg: dict, key: str) -> dict:
    return (cfg or {}).get(key, {}) if isinstance(cfg, dict) else {}

def maybe_upload(cfg: dict, local_path: str | Path, what: str):
    """Upload to cloud if configured: cfg['cloud'] with type {aws|gcp|azure} and bucket/container."""
    cloud = _cfg_section(cfg, "cloud")
    if not cloud: 
        return
    provider = cloud.get("provider")
    if provider == "aws":
        _aws_upload(local_path, cloud, what)
    elif provider == "gcp":
        _gcp_upload(local_path, cloud, what)
    elif provider == "azure":
        _azure_upload(local_path, cloud, what)

def maybe_download(cfg: dict, what: str):
    cloud = _cfg_section(cfg, "cloud")
    if not cloud: 
        return
    provider = cloud.get("provider")
    if provider == "aws":
        _aws_download(cloud, what)
    elif provider == "gcp":
        _gcp_download(cloud, what)
    elif provider == "azure":
        _azure_download(cloud, what)

# ——— AWS S3 ———
def _aws_upload(local_path, cloud, what):
    try:
        import boto3
        s3 = boto3.client("s3")
        bucket = cloud["bucket"]
        key = f"{cloud.get('prefix','')}/{what}"
        lp = Path(local_path)
        if lp.is_dir():
            for p in lp.rglob("*"):
                if p.is_file():
                    s3.upload_file(str(p), bucket, f"{key}/{p.name}")
        else:
            s3.upload_file(str(lp), bucket, f"{key}/{lp.name}")
        print(f"[CLOUD] Uploaded to s3://{bucket}/{key}")
    except Exception as e:
        print(f"[CLOUD] AWS upload skipped: {e}")

def _aws_download(cloud, what):
    try:
        import boto3, botocore
        s3 = boto3.client("s3")
        bucket = cloud["bucket"]
        key = f"{cloud.get('prefix','')}/{what}"
        # Minimal stub: list and pull top-level files
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=key)
        for obj in resp.get("Contents", []):
            if obj["Key"].endswith("/"): 
                continue
            fname = Path(obj["Key"]).name
            out = Path(what) if "." in fname else Path(what)/fname
            out.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, obj["Key"], str(out))
        print(f"[CLOUD] Downloaded from s3://{bucket}/{key}")
    except Exception as e:
        print(f"[CLOUD] AWS download skipped: {e}")

# ——— GCP GCS ———
def _gcp_upload(local_path, cloud, what):
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(cloud["bucket"])
        prefix = f"{cloud.get('prefix','')}/{what}"
        lp = Path(local_path)
        if lp.is_dir():
            for p in lp.rglob("*"):
                if p.is_file():
                    blob = bucket.blob(f"{prefix}/{p.name}")
                    blob.upload_from_filename(str(p))
        else:
            blob = bucket.blob(f"{prefix}/{lp.name}")
            blob.upload_from_filename(str(lp))
        print(f"[CLOUD] Uploaded to gs://{cloud['bucket']}/{prefix}")
    except Exception as e:
        print(f"[CLOUD] GCP upload skipped: {e}")

def _gcp_download(cloud, what):
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(cloud["bucket"])
        prefix = f"{cloud.get('prefix','')}/{what}"
        for blob in client.list_blobs(bucket, prefix=prefix):
            if blob.name.endswith("/"): 
                continue
            fname = Path(blob.name).name
            out = Path(what) if "." in fname else Path(what)/fname
            out.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(out))
        print(f"[CLOUD] Downloaded from gs://{cloud['bucket']}/{prefix}")
    except Exception as e:
        print(f"[CLOUD] GCP download skipped: {e}")

# ——— Azure Blob ———
def _azure_upload(local_path, cloud, what):
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(cloud["connection_string"])
        container = svc.get_container_client(cloud["container"])
        prefix = f"{cloud.get('prefix','')}/{what}"
        lp = Path(local_path)
        if lp.is_dir():
            for p in lp.rglob("*"):
                if p.is_file():
                    container.upload_blob(name=f"{prefix}/{p.name}", data=p.read_bytes(), overwrite=True)
        else:
            container.upload_blob(name=f"{prefix}/{lp.name}", data=lp.read_bytes(), overwrite=True)
        print(f"[CLOUD] Uploaded to azure://{cloud['container']}/{prefix}")
    except Exception as e:
        print(f"[CLOUD] Azure upload skipped: {e}")

def _azure_download(cloud, what):
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(cloud["connection_string"])
        container = svc.get_container_client(cloud["container"])
        prefix = f"{cloud.get('prefix','')}/{what}"
        blobs = container.list_blobs(name_starts_with=prefix)
        for b in blobs:
            if b.name.endswith("/"): 
                continue
            fname = Path(b.name).name
            out = Path(what) if "." in fname else Path(what)/fname
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "wb") as f:
                dl = container.download_blob(b)
                f.write(dl.readall())
        print(f"[CLOUD] Downloaded from azure://{cloud['container']}/{prefix}")
    except Exception as e:
        print(f"[CLOUD] Azure download skipped: {e}")
