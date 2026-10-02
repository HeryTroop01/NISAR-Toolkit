# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_preview_dialog.py
# Module     : NISAR Product Preview Dialog
# Version    : 0.1.1
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides the graphical preview dialog for an ASF NISAR catalogue
#     product.
#
#     The dialog displays available ASF browse images and selected product
#     metadata. It is intentionally independent from the catalogue-search
#     Processing algorithm.
#
# Data source:
#     Alaska Satellite Facility (ASF) / NASA Earthdata
#
# Status:
#     Development
# =============================================================================

from typing import Any, Dict, List

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import importlib.util
from pathlib import Path


def _load_preview_client():
    """Load the preview client from the plugin's processing directory."""

    module_path = (
        Path(__file__).resolve().parent.parent
        / "processing"
        / "nisar_preview.py"
    )

    spec = importlib.util.spec_from_file_location(
        "nisar_preview",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            "Could not locate the NISAR preview client module."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return (
        module.NISARPreviewClient,
        module.NISARPreviewError,
    )


NISARPreviewClient, NISARPreviewError = _load_preview_client()


class NISARPreviewDialog(QDialog):
    """Display ASF browse images and metadata for one NISAR product."""

    def __init__(
        self,
        properties: Dict[str, Any],
        parent: QWidget = None,
    ):
        """Initialize the NISAR product preview dialog."""

        super().__init__(parent)

        self.properties = properties
        self.preview_client = NISARPreviewClient()
        self.current_pixmap = None

        self.setWindowTitle("NISAR Product Preview")
        self.resize(1100, 750)

        self._build_ui()
        self._load_product_information()
        self._load_browse_options()

    def _build_ui(self):
        """Create the dialog controls and layout."""

        main_layout = QVBoxLayout(self)

        title_label = QLabel("NISAR Product Preview")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )
        main_layout.addWidget(title_label)

        content_layout = QHBoxLayout()

        preview_layout = QVBoxLayout()

        self.browse_selector = QComboBox()
        self.browse_selector.currentIndexChanged.connect(
            self._browse_selection_changed
        )
        preview_layout.addWidget(self.browse_selector)

        self.image_label = QLabel("No preview loaded.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(500, 500)
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)

        preview_layout.addWidget(scroll_area)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        preview_layout.addWidget(self.status_label)

        content_layout.addLayout(
            preview_layout,
            2,
        )

        metadata_widget = QWidget()
        metadata_layout = QFormLayout(metadata_widget)

        self.metadata_labels = {}

        metadata_fields = (
            ("product_id", "Product ID"),
            ("file_name", "File name"),
            ("processingLevel", "Processing level"),
            ("collectionName", "Collection"),
            ("platform", "Platform"),
            ("sensor", "Sensor"),
            ("polarization", "Polarization"),
            ("startTime", "Start time"),
            ("stopTime", "End time"),
            ("flightDirection", "Flight direction"),
            ("orbit", "Orbit"),
            ("orbitType", "Orbit type"),
            ("pathNumber", "Path number"),
            ("frameNumber", "Frame number"),
            ("frameCoverage", "Frame coverage"),
            ("pgeVersion", "PGE version"),
            ("file_size_mb", "File size (MiB)"),
        )

        for key, label_text in metadata_fields:
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )

            metadata_layout.addRow(
                f"{label_text}:",
                value_label,
            )

            self.metadata_labels[key] = value_label

        content_layout.addWidget(
            metadata_widget,
            1,
        )

        main_layout.addLayout(content_layout)

        button_layout = QHBoxLayout()

        self.open_preview_button = QPushButton("Open Preview")
        self.open_preview_button.clicked.connect(
            self._open_current_preview
        )
        button_layout.addWidget(self.open_preview_button)

        button_layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Close
        )
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)

        main_layout.addLayout(button_layout)

    def _load_product_information(self):
        """Populate the metadata panel from ASF product properties."""

        browse_urls = self.preview_client.get_browse_urls(
            self.properties
        )

        file_name = self.properties.get(
            "fileName",
            "",
        )

        self._set_metadata(
            "product_id",
            self.properties.get(
                "fileID",
                self.properties.get("sceneName", ""),
            ),
        )

        self._set_metadata(
            "file_name",
            file_name,
        )

        self._set_metadata(
            "processingLevel",
            self.properties.get("processingLevel", ""),
        )

        self._set_metadata(
            "collectionName",
            self.properties.get("collectionName", ""),
        )

        self._set_metadata(
            "platform",
            self.properties.get("platform", ""),
        )

        self._set_metadata(
            "sensor",
            self.properties.get("sensor", ""),
        )

        self._set_metadata(
            "polarization",
            self.properties.get("polarization", ""),
        )

        self._set_metadata(
            "startTime",
            self.properties.get("startTime", ""),
        )

        self._set_metadata(
            "stopTime",
            self.properties.get("stopTime", ""),
        )

        self._set_metadata(
            "flightDirection",
            self.properties.get("flightDirection", ""),
        )

        self._set_metadata(
            "orbit",
            self.properties.get("orbit", ""),
        )

        self._set_metadata(
            "orbitType",
            self.properties.get("orbitType", ""),
        )

        self._set_metadata(
            "pathNumber",
            self.properties.get("pathNumber", ""),
        )

        self._set_metadata(
            "frameNumber",
            self.properties.get("frameNumber", ""),
        )

        self._set_metadata(
            "frameCoverage",
            self.properties.get("frameCoverage", ""),
        )

        self._set_metadata(
            "pgeVersion",
            self.properties.get("pgeVersion", ""),
        )

        file_size = self._get_h5_size_mb(
            self.properties.get("bytes", {})
        )

        self._set_metadata(
            "file_size_mb",
            f"{file_size:.2f}" if file_size is not None else "",
        )

        if not browse_urls:
            self.status_label.setText(
                "No supported browse images are available."
            )

    def _load_browse_options(self):
        """Populate the browse-image selector."""

        options = self.preview_client.get_browse_options(
            self.properties
        )

        self.browse_selector.blockSignals(True)
        self.browse_selector.clear()

        for option in options:
            self.browse_selector.addItem(
                option["label"],
                option["url"],
            )

        self.browse_selector.blockSignals(False)

        if options:
            self.browse_selector.setCurrentIndex(0)
            self._load_selected_browse_image()

    def _browse_selection_changed(self, index: int):
        """Load the browse image selected by the user."""

        if index < 0:
            return

        self._load_selected_browse_image()

    def _load_selected_browse_image(self):
        """Download and display the currently selected browse image."""

        url = self.browse_selector.currentData()

        if not url:
            self.image_label.setText("No preview selected.")
            return

        self.status_label.setText(
            "Loading preview..."
        )

        try:
            pixmap = self.preview_client.load_pixmap(url)
        except NISARPreviewError as exc:
            self.current_pixmap = None
            self.image_label.clear()
            self.status_label.setText(
                f"Preview error: {exc}"
            )
            return

        self.current_pixmap = pixmap
        self._display_pixmap()

        self.status_label.setText(
            f"Preview loaded: {pixmap.width()} × "
            f"{pixmap.height()} pixels"
        )

    def _display_pixmap(self):
        """Scale the current image to fit the preview area."""

        if self.current_pixmap is None:
            return

        available_size = self.image_label.size()

        scaled_pixmap = self.current_pixmap.scaled(
            available_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled_pixmap)

    def _open_current_preview(self):
        """Open the currently selected browse image in the default viewer."""

        url = self.browse_selector.currentData()

        if not url:
            QMessageBox.warning(
                self,
                "NISAR Preview",
                "No browse image is selected.",
            )
            return

        try:
            import webbrowser

            webbrowser.open(url)

        except Exception as exc:
            QMessageBox.warning(
                self,
                "NISAR Preview",
                f"Could not open the preview URL.\n\n{exc}",
            )

    def resizeEvent(self, event):
        """Keep the displayed preview scaled after resizing the dialog."""

        super().resizeEvent(event)
        self._display_pixmap()

    def _set_metadata(self, key: str, value: Any):
        """Set a metadata value in the corresponding label."""

        label = self.metadata_labels.get(key)

        if label is not None:
            label.setText(
                str(value) if value not in (None, "") else "-"
            )

    @staticmethod
    def _get_h5_size_mb(byte_metadata: Any):
        """Extract the HDF5 product size and convert bytes to MiB."""

        if not isinstance(byte_metadata, dict):
            return None

        for filename, metadata in byte_metadata.items():
            if not filename.lower().endswith(".h5"):
                continue

            if not isinstance(metadata, dict):
                continue

            size_bytes = metadata.get("bytes")

            if isinstance(size_bytes, (int, float)):
                return size_bytes / (1024 * 1024)

        return None
