import os
import sys
import json
import base64
from pathlib import Path
import httpx

REPO_OWNER = "Siva-7418"
REPO_NAME = "raaleproject"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {".venv", ".pytest_cache", "__pycache__", ".git", "data"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "app.db"}

def get_headers():
    return {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Uploader"
    }

def get_all_files(root_dir):
    file_paths = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for f in filenames:
            if f in EXCLUDE_FILES or f.endswith(".pyc") or f.endswith(".db"):
                continue
            full_path = Path(dirpath) / f
            rel_path = full_path.relative_to(root_dir).as_posix()
            file_paths.append((rel_path, full_path))
    return file_paths

def upload_file_via_contents_api(client, rel_path, full_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{rel_path}"
    headers = get_headers()

    with open(full_path, "rb") as f:
        content_bytes = f.read()

    b64_content = base64.b64encode(content_bytes).decode("ascii")

    sha = None
    res_get = client.get(url, headers=headers)
    if res_get.status_code == 200:
        sha = res_get.json().get("sha")

    payload = {
        "message": f"Upload {rel_path}",
        "content": b64_content
    }
    if sha:
        payload["sha"] = sha

    res_put = client.put(url, headers=headers, json=payload)
    if res_put.status_code in [200, 201]:
        return True, "Success"
    else:
        return False, f"HTTP {res_put.status_code}: {res_put.text}"

def upload_project():
    if not TOKEN:
        print("Please set GITHUB_TOKEN environment variable.")
        sys.exit(1)

    print(f"Uploading {PROJECT_ROOT} to GitHub repository: {REPO_OWNER}/{REPO_NAME}...")
    client = httpx.Client(timeout=30.0)

    files = get_all_files(PROJECT_ROOT)
    print(f"Found {len(files)} files to upload.")

    success_count = 0
    fail_count = 0

    for rel_path, full_path in files:
        print(f" -> Uploading: {rel_path} ...", end="", flush=True)
        ok, msg = upload_file_via_contents_api(client, rel_path, full_path)
        if ok:
            print(" [OK]")
            success_count += 1
        else:
            print(f" [FAILED] ({msg})")
            fail_count += 1

    print("\n==================================================================")
    if fail_count == 0:
        print(f"SUCCESS! All {success_count} files uploaded to:")
        print(f"   https://github.com/{REPO_OWNER}/{REPO_NAME}")
    else:
        print(f"Uploaded {success_count} files, {fail_count} failed.")
    print("==================================================================")

if __name__ == "__main__":
    upload_project()
