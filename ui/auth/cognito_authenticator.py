import base64
import json
import os
from typing import Any
from urllib.parse import urlencode

import jwt
import requests
import streamlit as st

from ui.auth.base_authenticator import BaseAuthenticator


class CognitoAuthenticationError(Exception):
    """
    Custom exception for Cognito authentication errors.

    Attributes:
        message (str): The error message describing the authentication issue.
    """

    def __init__(self, message: str):
        """
        Initializes the CognitoAuthenticationError with a specific error message.

        Args:
            message (str): The error message.
        """
        super().__init__(message)
        self.message = message


class CognitoAuthenticator(BaseAuthenticator):
    """
    A class for handling authentication using AWS Cognito in a Streamlit application.
    """

    def _initialize_authenticator(self) -> Any:
        """
        Initializes the authenticator. This method is not implemented for Cognito.

        Returns:
            Any: Always returns None.
        """
        return None

    # pylint: disable=fixme
    def login(self):
        """
        Handles the login process by validating the user through ALB headers.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            username = self._process_alb_headers()
            st.session_state["authentication_status"] = True
            st.session_state["username"] = username
            st.session_state["roles"] = ["admin", "editor", "viewer"]  # TODO: get roles from Cognito
            st.sidebar.write(f"Welcome, **{username}**!")
            return True
        except Exception as e:  # pylint: disable=broad-except
            st.error(f"**Authentication Error**: {str(e)}")
            return False

    def render_logout(self):
        """
        Renders a logout button in the Streamlit sidebar.
        """
        st.sidebar.button(
            ":material/logout: Logout",
            on_click=self._on_logout,
            key="logout_button",
        )

    @staticmethod
    def _on_logout(*args, **kwargs):
        """
        Handles the logout process by clearing session state and redirecting the user.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        st.session_state.clear()

        # logout user from Cognito
        logout_url = (
            f"https://{os.environ['AWS_COGNITO_DOMAIN']}/logout?" +
            urlencode({
                "client_id": os.environ["AWS_COGNITO_CLIENT_ID"],
                "redirect_uri": os.environ["AWS_COGNITO_REDIRECT_URI"]
            })
        )
        st.write(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)

    def _process_alb_headers(self) -> str:
        """
        Processes the ALB headers to validate the JWT token and extract the username.

        Returns:
            str: The username extracted from the JWT payload.

        Raises:
            CognitoAuthenticationError: If the JWT token is invalid or headers are missing.
        """
        try:
            encoded_jwt = st.context.headers['x-amzn-oidc-data']
        except KeyError as exc:
            raise CognitoAuthenticationError("Missing x-amzn-oidc-data header") from exc

        # Step 1: Validate the signer
        jwt_headers = json.loads(base64.b64decode(encoded_jwt.split('.')[0]).decode("utf-8"))
        self._validate_jwt_headers(headers=jwt_headers)

        # Step 2: Get the key id from JWT headers (the kid field), and get the public key
        kid = jwt_headers['kid']
        pub_key = self._fetch_public_key(kid=kid)

        # Step 3: Get the payload
        payload = jwt.decode(encoded_jwt, pub_key, options={"verify_signature": True}, algorithms=['ES256'])
        if payload["iss"] != (
                f"https://cognito-idp.{os.environ['AWS_REGION']}.amazonaws.com/{os.environ['AWS_COGNITO_USER_POOL_ID']}"
        ):
            raise CognitoAuthenticationError("Invalid issuer for JWT token")

        return payload["username"]

    @staticmethod
    def _validate_jwt_headers(headers: dict):
        """Validates JWT headers for signer, issuer, and client."""
        if headers['signer'] != os.environ["AWS_ALB_ARN"]:
            raise CognitoAuthenticationError("Invalid signer for JWT token")
        if (
            headers["iss"]
            != f"https://cognito-idp.{os.environ['AWS_REGION']}.amazonaws.com/{os.environ['AWS_COGNITO_USER_POOL_ID']}"
        ):
            raise CognitoAuthenticationError("Invalid issuer for JWT token")
        if headers["client"] != os.environ["AWS_COGNITO_CLIENT_ID"]:
            raise CognitoAuthenticationError("Invalid client for JWT token")

    @staticmethod
    def _fetch_public_key(kid: str) -> str:
        """Fetches the public key for the given key ID."""
        try:
            return requests.get(
                url=f"https://public-keys.auth.elb.{os.environ['AWS_REGION']}.amazonaws.com/{kid}",
                timeout=5
            ).text
        except requests.RequestException as exc:
            raise CognitoAuthenticationError("Failed to fetch public key for JWT token") from exc
