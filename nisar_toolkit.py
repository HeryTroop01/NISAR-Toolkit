# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_toolkit.py
# Module     : Main QGIS Plugin
# Version    : 0.1.1
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Main QGIS plugin class for the NISAR Toolkit.
#
#     This module is responsible for:
#         - Initializing the plugin.
#         - Registering the NISAR Processing provider.
#         - Creating the QGIS toolbar/menu action.
#         - Cleaning up the provider and GUI elements during unload.
# =============================================================================

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication

from .nisar_provider import NISARProvider
class NISARToolkit:
    """Main QGIS plugin class for NISAR Toolkit."""

    def __init__(self, iface):
        """Initialize the plugin with the QGIS interface."""
        self.iface = iface
        self.action = None
        self.provider = None

    def initGui(self):
        """Initialize the plugin GUI and Processing provider."""

        self.provider = NISARProvider()

        if not QgsApplication.processingRegistry().addProvider(
            self.provider
        ):
            raise RuntimeError(
                "Failed to register the NISAR Toolkit Processing provider."
            )

        self.action = QAction(
            "NISAR Toolkit",
            self.iface.mainWindow(),
        )

        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)

        self.iface.addPluginToMenu(
            "&NISAR Toolkit",
            self.action,
        )

    def unload(self):
        """Remove the plugin GUI and Processing provider."""

        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(
                self.provider
            )
            self.provider = None

        if self.action is not None:
            self.iface.removeToolBarIcon(
                self.action
            )

            self.iface.removePluginMenu(
                "&NISAR Toolkit",
                self.action
            )

            self.action.deleteLater()
            self.action = None

    def run(self):
        """Open the plugin information dialog."""

        QMessageBox.information(
            self.iface.mainWindow(),
            "NISAR Toolkit",
            "NISAR Toolkit v0.1.1 is loaded successfully.\n\n"
            "The NISAR Processing provider is now available.",
        )