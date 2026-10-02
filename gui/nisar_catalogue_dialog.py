# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_catalogue_dialog.py
# Module     : NISAR Catalogue Search Dialog
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides a graphical interface for searching the ASF NISAR catalogue.
#
#     The dialog:
#         - Accepts catalogue search parameters.
#         - Displays returned NISAR products in a table.
#         - Retains the complete ASF product properties for each result.
#         - Opens the NISAR product preview dialog.
#         - Opens the ASF product URL in the default web browser.
# =============================================================================

import webbrowser

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class NISARCatalogueDialog(QDialog):
    """Graphical interface for searching the ASF NISAR catalogue."""

    def __init__(self, parent=None):
        """Initialize the catalogue search dialog."""
        super().__init__(parent)

        self.setWindowTitle("NISAR Catalogue Search")
        self.resize(1200, 700)

        self.results = []

        self._create_interface()

    def _create_interface(self):
        """Create the catalogue search interface."""

        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------------------
        # Search parameters
        # ---------------------------------------------------------------------

        search_layout = QFormLayout()

        self.dataset_combo = QComboBox()
        self.dataset_combo.addItem("NISAR")

        search_layout.addRow(
            "Dataset:",
            self.dataset_combo,
        )

        self.processing_level_combo = QComboBox()
        self.processing_level_combo.addItems(
            [
                "GSLC",
                "GCOV",
                "GUNW",
                "ROFF",
            ]
        )

        search_layout.addRow(
            "Processing level:",
            self.processing_level_combo,
        )

        self.max_results_spin = QSpinBox()
        self.max_results_spin.setMinimum(1)
        self.max_results_spin.setMaximum(100)
        self.max_results_spin.setValue(10)

        search_layout.addRow(
            "Maximum results:",
            self.max_results_spin,
        )

        main_layout.addLayout(search_layout)

        # ---------------------------------------------------------------------
        # Search button
        # ---------------------------------------------------------------------

        search_button_layout = QHBoxLayout()

        self.search_button = QPushButton(
            "Search Catalogue"
        )

        self.search_button.clicked.connect(
            self._search_catalogue
        )

        search_button_layout.addWidget(
            self.search_button
        )

        search_button_layout.addStretch()

        main_layout.addLayout(
            search_button_layout
        )

        # ---------------------------------------------------------------------
        # Results table
        # ---------------------------------------------------------------------

        self.results_table = QTableWidget()

        self.results_table.setColumnCount(8)

        self.results_table.setHorizontalHeaderLabels(
            [
                "Product ID",
                "Processing Level",
                "Polarization",
                "Start Time",
                "End Time",
                "Flight Direction",
                "Orbit",
                "File Size (MiB)",
            ]
        )

        self.results_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.results_table.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.results_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.results_table.horizontalHeader().setStretchLastSection(
            True
        )

        main_layout.addWidget(
            self.results_table
        )

        # ---------------------------------------------------------------------
        # Action buttons
        # ---------------------------------------------------------------------

        action_layout = QHBoxLayout()

        self.preview_button = QPushButton(
            "Preview"
        )

        self.preview_button.clicked.connect(
            self._preview_selected
        )

        self.open_product_button = QPushButton(
            "Open Product"
        )

        self.open_product_button.clicked.connect(
            self._open_selected_product
        )

        action_layout.addWidget(
            self.preview_button
        )

        action_layout.addWidget(
            self.open_product_button
        )

        action_layout.addStretch()

        main_layout.addLayout(
            action_layout
        )

        # ---------------------------------------------------------------------
        # Status
        # ---------------------------------------------------------------------

        self.status_label = QLabel(
            "Ready."
        )

        self.status_label.setAlignment(
            Qt.AlignLeft
        )

        main_layout.addWidget(
            self.status_label
        )

    def _search_catalogue(self):
        """Search the ASF catalogue using the selected parameters."""

        try:
            import asf_search
        except ImportError:
            QMessageBox.critical(
                self,
                "NISAR Toolkit",
                "The 'asf_search' package is not installed "
                "in the QGIS Python environment.",
            )
            return

        dataset = self.dataset_combo.currentText()
        processing_level = (
            self.processing_level_combo.currentText()
        )
        max_results = self.max_results_spin.value()

        self.status_label.setText(
            "Searching ASF catalogue..."
        )

        self.search_button.setEnabled(False)

        try:
            results = asf_search.search(
                dataset=dataset,
                processingLevel=processing_level,
                maxResults=max_results,
            )

            self.results = list(results)

            self._populate_results()

            self.status_label.setText(
                f"{len(self.results)} product(s) found."
            )

        except Exception as exc:
            self.results = []

            self.results_table.setRowCount(0)

            QMessageBox.critical(
                self,
                "NISAR Catalogue Search",
                f"Catalogue search failed:\n\n{exc}",
            )

            self.status_label.setText(
                "Search failed."
            )

        finally:
            self.search_button.setEnabled(True)

    def _populate_results(self):
        """Populate the results table with ASF products."""

        self.results_table.setRowCount(
            len(self.results)
        )

        for row, result in enumerate(self.results):

            properties = getattr(
                result,
                "properties",
                {},
            )

            values = [
                properties.get(
                    "fileID",
                    properties.get(
                        "sceneName",
                        "",
                    ),
                ),
                properties.get(
                    "processingLevel",
                    "",
                ),
                properties.get(
                    "polarization",
                    "",
                ),
                properties.get(
                    "startTime",
                    "",
                ),
                properties.get(
                    "stopTime",
                    "",
                ),
                properties.get(
                    "flightDirection",
                    "",
                ),
                properties.get(
                    "orbit",
                    "",
                ),
                self._get_h5_size_mb(
                    properties.get(
                        "bytes",
                        {},
                    )
                ),
            ]

            for column, value in enumerate(values):

                if value is None:
                    value = ""

                item = QTableWidgetItem(
                    str(value)
                )

                self.results_table.setItem(
                    row,
                    column,
                    item,
                )

    def _get_selected_result(self):
        """Return the ASF result selected in the table."""

        selected_rows = (
            self.results_table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            QMessageBox.information(
                self,
                "NISAR Toolkit",
                "Please select a catalogue product first.",
            )
            return None

        row = selected_rows[0].row()

        if row < 0 or row >= len(self.results):
            return None

        return self.results[row]

    def _preview_selected(self):
        """Open the preview dialog for the selected product."""

        result = self._get_selected_result()

        if result is None:
            return

        properties = getattr(
            result,
            "properties",
            {},
        )

        try:
            from importlib.util import module_from_spec, spec_from_file_location
            from pathlib import Path

            module_path = (
                Path(__file__).resolve().parent
                / "nisar_preview_dialog.py"
            )

            spec = spec_from_file_location(
                "nisar_preview_dialog",
                module_path,
            )

            if spec is None or spec.loader is None:
                raise ImportError(
                    "Could not locate the NISAR preview dialog module."
                )

            module = module_from_spec(spec)
            spec.loader.exec_module(module)

            NISARPreviewDialog = module.NISARPreviewDialog

            self.preview_dialog = NISARPreviewDialog(
                properties,
                parent=self,
            )

            self.preview_dialog.show()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "NISAR Preview",
                f"Could not open the preview:\n\n{exc}",
            )

    def _open_selected_product(self):
        """Open the ASF product URL for the selected result."""

        result = self._get_selected_result()

        if result is None:
            return

        properties = getattr(
            result,
            "properties",
            {},
        )

        product_url = properties.get(
            "url",
            "",
        )

        if not product_url:
            QMessageBox.information(
                self,
                "NISAR Toolkit",
                "No product URL is available for this result.",
            )
            return

        webbrowser.open(
            product_url
        )

    @staticmethod
    def _get_h5_size_mb(byte_metadata):
        """Extract HDF5 product size and convert bytes to MiB."""

        if not isinstance(
            byte_metadata,
            dict,
        ):
            return None

        for filename, metadata in byte_metadata.items():

            if filename.lower().endswith(".h5"):

                if isinstance(
                    metadata,
                    dict,
                ):

                    size_bytes = metadata.get(
                        "bytes"
                    )

                    if isinstance(
                        size_bytes,
                        (int, float),
                    ):
                        return round(
                            size_bytes / (1024 * 1024),
                            2,
                        )

        return None