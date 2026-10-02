# =============================================================================
# NISAR Toolkit
# -----------------------------------------------------------------------------
# File       : nisar_auth_dialog.py
# Module     : NASA Earthdata Authentication Dialog
# Version    : 0.1.0
# Author     : Punithan
# Project    : NISAR Toolkit
#
# Description:
#     Provides a session-only NASA Earthdata authentication interface.
#
#     The Earthdata token is entered by the user at runtime and is used to
#     create an authenticated ASFSession. The token is not written to the
#     plugin source code or GitHub repository.
# =============================================================================

from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class NISARAuthDialog(QDialog):
    """Dialog for creating an authenticated ASF session."""

    def __init__(self, parent=None):
        """Initialize the Earthdata authentication dialog."""

        super().__init__(parent)

        self.setWindowTitle(
            "NASA Earthdata Authentication"
        )

        self.resize(600, 220)

        self.session = None

        self._create_interface()

    def _create_interface(self):
        """Create the authentication interface."""

        main_layout = QVBoxLayout(self)

        # ---------------------------------------------------------------------
        # Information
        # ---------------------------------------------------------------------

        information_label = QLabel(
            "Enter your NASA Earthdata personal access token.\n\n"
            "The token is used only to create the authenticated ASF session "
            "for this QGIS session. It is not stored by NISAR Toolkit."
        )

        information_label.setWordWrap(True)

        main_layout.addWidget(
            information_label
        )

        # ---------------------------------------------------------------------
        # Token
        # ---------------------------------------------------------------------

        form_layout = QFormLayout()

        self.token_edit = QLineEdit()

        self.token_edit.setEchoMode(
            QLineEdit.Password
        )

        self.token_edit.setPlaceholderText(
            "Paste your Earthdata token"
        )

        form_layout.addRow(
            "Earthdata Token:",
            self.token_edit,
        )

        main_layout.addLayout(
            form_layout
        )

        # ---------------------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------------------

        button_layout = QHBoxLayout()

        self.authenticate_button = QPushButton(
            "Authenticate"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.authenticate_button.clicked.connect(
            self._authenticate
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.cancel_button
        )

        button_layout.addWidget(
            self.authenticate_button
        )

        main_layout.addLayout(
            button_layout
        )

    def _authenticate(self):
        """Authenticate with NASA Earthdata through ASF."""

        token = self.token_edit.text().strip()

        if not token:
            QMessageBox.warning(
                self,
                "Earthdata Authentication",
                "Please enter your NASA Earthdata token.",
            )

            return

        self.authenticate_button.setEnabled(
            False
        )

        self.status_label = QLabel(
            "Authenticating..."
        )

        self.status_label.setWordWrap(True)

        self.layout().insertWidget(
            2,
            self.status_label,
        )

        try:
            import asf_search

            session = asf_search.ASFSession()

            session.auth_with_token(
                token
            )

            self.session = session

            # Clear the token from the visible input field after
            # authentication succeeds.
            self.token_edit.clear()

            self.status_label.setText(
                "Authentication successful."
            )

            self.accept()

        except Exception as exc:
            self.session = None

            self.status_label.setText(
                "Authentication failed."
            )

            QMessageBox.critical(
                self,
                "Earthdata Authentication",
                (
                    "NASA Earthdata authentication failed.\n\n"
                    f"{exc}"
                ),
            )

            self.authenticate_button.setEnabled(
                True
            )