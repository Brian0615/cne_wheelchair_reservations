import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ui.auth.local_authenticator import LocalAuthenticator


class TestLocalAuthenticatorInitialization(TestCase):
    """Tests for LocalAuthenticator initialization."""

    def test_authenticate_initialized_with_zero_sleep_time(self):
        """_initialize_authenticator passes login_sleep_time=0 to prevent the
        stx.CookieManager iframe from triggering a mid-render rerun that causes
        a 'Missing Submit Button' flash on first page load.

        streamlit-authenticator stores this kwarg in self.attrs and reads it as
        self.attrs.get('login_sleep_time', PRE_LOGIN_SLEEP_TIME) inside login().
        Setting it to 0 eliminates the 0.7 s sleep that previously allowed the
        CookieManager JS callback to fire while the form was partially rendered.
        """
        mock_config = {"cookie": {"name": "test_cookie", "key": "test_key", "expiry_days": 30}}
        with patch("ui.auth.local_authenticator.st_auth.Authenticate") as mock_authenticate_class, \
             patch.object(LocalAuthenticator, "_load_config", return_value=mock_config), \
             patch.dict(os.environ, {"AUTH_CONFIG_PATH": "/fake/path"}):
            instance = object.__new__(LocalAuthenticator)
            instance._initialize_authenticator()

            mock_authenticate_class.assert_called_once_with(
                credentials="/fake/path",
                cookie_name="test_cookie",
                cookie_key="test_key",
                cookie_expiry_days=30,
                auto_hash=True,
                login_sleep_time=0,
            )


class TestLocalAuthenticatorLogging(TestCase):
    """Tests that LocalAuthenticator logs auth failures, previously invisible server-side."""

    def test_load_config_logs_and_reraises_on_missing_file(self):
        instance = object.__new__(LocalAuthenticator)
        with patch.dict(os.environ, {"AUTH_CONFIG_PATH": "/nonexistent/path"}):
            with self.assertLogs("ui.auth.local_authenticator", level="ERROR"):
                with self.assertRaises(FileNotFoundError):
                    instance._load_config()

    def test_login_logs_warning_on_incorrect_credentials(self):
        instance = object.__new__(LocalAuthenticator)
        instance.authenticator = MagicMock()
        with patch("ui.auth.local_authenticator.st") as mock_st:
            mock_st.session_state = {"authentication_status": False}
            with self.assertLogs("ui.auth.local_authenticator", level="WARNING"):
                self.assertFalse(instance.login())

    def test_login_logs_exception_on_unexpected_error(self):
        instance = object.__new__(LocalAuthenticator)
        instance.authenticator = MagicMock()
        instance.authenticator.login.side_effect = RuntimeError("boom")
        with patch("ui.auth.local_authenticator.st") as mock_st:
            with self.assertLogs("ui.auth.local_authenticator", level="ERROR"):
                self.assertFalse(instance.login())
            mock_st.error.assert_called_once()


class TestLocalAuthenticatorRoleChecks(TestCase):
    """Tests for LocalAuthenticator.is_admin_user/is_editor_user/is_display_user."""

    def test_is_display_user_true_with_display_role(self):
        instance = object.__new__(LocalAuthenticator)
        with patch.object(LocalAuthenticator, "get_current_user_groups", return_value=["display"]):
            self.assertTrue(instance.is_display_user())

    def test_is_display_user_false_without_display_role(self):
        instance = object.__new__(LocalAuthenticator)
        with patch.object(LocalAuthenticator, "get_current_user_groups", return_value=["admin"]):
            self.assertFalse(instance.is_display_user())

    def test_is_display_user_false_with_no_roles(self):
        instance = object.__new__(LocalAuthenticator)
        with patch.object(LocalAuthenticator, "get_current_user_groups", return_value=[]):
            self.assertFalse(instance.is_display_user())

    def test_is_display_user_true_for_admin_and_display(self):
        """is_display_user() is a pure role check; admin does not exclude it -- the
        'admin wins' precedence is main.py's responsibility, not this method's."""
        instance = object.__new__(LocalAuthenticator)
        with patch.object(LocalAuthenticator, "get_current_user_groups", return_value=["admin", "display"]):
            self.assertTrue(instance.is_display_user())
