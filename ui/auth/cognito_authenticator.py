import os
from typing import Any
from urllib.parse import urlencode

import jwt
import requests
import streamlit as st

from common.utils import read_secret
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

    def __init__(self):
        self.aws_region = os.environ["AWS_REGION"]
        self.aws_alb_arn = read_secret(os.environ["AWS_ALB_ARN"])
        self.aws_cognito_client_id = read_secret(os.environ["AWS_COGNITO_CLIENT_ID"])
        self.aws_cognito_domain = os.environ["AWS_COGNITO_DOMAIN"]
        self.aws_cognito_redirect_uri = os.environ["AWS_COGNITO_REDIRECT_URI"]
        self.aws_cognito_user_pool_id = read_secret(os.environ["AWS_COGNITO_USER_POOL_ID"])
        super().__init__()

    def _initialize_authenticator(self) -> Any:
        """
        Initializes the authenticator. This method is not implemented for Cognito.

        Returns:
            Any: Always returns None.
        """
        return None

    # pylint: disable=unused-argument,fixme
    def login(self, rendered: bool = False) -> bool:
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

    def _on_logout(self, *args, **kwargs):
        """
        Handles the logout process by clearing session state and redirecting the user.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        st.session_state.clear()

        # logout user from Cognito
        logout_url = (
            f"{self.aws_cognito_domain}/logout?" +
            urlencode({
                "client_id": self.aws_cognito_client_id,
                "logout_uri": self.aws_cognito_redirect_uri,
            })
        )
        st.write(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)

    def _get_expected_cognito_issuer(self) -> str:
        return f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.aws_cognito_user_pool_id}"

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
        jwt_headers = jwt.get_unverified_header(encoded_jwt)
        self._validate_jwt_headers(headers=jwt_headers)

        # Step 2: Get the key id from JWT headers (the kid field), and get the public key
        kid = jwt_headers['kid']
        pub_key = self._fetch_public_key(kid=kid)

        # Step 3: Get the payload
        try:
            payload = jwt.decode(encoded_jwt, pub_key, algorithms=['ES256'], issuer=self._get_expected_cognito_issuer())
        except jwt.InvalidIssuerError as exc:
            raise CognitoAuthenticationError("Invalid issuer for JWT token") from exc

        return payload["username"]

    def _validate_jwt_headers(self, headers: dict):
        """Validates JWT headers for signer, issuer, and client."""
        if headers["signer"] != self.aws_alb_arn:
            raise CognitoAuthenticationError("Invalid signer for JWT token")
        if headers["iss"] != self._get_expected_cognito_issuer():
            raise CognitoAuthenticationError("Invalid issuer for JWT token")
        if headers["client"] != self.aws_cognito_client_id:
            raise CognitoAuthenticationError("Invalid client for JWT token")

    def _fetch_public_key(self, kid: str) -> str:
        """Fetches the public key for the given key ID."""
        try:
            return requests.get(
                url=f"https://public-keys.auth.elb.{self.aws_region}.amazonaws.com/{kid}",
                timeout=5,
            ).text
        except requests.RequestException as exc:
            raise CognitoAuthenticationError("Failed to fetch public key for JWT token") from exc
