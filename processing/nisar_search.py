# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_search.py
# Module     : NISAR Catalogue Search
# Version    : 0.1.2
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Searches the ASF catalogue for NISAR products and returns the results
#     as a spatial QGIS vector layer using the ASF product footprints.
#
#     The search supports:
#         - Dataset
#         - Processing level
#         - Start date
#         - End date
#         - Maximum number of results
#
# Data source:
#     Alaska Satellite Facility (ASF) / NASA Earthdata
#
# Status:
#     Development
# =============================================================================

import json
from datetime import datetime

from qgis.core import (
    QgsFeature,
    QgsFields,
    QgsField,
    QgsJsonUtils,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


class NISARSearchAlgorithm(QgsProcessingAlgorithm):
    """Search the ASF catalogue for NISAR products."""

    DATASET = "DATASET"
    PROCESSING_LEVEL = "PROCESSING_LEVEL"
    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
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
            QgsProcessingParameterString(
                self.START_DATE,
                "Start date",
                defaultValue="",
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.END_DATE,
                "End date",
                defaultValue="",
                optional=True,
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

        fields = self._create_output_fields()

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Search results",
                QgsProcessing.TypeVector,
                fields,
                QgsWkbTypes.Polygon,
            )
        )

    def _create_output_fields(self):
        """Create the catalogue result fields."""

        fields = QgsFields()

        fields.append(QgsField("product_id", QVariant.String))
        fields.append(QgsField("file_name", QVariant.String))
        fields.append(QgsField("processing_level", QVariant.String))
        fields.append(QgsField("collection", QVariant.String))
        fields.append(QgsField("platform", QVariant.String))
        fields.append(QgsField("sensor", QVariant.String))
        fields.append(QgsField("start_time", QVariant.String))
        fields.append(QgsField("end_time", QVariant.String))
        fields.append(QgsField("flight_direction", QVariant.String))
        fields.append(QgsField("orbit", QVariant.LongLong))
        fields.append(QgsField("orbit_type", QVariant.String))
        fields.append(QgsField("path_number", QVariant.LongLong))
        fields.append(QgsField("frame_number", QVariant.LongLong))
        fields.append(QgsField("polarization", QVariant.String))
        fields.append(QgsField("frame_coverage", QVariant.String))
        fields.append(QgsField("file_size_mb", QVariant.Double))
        fields.append(QgsField("browse_url", QVariant.String))
        fields.append(QgsField("product_url", QVariant.String))

        return fields

    @staticmethod
    def _format_start_date(date_text):
        """Convert a YYYY-MM-DD start date to an ASF timestamp."""

        if not date_text:
            return None

        try:
            parsed_date = datetime.strptime(
                date_text,
                "%Y-%m-%d",
            )
        except ValueError as exc:
            raise ValueError(
                "Start date must use the format YYYY-MM-DD."
            ) from exc

        return parsed_date.strftime(
            "%Y-%m-%dT00:00:00Z"
        )

    @staticmethod
    def _format_end_date(date_text):
        """Convert a YYYY-MM-DD end date to an ASF timestamp."""

        if not date_text:
            return None

        try:
            parsed_date = datetime.strptime(
                date_text,
                "%Y-%m-%d",
            )
        except ValueError as exc:
            raise ValueError(
                "End date must use the format YYYY-MM-DD."
            ) from exc

        return parsed_date.strftime(
            "%Y-%m-%dT23:59:59Z"
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Execute the NISAR catalogue search."""

        try:
            import asf_search
        except ImportError as exc:
            raise RuntimeError(
                "The 'asf_search' package is not installed in the QGIS "
                "Python environment."
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

        start_date_text = self.parameterAsString(
            parameters,
            self.START_DATE,
            context,
        ).strip()

        end_date_text = self.parameterAsString(
            parameters,
            self.END_DATE,
            context,
        ).strip()

        max_results = self.parameterAsInt(
            parameters,
            self.MAX_RESULTS,
            context,
        )

        start_date = self._format_start_date(
            start_date_text
        )

        end_date = self._format_end_date(
            end_date_text
        )

        if start_date and end_date:
            if start_date > end_date:
                raise ValueError(
                    "Start date cannot be later than end date."
                )

        feedback.pushInfo(
            f"Searching ASF catalogue: dataset={dataset}, "
            f"processingLevel={processing_level}, "
            f"start={start_date or 'not specified'}, "
            f"end={end_date or 'not specified'}, "
            f"maxResults={max_results}"
        )

        search_parameters = {
            "dataset": dataset,
            "processingLevel": processing_level,
            "maxResults": max_results,
        }

        if start_date:
            search_parameters["start"] = start_date

        if end_date:
            search_parameters["end"] = end_date

        results = asf_search.search(
            **search_parameters
        )

        feedback.pushInfo(
            f"ASF returned {len(results)} result(s)."
        )

        fields = self._create_output_fields()

        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Polygon,
        )

        if sink is None:
            raise RuntimeError(
                "Could not create the output layer."
            )

        for result in results:
            if feedback.isCanceled():
                break

            properties = getattr(
                result,
                "properties",
                {},
            )

            geometry_data = getattr(
                result,
                "geometry",
                None,
            )

            feature = QgsFeature(fields)

            if geometry_data:
                feature.setGeometry(
                    QgsJsonUtils.geometryFromGeoJson(
                        json.dumps(geometry_data)
                    )
                )

            feature["product_id"] = properties.get(
                "fileID",
                properties.get(
                    "sceneName",
                    "",
                ),
            )

            feature["file_name"] = properties.get(
                "fileName",
                "",
            )

            feature["processing_level"] = properties.get(
                "processingLevel",
                processing_level,
            )

            feature["collection"] = properties.get(
                "collectionName",
                "",
            )

            feature["platform"] = properties.get(
                "platform",
                "",
            )

            feature["sensor"] = properties.get(
                "sensor",
                "",
            )

            feature["start_time"] = properties.get(
                "startTime",
                "",
            )

            feature["end_time"] = properties.get(
                "stopTime",
                "",
            )

            feature["flight_direction"] = properties.get(
                "flightDirection",
                "",
            )

            feature["orbit"] = properties.get(
                "orbit",
                None,
            )

            feature["orbit_type"] = properties.get(
                "orbitType",
                "",
            )

            feature["path_number"] = properties.get(
                "pathNumber",
                None,
            )

            feature["frame_number"] = properties.get(
                "frameNumber",
                None,
            )

            feature["polarization"] = properties.get(
                "polarization",
                "",
            )

            feature["frame_coverage"] = properties.get(
                "frameCoverage",
                "",
            )

            file_size = self._get_h5_size_mb(
                properties.get(
                    "bytes",
                    {},
                )
            )

            feature["file_size_mb"] = file_size

            browse_urls = properties.get(
                "browse",
                [],
            )

            if isinstance(
                browse_urls,
                list,
            ) and browse_urls:

                feature["browse_url"] = browse_urls[0]

            else:
                feature["browse_url"] = ""

            feature["product_url"] = properties.get(
                "url",
                "",
            )

            sink.addFeature(feature)

        return {
            self.OUTPUT: destination_id,
        }

    @staticmethod
    def _get_h5_size_mb(byte_metadata):
        """Extract the HDF5 product size and convert bytes to MiB."""

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

                        return size_bytes / (
                            1024 * 1024
                        )

        return None

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
            "Search the ASF catalogue for NISAR products using "
            "dataset, processing level, optional acquisition dates, "
            "and maximum result count. Returns product metadata "
            "and spatial footprints."
        )

    def createInstance(self):
        """Create a new algorithm instance."""

        return NISARSearchAlgorithm()