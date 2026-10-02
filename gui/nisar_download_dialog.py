# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_download_dialog.py
# Module     : NISAR Product Download Dialog
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides the graphical interface for downloading NISAR products.
#
#     Current features:
#         - Displays selected product metadata.
#         - Displays the NISAR product size before download.
#         - Provides Full Product and AOI / Region Subset options.
#         - Provides output-folder selection.
#
#     Download execution and live progress will be connected in later steps.
# =============================================================================

import os

from qgis.PyQt.QtCore import Qt, QThread
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

# -----------------------------------------------------------------------------
# NISAR Download Worker
# -----------------------------------------------------------------------------

import importlib.util
from pathlib import Path


def _load_download_worker():
    """Load the NISAR download worker from the GUI directory."""

    module_path = (
        Path(__file__).resolve().parent
        / "nisar_download_worker.py"
    )

    spec = importlib.util.spec_from_file_location(
        "nisar_download_worker",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            "Could not locate the NISAR download worker."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.NISARDownloadWorker


NISARDownloadWorker = _load_download_worker()

class NISARDownloadDialog(QDialog):
    """Graphical interface for downloading a NISAR product."""

    def __init__(
        self,
        properties,
        session=None,
        parent=None,
    ):
        """
        Initialize the NISAR download dialog.

        Parameters
        ----------
        properties : dict
            ASF product properties.
        parent : QWidget or None
            Parent Qt widget.
        """
        super().__init__(parent)

        self.properties = properties or {}
        self.session = session
        self.download_thread = None
        self.download_worker = None
        self._cancel_requested = False

        self.setWindowTitle("NISAR Product Download")
        self.resize(850, 650)

        self._create_interface()
        self._populate_product_information()
        self._update_download_mode()

    def _create_interface(self):
        """Create the download dialog interface."""

        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------------------
        # Product information
        # ---------------------------------------------------------------------

        product_group = QGroupBox("Product Information")
        product_layout = QFormLayout(product_group)

        self.product_id_label = QLabel()
        self.product_id_label.setWordWrap(True)

        self.file_name_label = QLabel()
        self.file_name_label.setWordWrap(True)

        self.processing_level_label = QLabel()
        self.polarization_label = QLabel()
        self.acquisition_label = QLabel()
        self.dataset_size_label = QLabel()

        product_layout.addRow(
            "Product ID:",
            self.product_id_label,
        )

        product_layout.addRow(
            "File Name:",
            self.file_name_label,
        )

        product_layout.addRow(
            "Processing Level:",
            self.processing_level_label,
        )

        product_layout.addRow(
            "Polarization:",
            self.polarization_label,
        )

        product_layout.addRow(
            "Acquisition:",
            self.acquisition_label,
        )

        product_layout.addRow(
            "Dataset Size:",
            self.dataset_size_label,
        )

        main_layout.addWidget(product_group)

        # ---------------------------------------------------------------------
        # Download mode
        # ---------------------------------------------------------------------

        mode_group = QGroupBox("Download Option")
        mode_layout = QVBoxLayout(mode_group)

        self.full_product_radio = QRadioButton(
            "Full Product"
        )

        self.full_product_radio.setToolTip(
            "Download the complete NISAR HDF5 product."
        )

        self.aoi_radio = QRadioButton(
            "AOI / Region Subset"
        )

        self.aoi_radio.setToolTip(
            "Use a QGIS region or AOI for spatial processing."
        )

        self.full_product_radio.setChecked(True)

        self.mode_group = QButtonGroup(self)

        self.mode_group.addButton(
            self.full_product_radio
        )

        self.mode_group.addButton(
            self.aoi_radio
        )

        mode_layout.addWidget(
            self.full_product_radio
        )

        mode_layout.addWidget(
            self.aoi_radio
        )

        main_layout.addWidget(mode_group)

        self.full_product_radio.toggled.connect(
            self._update_download_mode
        )

        # ---------------------------------------------------------------------
        # AOI selection
        # ---------------------------------------------------------------------

        aoi_layout = QFormLayout()

        self.aoi_layer_combo = QComboBox()
        self.aoi_layer_combo.setEnabled(False)

        self.aoi_layer_combo.addItem(
            "Select QGIS AOI layer..."
        )

        aoi_layout.addRow(
            "AOI Layer:",
            self.aoi_layer_combo,
        )

        main_layout.addLayout(aoi_layout)

        # ---------------------------------------------------------------------
        # Output folder
        # ---------------------------------------------------------------------

        output_layout = QHBoxLayout()

        self.output_folder_label = QLabel(
            os.path.expanduser("~/Downloads")
        )

        self.output_folder_label.setWordWrap(True)

        browse_button = QPushButton("Browse...")

        browse_button.clicked.connect(
            self._select_output_folder
        )

        output_layout.addWidget(
            self.output_folder_label,
            1,
        )

        output_layout.addWidget(
            browse_button
        )

        main_layout.addWidget(
            QLabel("Output Folder:")
        )

        main_layout.addLayout(
            output_layout
        )

        # ---------------------------------------------------------------------
        # Progress area
        # ---------------------------------------------------------------------

        progress_group = QGroupBox(
            "Download Progress"
        )

        progress_layout = QFormLayout(
            progress_group
        )

        self.status_label = QLabel(
            "Ready to download."
        )

        self.downloaded_label = QLabel(
            "Downloaded: 0 B"
        )

        self.speed_label = QLabel(
            "Speed: —"
        )

        self.eta_label = QLabel(
            "Estimated time remaining: —"
        )

        self.progress_label = QLabel(
            "Progress: 0%"
        )

        progress_layout.addRow(
            "Status:",
            self.status_label,
        )

        progress_layout.addRow(
            "Progress:",
            self.progress_label,
        )

        progress_layout.addRow(
            "Downloaded:",
            self.downloaded_label,
        )

        progress_layout.addRow(
            "Speed:",
            self.speed_label,
        )

        progress_layout.addRow(
            "ETA:",
            self.eta_label,
        )

        main_layout.addWidget(
            progress_group
        )

        # ---------------------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------------------

        button_layout = QHBoxLayout()

        self.download_button = QPushButton(
            "Download"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.cancel_button.clicked.connect(
            self._cancel_download
        )

        self.download_button.clicked.connect(
            self._start_download
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.cancel_button
        )

        button_layout.addWidget(
            self.download_button
        )

        main_layout.addLayout(
            button_layout
        )

    def _populate_product_information(self):
        """Populate the product information section."""

        product_id = self.properties.get(
            "fileID",
            self.properties.get(
                "sceneName",
                "Unknown",
            ),
        )

        file_name = self.properties.get(
            "fileName",
            "Unknown",
        )

        processing_level = self.properties.get(
            "processingLevel",
            "Unknown",
        )

        polarization = self.properties.get(
            "polarization",
            "Unknown",
        )

        start_time = self.properties.get(
            "startTime",
            "Unknown",
        )

        stop_time = self.properties.get(
            "stopTime",
            "Unknown",
        )

        self.product_id_label.setText(
            str(product_id)
        )

        self.file_name_label.setText(
            str(file_name)
        )

        self.processing_level_label.setText(
            str(processing_level)
        )

        self.polarization_label.setText(
            str(polarization)
        )

        self.acquisition_label.setText(
            f"{start_time} → {stop_time}"
        )

        size_bytes = self._get_product_size()

        if size_bytes is not None:
            self.dataset_size_label.setText(
                self._format_size(size_bytes)
            )
        else:
            self.dataset_size_label.setText(
                "Unknown"
            )

    def _get_product_size(self):
        """Return the HDF5 product size in bytes."""

        byte_metadata = self.properties.get(
            "bytes",
            {},
        )

        if not isinstance(
            byte_metadata,
            dict,
        ):
            return None

        for filename, metadata in byte_metadata.items():

            if not filename.lower().endswith(".h5"):
                continue

            if not isinstance(
                metadata,
                dict,
            ):
                continue

            size_bytes = metadata.get(
                "bytes"
            )

            if isinstance(
                size_bytes,
                (int, float),
            ):
                return int(size_bytes)

        return None

    @staticmethod
    def _format_size(size_bytes):
        """Convert bytes into a human-readable binary size."""

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

    def _update_download_mode(self):
        """Enable or disable AOI controls."""

        use_aoi = self.aoi_radio.isChecked()

        self.aoi_layer_combo.setEnabled(
            use_aoi
        )

    def _select_output_folder(self):
        """Select the destination folder."""

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select NISAR Output Folder",
            self.output_folder_label.text(),
        )

        if folder:
            self.output_folder_label.setText(
                folder
            )

    def _start_download(self):
        """Start a full NISAR product download in a background thread."""

        # -------------------------------------------------------------------------
        # Download mode validation
        # -------------------------------------------------------------------------

        if self.aoi_radio.isChecked():
            QMessageBox.information(
                self,
                "NISAR Download",
                "AOI / Region Subset is not available yet.\n\n"
                "Please use Full Product for now.",
            )
            return

        # -------------------------------------------------------------------------
        # Authentication validation
        # -------------------------------------------------------------------------

        if self.session is None:
            QMessageBox.warning(
                self,
                "NISAR Download",
                "No authenticated Earthdata session is available.\n\n"
                "Please authenticate with NASA Earthdata before downloading.",
            )
            return

        # -------------------------------------------------------------------------
        # Output folder validation
        # -------------------------------------------------------------------------

        output_folder = self.output_folder_label.text().strip()

        if not output_folder or not os.path.isdir(output_folder):
            QMessageBox.warning(
                self,
                "NISAR Download",
                "Please select a valid output folder.",
            )
            return

        # -------------------------------------------------------------------------
        # Product URL
        # -------------------------------------------------------------------------

        product_url = self.properties.get("url")

        if not product_url:
            QMessageBox.warning(
                self,
                "NISAR Download",
                "The selected NISAR product does not contain a download URL.",
            )
            return

        # -------------------------------------------------------------------------
        # Output filename
        # -------------------------------------------------------------------------

        file_name = self.properties.get("fileName")

        if not file_name:
            QMessageBox.warning(
                self,
                "NISAR Download",
                "The selected NISAR product does not contain a file name.",
            )
            return

        file_name = os.path.basename(str(file_name))

        if not file_name.lower().endswith(".h5"):
            QMessageBox.warning(
                self,
                "NISAR Download",
                "The selected product is not an HDF5 (.h5) product.",
            )
            return

        output_path = os.path.join(
            output_folder,
            file_name,
        )

        # -------------------------------------------------------------------------
        # Prevent accidental overwrite
        # -------------------------------------------------------------------------

        if os.path.exists(output_path):
            response = QMessageBox.question(
                self,
                "File Already Exists",
                (
                    f"The file already exists:\n\n"
                    f"{output_path}\n\n"
                    "Do you want to replace it?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if response != QMessageBox.Yes:
                return

        # -------------------------------------------------------------------------
        # Expected product size
        # -------------------------------------------------------------------------

        expected_size = self._get_product_size()

        # -------------------------------------------------------------------------
        # Prepare GUI
        # -------------------------------------------------------------------------

        self._cancel_requested = False

        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.status_label.setText(
            "Starting download..."
        )

        self.progress_label.setText(
            "Progress: 0%"
        )

        self.downloaded_label.setText(
            "Downloaded: 0 B"
        )

        self.speed_label.setText(
            "Speed: —"
        )

        self.eta_label.setText(
            "Estimated time remaining: —"
        )

        # -------------------------------------------------------------------------
        # Create worker thread
        # -------------------------------------------------------------------------

        self.download_thread = QThread(
            self
        )

        self.download_worker = NISARDownloadWorker(
            url=product_url,
            output_path=output_path,
            expected_size=expected_size,
            session=self.session,
        )

        self.download_worker.moveToThread(
            self.download_thread
        )

        # -------------------------------------------------------------------------
        # Worker signals
        # -------------------------------------------------------------------------

        self.download_thread.started.connect(
            self.download_worker.run
        )

        self.download_worker.progress.connect(
            self._update_download_progress
        )

        self.download_worker.finished.connect(
            self._download_finished
        )

        self.download_worker.cancelled.connect(
            self._download_cancelled
        )

        self.download_worker.error.connect(
            self._download_error
        )

        # -------------------------------------------------------------------------
        # Thread cleanup
        # -------------------------------------------------------------------------

        self.download_worker.finished.connect(
            self.download_thread.quit
        )

        self.download_worker.cancelled.connect(
            self.download_thread.quit
        )

        self.download_worker.error.connect(
            self.download_thread.quit
        )

        self.download_thread.finished.connect(
            self._download_thread_finished
        )

        # -------------------------------------------------------------------------
        # Start background download
        # -------------------------------------------------------------------------

        self.download_thread.start()

    def _update_download_progress(
        self,
        percentage,
        downloaded,
        speed,
        eta,
        total,
    ):
        """Update the download progress displayed by the dialog."""

        self.progress_label.setText(
            f"Progress: {percentage}%"
        )

        if total:
            self.downloaded_label.setText(
                f"Downloaded: "
                f"{self._format_size(downloaded)} / "
                f"{self._format_size(total)}"
            )
        else:
            self.downloaded_label.setText(
                f"Downloaded: "
                f"{self._format_size(downloaded)}"
            )

        if speed and speed > 0:
            self.speed_label.setText(
                f"Speed: {self._format_size(speed)}/s"
            )
        else:
            self.speed_label.setText(
                "Speed: —"
            )

        if eta is not None:
            self.eta_label.setText(
                f"ETA: {self._format_time(eta)}"
            )
        else:
            self.eta_label.setText(
                "ETA: —"
            )

        self.status_label.setText(
            "Downloading..."
        )

    @staticmethod
    def _format_time(seconds):
        """Format seconds into a human-readable duration."""

        if seconds is None:
            return "—"

        seconds = max(0, int(seconds))

        hours, remainder = divmod(
            seconds,
            3600,
        )

        minutes, seconds = divmod(
            remainder,
            60,
        )

        if hours:
            return f"{hours}h {minutes}m {seconds}s"

        if minutes:
            return f"{minutes}m {seconds}s"

        return f"{seconds}s"

    def _download_finished(self, output_path):
        """Handle successful download completion."""

        self.status_label.setText(
            "Download completed successfully."
        )

        self.progress_label.setText(
            "Progress: 100%"
        )

        self.downloaded_label.setText(
            f"Downloaded: "
            f"{self._format_size(os.path.getsize(output_path))}"
        )

        self.speed_label.setText(
            "Speed: —"
        )

        self.eta_label.setText(
            "ETA: Complete"
        )

        QMessageBox.information(
            self,
            "NISAR Download",
            (
                "NISAR product downloaded successfully.\n\n"
                f"File:\n{output_path}"
            ),
        )

    def _download_cancelled(self):
        """Handle cancellation of the download."""

        self.status_label.setText(
            "Download cancelled."
        )

        self.cancel_button.setEnabled(
            True
        )

        self.download_button.setEnabled(
            True
        )

    def _download_error(self, message):
        """Handle a download error."""

        self.status_label.setText(
            "Download failed."
        )

        QMessageBox.critical(
            self,
            "NISAR Download Error",
            (
                "The NISAR product could not be downloaded.\n\n"
                f"{message}"
            ),
        )

        self.download_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            True
        )

    def _download_thread_finished(self):
        """Clean up the completed download thread."""

        if self.download_worker is not None:
            self.download_worker.deleteLater()
            self.download_worker = None

        if self.download_thread is not None:
            self.download_thread.deleteLater()
            self.download_thread = None

    def _cancel_download(self):
        """Request cancellation of the active download."""

        if self.download_worker is not None:
            self.download_worker.request_cancel()

        self.status_label.setText(
            "Cancelling download..."
        )

        self.cancel_button.setEnabled(
            False
        )

    # def _cancel_download(self):
    #     """Request cancellation of the active download."""

    #     if self.download_worker is not None:
    #         self.status_label.setText(
    #             "Cancelling download..."
    #         )

    #         self.cancel_button.setEnabled(
    #             False
    #         )

    #         self.download_worker.request_cancel()

    #         return

    #     self.reject()