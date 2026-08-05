from unittest import TestCase
from unittest.mock import MagicMock, patch

from moto import mock_aws
from streamlit.testing.v1 import AppTest

from ui.auth.cognito.authenticator import CognitoAuthenticator
from ui.auth.cognito.credentials import Credentials
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

    @staticmethod
    def _build_authenticator():
        """Builds an authenticator with cookies disabled, then swaps in a mock cookie manager."""
        authenticator = CognitoAuthenticator(
            pool_id="mock_pool_id",
            app_client_id="us-west-2_123456789",
            app_client_secret="mock_app_client_secret",
            use_cookies=False,
        )
        authenticator.cookie_manager = MagicMock()
        return authenticator

    @staticmethod
    def _mock_credentials():
        return Credentials(
            id_token="mock_id_token",
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            expires_in=3600,
            token_type="Bearer",
        )

    def test_login_from_cookies_empty_read_does_not_reset(self):
        """An empty cookie read (component not ready) must not wipe the cookies."""
        authenticator = self._build_authenticator()
        authenticator.cookie_manager.load_credentials.return_value = None

        with patch.object(CognitoAuthenticator, "_set_state_login") as mock_set_state:
            logged_in = authenticator._login_from_cookies()

        self.assertFalse(logged_in)
        mock_set_state.assert_not_called()
        authenticator.cookie_manager.reset_credentials.assert_not_called()

    def test_login_from_cookies_valid_restores_session(self):
        """Valid cookie credentials restore the session without resetting cookies."""
        authenticator = self._build_authenticator()
        authenticator.cookie_manager.load_credentials.return_value = self._mock_credentials()

        with patch.object(CognitoAuthenticator, "_set_state_login", return_value=True):
            logged_in = authenticator._login_from_cookies()

        self.assertTrue(logged_in)
        authenticator.cookie_manager.reset_credentials.assert_not_called()

    def test_login_from_cookies_invalid_does_not_reset_cookies(self):
        """Cookie credentials that fail verification are left alone (not cleared).

        Calling reset_credentials() here would lazily mount the stx.CookieManager iframe
        on an otherwise passive page load, racing with the rest of the script (e.g. the
        login form rendering later in the same run) and causing the "Missing Submit
        Button" flash. Stale credentials are harmless and get overwritten on next login.
        """
        authenticator = self._build_authenticator()
        authenticator.cookie_manager.load_credentials.return_value = self._mock_credentials()

        with patch.object(CognitoAuthenticator, "_set_state_login", return_value=False):
            logged_in = authenticator._login_from_cookies()

        self.assertFalse(logged_in)
        authenticator.cookie_manager.reset_credentials.assert_not_called()

    def test_login_from_cookies_ignored_after_logout(self):
        """After an explicit logout, stale request cookies must not log the user back in."""
        authenticator = self._build_authenticator()
        authenticator.session_manager = MagicMock()
        authenticator.session_manager.is_logged_out.return_value = True

        logged_in = authenticator._login_from_cookies()

        self.assertFalse(logged_in)
        authenticator.cookie_manager.load_credentials.assert_not_called()
        authenticator.cookie_manager.reset_credentials.assert_not_called()

    def test_set_state_login_persist_false_skips_cookie_write(self):
        """Restoring a session must not re-write cookies (which would render the cookie
        component and leave empty space at the top of every page)."""
        authenticator = self._build_authenticator()
        with patch(
                "ui.auth.cognito.authenticator.verify_access_token",
                return_value=({"username": "u"}, MagicMock(email="u@example.com")),
        ), patch.object(CognitoAuthenticator, "_get_user_groups", return_value=[]):
            logged_in = authenticator._set_state_login(self._mock_credentials(), persist=False)

        self.assertTrue(logged_in)
        authenticator.cookie_manager.set_credentials.assert_not_called()

    def test_set_state_login_persist_true_writes_cookie(self):
        """A fresh login must persist the credentials to cookies, and must wait for the
        cookie component's browser round-trip to complete before returning.

        Without this wait, a caller that reruns immediately afterwards (as login() does)
        tears down the cookie-setting component before its document.cookie write actually
        lands in the browser -- confirmed by manual reproduction -- silently losing the
        session, so a refresh right after logging in logs the user back out.
        """
        authenticator = self._build_authenticator()
        with patch(
                "ui.auth.cognito.authenticator.verify_access_token",
                return_value=({"username": "u"}, MagicMock(email="u@example.com")),
        ), patch.object(CognitoAuthenticator, "_get_user_groups", return_value=[]), patch(
            "ui.auth.cognito.authenticator.time.sleep"
        ) as mock_sleep:
            logged_in = authenticator._set_state_login(self._mock_credentials(), persist=True)

        self.assertTrue(logged_in)
        authenticator.cookie_manager.set_credentials.assert_called_once()
        mock_sleep.assert_called_once()

    def test_set_state_login_persist_false_does_not_wait(self):
        """Restoring a session doesn't write cookies, so there's nothing to wait for."""
        authenticator = self._build_authenticator()
        with patch(
                "ui.auth.cognito.authenticator.verify_access_token",
                return_value=({"username": "u"}, MagicMock(email="u@example.com")),
        ), patch.object(CognitoAuthenticator, "_get_user_groups", return_value=[]), patch(
            "ui.auth.cognito.authenticator.time.sleep"
        ) as mock_sleep:
            logged_in = authenticator._set_state_login(self._mock_credentials(), persist=False)

        self.assertTrue(logged_in)
        mock_sleep.assert_not_called()

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
