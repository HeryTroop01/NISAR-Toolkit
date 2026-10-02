# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_download.py
# Module     : NISAR Product Download Engine
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides the core download functionality for NISAR products.
#
#     Features:
#         - Downloads NISAR HDF5 products from ASF.
#         - Streams data in chunks instead of loading the complete file
#           into memory.
#         - Reports download progress.
#         - Calculates download speed.
#         - Estimates remaining download time.
#         - Supports cancellation.
#         - Validates the downloaded file size.
#
#     This module contains no QGIS GUI code. The graphical download dialog
#     will use this engine in a later step.
# =============================================================================

import os
import time

import requests


class NISARDownloadError(RuntimeError):
    """Raised when a NISAR product download fails."""


class NISARDownloadCancelled(RuntimeError):
    """Raised when a NISAR product download is cancelled."""


class NISARDownloadClient:
    """Client for downloading NISAR products from ASF."""

    def __init__(
        self,
        chunk_size=1024 * 1024,
        timeout=60,
        session=None,
    ):
        """
        Initialize the download client.

        Parameters
        ----------
        chunk_size : int
            Number of bytes requested per download chunk.
        timeout : int
            HTTP request timeout in seconds.
        """
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.session = session
    @staticmethod
    def get_product_size(properties):
        """
        Extract the HDF5 product size from ASF product properties.

        Parameters
        ----------
        properties : dict
            ASF product properties.

        Returns
        -------
        int or None
            Product size in bytes.
        """
        if not isinstance(properties, dict):
            return None

        byte_metadata = properties.get("bytes", {})

        if not isinstance(byte_metadata, dict):
            return None

        for filename, metadata in byte_metadata.items():
            if filename.lower().endswith(".h5"):
                if isinstance(metadata, dict):
                    size_bytes = metadata.get("bytes")

                    if isinstance(size_bytes, (int, float)):
                        return int(size_bytes)

        return None

    @staticmethod
    def format_size(size_bytes):
        """
        Convert bytes into a human-readable binary size.

        Parameters
        ----------
        size_bytes : int or None
            Size in bytes.

        Returns
        -------
        str
            Human-readable size.
        """
        if size_bytes is None:
            return "Unknown"

        size = float(size_bytes)

        units = [
            "B",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
        ]

        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}"

            size /= 1024

        return "Unknown"

    @staticmethod
    def calculate_speed(downloaded_bytes, elapsed_seconds):
        """
        Calculate the current average download speed.

        Returns
        -------
        float
            Speed in bytes per second.
        """
        if elapsed_seconds <= 0:
            return 0.0

        return downloaded_bytes / elapsed_seconds

    @staticmethod
    def calculate_eta(
        downloaded_bytes,
        total_bytes,
        speed_bytes_per_second,
    ):
        """
        Calculate estimated remaining download time.

        Returns
        -------
        float or None
            Remaining time in seconds.
        """
        if (
            total_bytes is None
            or total_bytes <= 0
            or speed_bytes_per_second <= 0
        ):
            return None

        remaining_bytes = max(
            total_bytes - downloaded_bytes,
            0,
        )

        return remaining_bytes / speed_bytes_per_second

    @staticmethod
    def format_time(seconds):
        """
        Convert seconds into a human-readable duration.
        """
        if seconds is None:
            return "Unknown"

        seconds = max(int(seconds), 0)

        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"

        if minutes > 0:
            return f"{minutes}m {seconds}s"

        return f"{seconds}s"

    def download(
        self,
        url,
        output_path,
        expected_size=None,
        progress_callback=None,
        cancel_callback=None,
    ):
        """
        Download a NISAR product.

        Parameters
        ----------
        url : str
            ASF product URL.

        output_path : str
            Destination file path.

        expected_size : int or None
            Expected product size in bytes.

        progress_callback : callable or None
            Callback receiving:

                downloaded_bytes
                total_bytes
                percentage
                speed_bytes_per_second
                eta_seconds

        cancel_callback : callable or None
            Callback returning True when the download should be cancelled.

        Returns
        -------
        str
            Path to the downloaded file.

        Raises
        ------
        NISARDownloadError
            If the download fails.
        NISARDownloadCancelled
            If the download is cancelled.
        """

        if not url:
            raise NISARDownloadError(
                "No product URL was provided."
            )

        if not output_path:
            raise NISARDownloadError(
                "No output path was provided."
            )

        output_directory = os.path.dirname(
            os.path.abspath(output_path)
        )

        os.makedirs(
            output_directory,
            exist_ok=True,
        )

        temporary_path = output_path + ".part"

        downloaded_bytes = 0
        start_time = time.monotonic()

        try:
            request_session = self.session or requests

            with request_session.get(
                url,
                stream=True,
                timeout=self.timeout,
            ) as response:

                response.raise_for_status()

                content_length = response.headers.get(
                    "Content-Length"
                )

                total_bytes = expected_size

                if total_bytes is None and content_length:
                    try:
                        total_bytes = int(content_length)
                    except ValueError:
                        total_bytes = None

                with open(
                    temporary_path,
                    "wb",
                ) as output_file:

                    for chunk in response.iter_content(
                        chunk_size=self.chunk_size
                    ):

                        if cancel_callback is not None:
                            if cancel_callback():
                                raise NISARDownloadCancelled(
                                    "Download cancelled by user."
                                )

                        if not chunk:
                            continue

                        output_file.write(chunk)

                        downloaded_bytes += len(chunk)

                        elapsed_seconds = (
                            time.monotonic()
                            - start_time
                        )

                        speed = self.calculate_speed(
                            downloaded_bytes,
                            elapsed_seconds,
                        )

                        eta = self.calculate_eta(
                            downloaded_bytes,
                            total_bytes,
                            speed,
                        )

                        percentage = None

                        if total_bytes:
                            percentage = (
                                downloaded_bytes
                                / total_bytes
                            ) * 100.0

                            percentage = min(
                                max(percentage, 0.0),
                                100.0,
                            )

                        if progress_callback is not None:
                            progress_callback(
                                downloaded_bytes,
                                total_bytes,
                                percentage,
                                speed,
                                eta,
                            )

            if expected_size is not None:
                actual_size = os.path.getsize(
                    temporary_path
                )

                if actual_size != expected_size:
                    raise NISARDownloadError(
                        "Downloaded file size does not match "
                        "the ASF metadata.\n\n"
                        f"Expected: "
                        f"{self.format_size(expected_size)}\n"
                        f"Received: "
                        f"{self.format_size(actual_size)}"
                    )

            os.replace(
                temporary_path,
                output_path,
            )

            if progress_callback is not None:
                progress_callback(
                    downloaded_bytes,
                    total_bytes,
                    100.0,
                    self.calculate_speed(
                        downloaded_bytes,
                        time.monotonic()
                        - start_time,
                    ),
                    0.0,
                )

            return output_path

        except NISARDownloadCancelled:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

            raise

        except requests.RequestException as exc:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

            raise NISARDownloadError(
                f"HTTP download failed:\n\n{exc}"
            ) from exc

        except OSError as exc:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

            raise NISARDownloadError(
                f"Could not write the downloaded file:\n\n{exc}"
            ) from exc

        except Exception:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

            raise