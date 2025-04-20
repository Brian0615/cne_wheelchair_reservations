import os
import time
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import boto3
import pycognito  # type: ignore
import streamlit as st
from pycognito import AWSSRP

from common.logger import initialize_logger
from common.utils import read_secret
from ui.auth.cognito.cookie_manager import CognitoAuthCookieManager, CognitoAuthCookieManagerNoop
from ui.auth.cognito.credentials import Credentials
from ui.auth.cognito.exceptions import TokenVerificationException
from ui.auth.cognito.session_state_manager import CognitoAuthSessionStateManager
from ui.auth.cognito.utils import verify_access_token

logger = initialize_logger()


class CognitoAuthenticatorBase(ABC):
    """Base class for cognito base authenticators.

    Args:
        pool_id: Cognito pool ID.
        app_client_id: Cognito Application client ID.
        app_client_secret: Cognito Application client secret.
        boto_client: optional boto3 CognitoIdentityProvider ("cognito-idp") client
        use_cookies: use cookies to save credentials.
    """

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            pool_id: str,
            app_client_id: str,
            app_client_secret: Optional[str] = None,
            boto_client: Optional[Any] = None,
            use_cookies: bool = True,
    ):
        self.pool_region = pool_id.split("_")[0]
        self.client = boto_client or boto3.client(
            "cognito-idp",
            aws_access_key_id=read_secret(os.environ["AWS_ACCESS_KEY_ID"]),
            aws_secret_access_key=read_secret(os.environ["AWS_SECRET_ACCESS_KEY"]),
            region_name=self.pool_region
        )
        self.pool_id = pool_id
        self.app_client_id = app_client_id
        self.app_client_secret = app_client_secret

        self.session_manager = CognitoAuthSessionStateManager()
        self.cookie_manager = (
            CognitoAuthCookieManager() if use_cookies else CognitoAuthCookieManagerNoop()
        )

    def _get_user_groups(self, username: str) -> list[str]:
        """
        Retrieves the groups that a user belongs to.

        Args:
            username (str): The username of the user.

        Returns:
            list[str]: A list of group names the user belongs to.
        """
        try:
            response = self.client.admin_list_groups_for_user(
                UserPoolId=self.pool_id,
                Username=username
            )
            groups = [group["GroupName"] for group in response.get("Groups", [])]
            return groups
        except self.client.exceptions.UserNotFoundException:
            logger.error("User not found: %s", username)
            return []
        except Exception as e:
            logger.exception("Error retrieving groups for user %s: %s", username, e)
            raise

    def _login_from_cookies(self) -> bool:
        credentials = self.cookie_manager.load_credentials()
        logged_in = False
        if credentials:
            logger.info("Found credentials in cookies, trying to log in ...")
            logged_in = self._set_state_login(credentials=credentials)
        if not logged_in:
            logger.info("Clearing cookie credentials")
            self.cookie_manager.reset_credentials()
        return logged_in

    def _set_state_login(self, credentials: Credentials) -> bool:
        try:
            claims, user = verify_access_token(
                self.pool_id,
                self.app_client_id,
                self.pool_region,
                credentials.access_token
            )
        except TokenVerificationException as exc:
            logger.exception(exc)
            claims = None
        if claims:
            self.session_manager.set_credentials(credentials=credentials)
            try:
                email = user.email
            except AttributeError:
                email = None
            groups = self._get_user_groups(username=claims["username"])
            self.session_manager.set_logged_in(username=claims["username"], email=email, groups=groups)
            self.cookie_manager.set_credentials(credentials=credentials)
            logger.info("Successfully logged in")
            return True
        logger.info("Could not log in")
        self._set_state_logout()
        return False

    def _set_state_logout(self) -> None:
        self.session_manager.reset_credentials()
        self.session_manager.set_logged_out()

    def _login_from_saved_credentials(self) -> bool:
        logged_in = False
        logger.info("_login_from_saved_credentials")
        session_state_credentials = self.session_manager.load_credentials()
        if session_state_credentials:
            logged_in = self._set_state_login(credentials=session_state_credentials)
            logger.info("Logged in with session state credentials: %s", logged_in)
        else:
            logger.info("No credentials in session state")
        if not logged_in:
            logger.info("Logging in from cookies")
            logged_in = self._login_from_cookies()
            logger.info("Logged in with cookies credentials: %s", logged_in)
        logger.info("_login_from_saved_credentials finished")
        return logged_in

    @abstractmethod
    def login(self) -> bool:
        """Logs in the user, showing UI elements if necessary.

        Returns: True if the user was successfully logged in.
        """

    def logout(self):
        """Logs out the currently logged user."""
        logger.info("Logout")
        self._set_state_logout()
        self.cookie_manager.reset_credentials()

    def is_logged_in(self) -> bool:
        """Returns whether the current user is logged in."""
        return self.session_manager.is_logged_in()

    def get_username(self) -> Optional[str]:
        """Gets the user name of the current user, if they are logged in."""
        return self.session_manager.get_username()

    def get_user_groups(self) -> List[str]:
        """Get the groups of the current user, if they are logged in."""
        return self.session_manager.get_groups()

    def get_email(self) -> Optional[str]:
        """Gets the email of the current user, if they are logged in."""
        return self.session_manager.get_email()

    def get_credentials(self) -> Optional[Credentials]:
        """Retrieve user credentials"""
        return self.session_manager.load_credentials()


class CognitoAuthenticator(CognitoAuthenticatorBase):
    """Authenticates the user with Cognito using custom streamlit UI elements."""

    def _show_login_form(self, placeholder):
        with placeholder:
            cols = st.columns([1, 3, 1])
            with cols[1]:
                with st.form("login_form"):
                    st.subheader("Login")
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    login_submitted = st.form_submit_button("Login")
                    status_container = st.container()

        return login_submitted, username, password, status_container

    def _show_password_reset_form(self, placeholder):
        username, password = self.session_manager.reset_password_credentials()
        with placeholder:
            cols = st.columns([1, 3, 1])
            with cols[1]:
                with st.form("reset_password_form"):
                    st.subheader("Reset Password")
                    username = st.text_input(
                        "Username",
                        value=username,
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        value=password,
                        disabled=True,
                    )
                    new_password = st.text_input("New Password", type="password")
                    confirm_new_password = st.text_input(
                        "Confirm Password", type="password"
                    )
                    password_reset_submitted = st.form_submit_button("Reset Password")
                    status_container = st.container()

        return (
            password_reset_submitted,
            username,
            password,
            new_password,
            confirm_new_password,
            status_container,
        )

    def _login(self, username, password):
        aws_srp_args = {
            "client": self.client,
            "pool_id": self.pool_id,
            "client_id": self.app_client_id,
            "username": username,
            "password": password,
        }

        if self.app_client_secret is not None:
            aws_srp_args["client_secret"] = self.app_client_secret

        aws_srp = AWSSRP(**aws_srp_args)

        try:
            tokens = aws_srp.authenticate_user()

        except pycognito.exceptions.ForceChangePasswordException:
            logger.info("Force password reset")
            self._set_reset_password_session(username, password)
            return False

        except self.client.exceptions.PasswordResetRequiredException:
            logger.info("Password reset required")
            self._set_state_logout()
            return False

        except self.client.exceptions.NotAuthorizedException:
            logger.info("Login not authorized")
            self._set_state_logout()
            return False

        except Exception as e:
            logger.exception("Unknown exception during login: %s", e)
            self._set_state_logout()
            raise e

        else:
            credentials = Credentials.from_tokens(tokens)
            return self._set_state_login(credentials=credentials)

    def _set_reset_password_session(
            self,
            reset_password_username: str,
            reset_password_password: str
    ) -> None:
        logger.info("Set password reset state")
        self.session_manager.set_reset_password_session(
            reset_password_username, reset_password_password
        )

    def _reset_password(self, username, password, new_password) -> bool:
        aws_srp_args = {
            "client": self.client,
            "pool_id": self.pool_id,
            "client_id": self.app_client_id,
            "username": username,
            "password": password,
        }

        if self.app_client_secret is not None:
            aws_srp_args["client_secret"] = self.app_client_secret

        aws_srp = AWSSRP(**aws_srp_args)

        try:
            tokens = aws_srp.set_new_password_challenge(new_password=new_password)

        except self.client.exceptions.NotAuthorizedException:
            logger.info("Password reset not authorized")
            self._set_state_logout()
            return False

        except Exception as e:
            logger.exception("Unknown exception during password reset: %s", e)
            self._set_state_logout()
            raise e

        else:
            credentials = Credentials.from_tokens(tokens)
            logged_in = self._set_state_login(credentials=credentials)
            if logged_in:
                self.session_manager.clear_reset_password_session()
            return logged_in

    # pylint: disable=too-many-return-statements
    def login(self) -> bool:

        form_placeholder = st.empty()

        if self.session_manager.is_reset_password_session():
            logger.info("Password reset is requested")
            (
                password_reset_submitted,
                username,
                password,
                new_password,
                confirm_new_password,
                status_container,
            ) = self._show_password_reset_form(form_placeholder)
            if not password_reset_submitted:
                return False

            if not new_password:
                status_container.error("New password is empty")
                return False

            if new_password != confirm_new_password:
                status_container.error("New password mismatch")
                return False

            is_password_reset = self._reset_password(
                username=username,
                password=password,
                new_password=new_password,
            )
            if not is_password_reset:
                status_container.error("Failed to reset password")
                return False

            status_container.success("Logged in")
            st.rerun()

        logger.info("Trying to log in from saved credentials ...")
        logged_in = self._login_from_saved_credentials()
        if logged_in:
            logger.info("Success")
            return True

        logger.info("Showing login form ...")
        # login
        login_submitted, username, password, status_container = self._show_login_form(
            form_placeholder
        )
        if not login_submitted:
            logger.info("Login button was not pushed yet")
            return False

        is_logged_in = self._login(
            username=username,
            password=password,
        )
        logger.info("_login was called, result: {%s}", is_logged_in)

        if self.session_manager.is_reset_password_session():
            status_container.info("Password reset is required")
            time.sleep(1.5)
            st.rerun()

        if not is_logged_in:
            status_container.error("Invalid username or password")
            return False

        status_container.success("Logged in")
        st.rerun()
