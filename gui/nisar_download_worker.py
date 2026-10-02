# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_download_worker.py
# Module     : NISAR Download Worker
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Runs NISAR product downloads in a background QGIS/Qt thread.
#
#     The worker keeps the GUI responsive while a NISAR HDF5 product is being
#     downloaded and emits progress, completion, cancellation, and error
#     signals to the download dialog.
# =============================================================================

from qgis.PyQt.QtCore import QObject, pyqtSignal

import importlib.util
from pathlib import Path


def _load_download_client():
    """Load the NISAR download engine from the plugin processing directory."""

    module_path = (
        Path(__file__).resolve().parent.parent
        / "processing"
        / "nisar_download.py"
    )

    spec = importlib.util.spec_from_file_location(
        "nisar_download",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            "Could not locate the NISAR download engine."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return (
        module.NISARDownloadCancelled,
        module.NISARDownloadClient,
    )


NISARDownloadCancelled, NISARDownloadClient = (
    _load_download_client()
)


class NISARDownloadWorker(QObject):
    """Background worker for downloading a NISAR product."""

    progress = pyqtSignal(
        int,
        int,
        float,
        float,
        object,
    )

    finished = pyqtSignal(str)

    cancelled = pyqtSignal()

    error = pyqtSignal(str)

    def __init__(
        self,
        url,
        output_path,
        expected_size=None,
        session=None,
        parent=None,
    ):
        """
        Initialize the download worker.

        Parameters
        ----------
        url : str
            ASF product URL.

        output_path : str
            Destination file path.

        expected_size : int or None
            Expected product size in bytes.

        session : requests.Session or None
            Optional authenticated ASF session.

        parent : QObject or None
            Parent Qt object.
        """
        super().__init__(parent)

        self.url = url
        self.output_path = output_path
        self.expected_size = expected_size
        self.session = session

        self._cancel_requested = False

    def request_cancel(self):
        """Request cancellation of the active download."""

        self._cancel_requested = True

    def _is_cancelled(self):
        """Return whether cancellation has been requested."""

        return self._cancel_requested

    def _handle_progress(
        self,
        downloaded,
        total,
        percentage,
        speed,
        eta,
    ):
        """Forward download progress to the Qt interface."""

        if percentage is None:
            percentage_value = 0
        else:
            percentage_value = int(
                round(percentage)
            )

        self.progress.emit(
            percentage_value,
            downloaded,
            speed,
            eta,
            total,
        )

    def run(self):
        """Execute the download."""

        try:
            client = NISARDownloadClient(
                session=self.session
            )

            output = client.download(
                url=self.url,
                output_path=self.output_path,
                expected_size=self.expected_size,
                progress_callback=self._handle_progress,
                cancel_callback=self._is_cancelled,
            )

            self.finished.emit(output)

        except NISARDownloadCancelled:
            self.cancelled.emit()

        except Exception as exc:
            self.error.emit(str(exc))