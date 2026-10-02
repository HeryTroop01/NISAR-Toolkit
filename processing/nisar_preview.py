# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_preview.py
# Module     : NISAR Product Preview
# Version    : 0.1.1
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides reusable utilities for downloading and decoding ASF browse
#     images associated with NISAR catalogue products.
#
#     This module is intentionally independent of the catalogue-search
#     Processing algorithm. It does not perform Earthdata authentication,
#     product downloads, HDF5 inspection, or QGIS raster loading.
#
# Data source:
#     Alaska Satellite Facility (ASF) / NASA Earthdata
#
# Status:
#     Development
# =============================================================================

from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from qgis.PyQt.QtGui import QPixmap


class NISARPreviewError(RuntimeError):
    """Raised when an ASF browse image cannot be retrieved or decoded."""


class NISARPreviewClient:
    """Retrieve and decode ASF browse images for NISAR products."""

    REQUEST_TIMEOUT = 30

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        """Initialize the preview client.

        Args:
            timeout: Maximum HTTP request time in seconds.
        """
        self.timeout = timeout

    @staticmethod
    def get_browse_urls(properties: Dict[str, Any]) -> List[str]:
        """Return valid browse-image URLs from an ASF product properties dict.

        The ASF ``browse`` property is expected to contain a list of URLs.
        Invalid or non-image entries are ignored.
        """

        browse = properties.get("browse", [])

        if not isinstance(browse, list):
            return []

        image_extensions = (
            ".png",
            ".jpg",
            ".jpeg",
        )

        return [
            url
            for url in browse
            if isinstance(url, str)
            and url.lower().endswith(image_extensions)
        ]

    @staticmethod
    def classify_browse_url(url: str) -> str:
        """Return a human-readable label for an ASF browse URL."""

        filename = url.rsplit("/", 1)[-1].lower()

        if "latlon_thumbnail" in filename:
            return "LATLON Thumbnail"

        if "latlon" in filename:
            return "LATLON"

        if "native_b_" in filename:
            polarization = filename.split("native_b_", 1)[1]
            polarization = polarization.rsplit(".", 1)[0].upper()
            return f"NATIVE {polarization}"

        if "native" in filename:
            return "NATIVE"

        return "Browse Image"

    @classmethod
    def get_browse_options(
        cls,
        properties: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Build browse-image options suitable for a preview GUI."""

        options = []

        for url in cls.get_browse_urls(properties):
            options.append(
                {
                    "label": cls.classify_browse_url(url),
                    "url": url,
                }
            )

        return options

    def download_image(self, url: str) -> bytes:
        """Download an ASF browse image and return its raw bytes.

        ASF browse endpoints may return ``application/octet-stream`` even when
        the payload itself is a valid PNG or JPEG. Therefore, validation is
        performed by Qt image decoding rather than by MIME type alone.
        """

        if not isinstance(url, str) or not url.strip():
            raise NISARPreviewError(
                "The browse image URL is empty or invalid."
            )

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NISARPreviewError(
                f"Could not retrieve browse image: {exc}"
            ) from exc

        if response.status_code != 200:
            raise NISARPreviewError(
                f"ASF browse request failed with HTTP "
                f"{response.status_code}."
            )

        if not response.content:
            raise NISARPreviewError(
                "ASF returned an empty browse image."
            )

        return response.content

    def load_pixmap(self, url: str) -> QPixmap:
        """Download a browse image and decode it into a QPixmap."""

        image_bytes = self.download_image(url)

        pixmap = QPixmap()

        if not pixmap.loadFromData(image_bytes):
            raise NISARPreviewError(
                "The ASF response was received, but Qt could not decode "
                "it as a supported image."
            )

        return pixmap

    def load_pixmap_from_properties(
        self,
        properties: Dict[str, Any],
        browse_index: int = 0,
    ) -> QPixmap:
        """Load a browse image selected from ASF product properties."""

        browse_urls = self.get_browse_urls(properties)

        if not browse_urls:
            raise NISARPreviewError(
                "No supported browse images were found for this product."
            )

        if browse_index < 0 or browse_index >= len(browse_urls):
            raise NISARPreviewError(
                f"Browse image index {browse_index} is out of range."
            )

        return self.load_pixmap(browse_urls[browse_index])
