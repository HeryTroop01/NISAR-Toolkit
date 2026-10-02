# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_search.py
# Module     : NISAR Catalogue Search
# Version    : 0.1.1
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides the first NISAR catalogue-search Processing algorithm.
#
#     This module communicates with the ASF Search API through the
#     asf_search Python package. It is intentionally limited to catalogue
#     discovery in this version. Downloading, authentication, HDF5
#     inspection, and QGIS layer loading will be implemented separately.
#
# Data source:
#     Alaska Satellite Facility (ASF) / NASA Earthdata
#
# Status:
#     Development
# =============================================================================

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


class NISARSearchAlgorithm(QgsProcessingAlgorithm):
    """Search the ASF catalogue for NISAR products."""

    DATASET = "DATASET"
    PROCESSING_LEVEL = "PROCESSING_LEVEL"
    MAX_RESULTS = "MAX_RESULTS"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        """Define the Processing algorithm parameters."""

        self.addParameter(
            QgsProcessingParameterString(
                self.DATASET,
                "Dataset",
                defaultValue="NISAR",
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.PROCESSING_LEVEL,
                "Processing level",
                defaultValue="GSLC",
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_RESULTS,
                "Maximum results",
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                maxValue=100,
                defaultValue=10,
            )
        )

        fields = QgsFields()

        fields.append(QgsField("product_id", QVariant.String))
        fields.append(QgsField("processing_level", QVariant.String))
        fields.append(QgsField("platform", QVariant.String))
        fields.append(QgsField("start_time", QVariant.String))
        fields.append(QgsField("end_time", QVariant.String))

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Search results",
                QgsProcessing.TypeVector,
                fields,
                QgsWkbTypes.NoGeometry,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Execute the NISAR catalogue search."""

        try:
            import asf_search
        except ImportError as exc:
            raise RuntimeError(
                "The 'asf_search' package is not installed in the QGIS Python environment."
            ) from exc

        dataset = self.parameterAsString(
            parameters,
            self.DATASET,
            context,
        )

        processing_level = self.parameterAsString(
            parameters,
            self.PROCESSING_LEVEL,
            context,
        )

        max_results = self.parameterAsInt(
            parameters,
            self.MAX_RESULTS,
            context,
        )

        feedback.pushInfo(
            f"Searching ASF catalogue: dataset={dataset}, "
            f"processingLevel={processing_level}, "
            f"maxResults={max_results}"
        )

        results = asf_search.search(
            dataset=dataset,
            processingLevel=processing_level,
            maxResults=max_results,
        )

        feedback.pushInfo(
            f"ASF returned {len(results)} result(s)."
        )

        fields = QgsFields()

        fields.append(QgsField("product_id", QVariant.String))
        fields.append(QgsField("processing_level", QVariant.String))
        fields.append(QgsField("platform", QVariant.String))
        fields.append(QgsField("start_time", QVariant.String))
        fields.append(QgsField("end_time", QVariant.String))

        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.NoGeometry,
        )

        if sink is None:
            raise RuntimeError("Could not create the output layer.")

        for result in results:
            if feedback.isCanceled():
                break

            feature = QgsFeature(fields)

            feature["product_id"] = getattr(
                result,
                "properties",
                {},
            ).get("sceneName", result.properties.get("fileID", ""))

            feature["processing_level"] = processing_level

            feature["platform"] = getattr(
                result,
                "properties",
                {},
            ).get("platform", "NISAR")

            feature["start_time"] = getattr(
                result,
                "properties",
                {},
            ).get("startTime", "")

            feature["end_time"] = getattr(
                result,
                "properties",
                {},
            ).get("stopTime", "")

            sink.addFeature(feature)

        return {
            self.OUTPUT: destination_id,
        }

    def name(self):
        """Return the internal algorithm name."""
        return "nisar_search"

    def displayName(self):
        """Return the user-visible algorithm name."""
        return "Search NISAR Catalogue"

    def group(self):
        """Return the Processing toolbox group."""
        return "NISAR Toolkit"

    def groupId(self):
        """Return the Processing toolbox group ID."""
        return "nisar_toolkit"

    def shortHelpString(self):
        """Return the algorithm help text."""
        return (
            "Search the ASF catalogue for NISAR products. "
            "This initial version supports dataset, processing-level, "
            "and maximum-result filtering."
        )

    def createInstance(self):
        """Create a new algorithm instance."""
        return NISARSearchAlgorithm()
