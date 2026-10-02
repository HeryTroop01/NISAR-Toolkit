# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_provider.py
# Module     : QGIS Processing Provider
# Version    : 0.1.1
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Registers NISAR-related Processing algorithms with QGIS.
#
#     Algorithms are kept in separate modules so that the provider remains
#     small and easy to extend as new NISAR functionality is added.
# =============================================================================

from qgis.core import QgsProcessingProvider

from .processing.nisar_search import NISARSearchAlgorithm


class NISARProvider(QgsProcessingProvider):
    """Processing provider for NISAR Toolkit algorithms."""

    def __init__(self):
        """Initialize the NISAR Processing provider."""
        super().__init__()

    def loadAlgorithms(self):
        """Register all available NISAR Processing algorithms."""
        self.addAlgorithm(
            NISARSearchAlgorithm()
        )

    def id(self):
        """Return the unique provider ID."""
        return "nisar_toolkit"

    def name(self):
        """Return the provider name."""
        return "NISAR Toolkit"

    def longName(self):
        """Return the full provider name."""
        return "NISAR Toolkit Processing Provider"
    