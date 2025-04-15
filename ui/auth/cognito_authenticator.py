import os
from typing import Any

import streamlit as st

from common.utils import read_secret
from ui.auth.base_authenticator import BaseAuthenticator
from ui.auth.cognito.authenticator import CognitoAuthenticator as CognitoAuth


class CognitoAuthenticator(BaseAuthenticator):
    """
    A class for handling authentication using AWS Cognito in a Streamlit application.
    """

    # def __init__(self):
    # self.aws_region = os.environ["AWS_REGION"]
    # self.aws_alb_arn = read_secret(os.environ["AWS_ALB_ARN"])
    # self.aws_cognito_client_id = read_secret(os.environ["AWS_COGNITO_CLIENT_ID"])
    # self.aws_cognito_domain = os.environ["AWS_COGNITO_DOMAIN"]
    # self.aws_cognito_redirect_uri = os.environ["AWS_COGNITO_REDIRECT_URI"]
    # self.aws_cognito_user_pool_id = read_secret(os.environ["AWS_COGNITO_USER_POOL_ID"])
    # super().__init__()

    def _initialize_authenticator(self) -> Any:
        """
        Initializes the authenticator. This method is not implemented for Cognito.

        Returns:
            Any: Always returns None.
        """
        return CognitoAuth(
            pool_id=read_secret(os.environ["AWS_COGNITO_USER_POOL_ID"]),
            app_client_id=read_secret(os.environ["AWS_COGNITO_CLIENT_ID"]),
            app_client_secret=read_secret(os.environ["AWS_COGNITO_CLIENT_SECRET"]),
            use_cookies=False
        )

    def get_current_user(self) -> str:
        return self.authenticator.get_username()

    def is_authenticated(self) -> bool:
        return self.authenticator.is_logged_in()

    # pylint: disable=unused-argument,fixme
    def login(self, rendered: bool = False) -> bool:
        """
        Handles the login process by validating the user through ALB headers.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        return self.authenticator.login()

    def render_logout(self):
        """
        Renders a logout button in the Streamlit sidebar.
        """
        st.sidebar.button(
            ":material/logout: Logout",
            on_click=self.authenticator.logout,
            key="logout_button",
        )
