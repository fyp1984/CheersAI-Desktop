from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import BinaryIO

import requests


class FileBayClient:
    """Small FileBay/Gitea contents API client.

    Markdown is accepted by this helper as a plain Python string. Images and
    other binary files are accepted as streams, then encoded for the FileBay
    contents API request body.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        owner: str,
        repo: str,
        branch: str = "main",
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _contents_url(self, path: str) -> str:
        clean_path = path.strip("/")
        return f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}/contents/{clean_path}"

    def get_file_sha(self, path: str) -> str | None:
        response = requests.get(
            self._contents_url(path),
            headers=self.headers,
            params={"ref": self.branch},
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("sha")
        return None

    def write_base64(
        self,
        path: str,
        content_base64: str,
        message: str,
        sha: str | None = None,
    ) -> dict:
        current_sha = sha if sha is not None else self.get_file_sha(path)
        payload: dict[str, str] = {
            "message": message,
            "content": content_base64,
            "branch": self.branch,
        }
        if current_sha:
            payload["sha"] = current_sha

        method = requests.put if current_sha else requests.post
        response = method(
            self._contents_url(path),
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def write_markdown_string(
        self,
        path: str,
        markdown_text: str,
        message: str = "Write Markdown string",
    ) -> dict:
        content_base64 = base64.b64encode(markdown_text.encode("utf-8")).decode("ascii")
        return self.write_base64(path, content_base64, message)

    def write_image_stream(
        self,
        path: str,
        image_stream: BinaryIO,
        message: str = "Write image stream",
        chunk_size: int = 1024 * 1024,
    ) -> dict:
        encoded_parts: list[str] = []
        carry = b""

        while True:
            chunk = image_stream.read(chunk_size)
            if not chunk:
                break

            chunk = carry + chunk
            remainder = len(chunk) % 3
            if remainder:
                carry = chunk[-remainder:]
                chunk = chunk[:-remainder]
            else:
                carry = b""

            if chunk:
                encoded_parts.append(base64.b64encode(chunk).decode("ascii"))

        if carry:
            encoded_parts.append(base64.b64encode(carry).decode("ascii"))

        return self.write_base64(path, "".join(encoded_parts), message)

    def write_image_file(
        self,
        path: str,
        local_image_path: str | Path,
        message: str = "Write image file",
    ) -> dict:
        with Path(local_image_path).open("rb") as image_stream:
            return self.write_image_stream(path, image_stream, message)


def client_from_env() -> FileBayClient:
    return FileBayClient(
        base_url=os.environ["FILEBAY_URL"],
        token=os.environ["FILEBAY_TOKEN"],
        owner=os.environ["FILEBAY_OWNER"],
        repo=os.environ["FILEBAY_REPO"],
        branch=os.environ.get("FILEBAY_BRANCH", "main"),
    )


if __name__ == "__main__":
    client = client_from_env()

    markdown = """# FileBay Markdown example

This Markdown content is passed to the helper as a plain Python string.
"""
    client.write_markdown_string("examples/filebay-markdown-example.md", markdown)

    image_path = os.environ.get("FILEBAY_EXAMPLE_IMAGE")
    if image_path:
        client.write_image_file("examples/filebay-image-example.png", image_path)
