from unittest import TestCase
from unittest.mock import MagicMock, patch

from moto import mock_aws
from streamlit.testing.v1 import AppTest

from ui.auth.cognito.authenticator import CognitoAuthenticator
from ui.auth.cognito.session_state_manager import CognitoAuthSessionStateManager


# pylint: disable=import-outside-toplevel, reimported
def run_login():
    """Function to run the login process in Streamlit AppTest."""
    from ui.auth.cognito.authenticator import CognitoAuthenticator as CognitoAuth

    authenticator = CognitoAuth(
        pool_id="mock_pool_id",
        app_client_id="us-west-2_123456789",
        app_client_secret="mock_app_client_secret",
        use_cookies=False
    )
    authenticator.login()


# pylint: disable=no-member
@mock_aws
class TestCognitoAuthenticator(TestCase):
    """Test cases for CognitoAuthenticator class."""

    def test_login_successful(self):
        """Test successful login with valid credentials."""
        with patch.object(
                CognitoAuthSessionStateManager,
                "is_reset_password_session",
                return_value=False
        ):
            with patch.multiple(
                    CognitoAuthenticator,
                    _login_from_saved_credentials=MagicMock(return_value=False),
                    _login=MagicMock(return_value=True)
            ):
                at = AppTest.from_function(run_login)
                at.run()
                self.assertEqual(len(at.button), 1, "Login button should be rendered.")
                self.assertEqual(len(at.text_input), 2,
                                 "Two text inputs should be rendered for username and password.")

                at.text_input("cognito_login_form_username").set_value("test_user")
                at.text_input("cognito_login_form_password").set_value("test_password")
                at.button("FormSubmitter:login_form-Login").click()
                with patch("streamlit.rerun") as mock_rerun:
                    at.run()
                    self.assertEqual(at.success[0].value, "Logged in")
                    mock_rerun.assert_called_once()

    def test_login_incorrect_credentials(self):
        """Test login with incorrect credentials."""
        with patch.object(
                CognitoAuthSessionStateManager,
                "is_reset_password_session",
                return_value=False
        ):
            with patch.multiple(
                    CognitoAuthenticator,
                    _login_from_saved_credentials=MagicMock(return_value=False),
                    _login=MagicMock(return_value=False)
            ):
                at = AppTest.from_function(run_login)
                at.run()
                at.text_input("cognito_login_form_username").set_value("wrong_user")
                at.text_input("cognito_login_form_password").set_value("wrong_password")
                at.button("FormSubmitter:login_form-Login").click()
                with patch("streamlit.rerun") as mock_rerun:
                    at.run()
                    self.assertEqual(at.error[0].value, "Invalid username or password")
                    mock_rerun.assert_not_called()

    def test_login_no_credentials(self):
        """Test that the login fails when no credentials are provided."""
        with  patch.object(
                CognitoAuthSessionStateManager,
                "is_reset_password_session",
                return_value=False
        ):
            with patch.multiple(
                    CognitoAuthenticator,
                    _login_from_saved_credentials=MagicMock(return_value=False),
                    _login=MagicMock(return_value=False)
            ):
                at = AppTest.from_function(run_login)
                at.run()
                at.button("FormSubmitter:login_form-Login").click()
                with patch("streamlit.rerun") as mock_rerun:
                    at.run()
                    self.assertEqual(at.error[0].value, "Username and/or password is empty")
                    mock_rerun.assert_not_called()
