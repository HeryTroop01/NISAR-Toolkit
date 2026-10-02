# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : __init__.py
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     QGIS plugin entry point for the NISAR Toolkit.
# =============================================================================


def classFactory(iface):
    """Create and return the NISAR Toolkit plugin instance."""
    from .nisar_toolkit import NISARToolkit

    return NISARToolkit(iface)
