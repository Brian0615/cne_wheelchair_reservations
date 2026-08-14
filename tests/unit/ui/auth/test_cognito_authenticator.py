from unittest import TestCase
from unittest.mock import patch

from ui.auth.cognito_authenticator import CognitoAuthenticator


class TestCognitoAuthenticatorRoleChecks(TestCase):
    """Tests for CognitoAuthenticator.is_admin_user/is_editor_user/is_display_user."""

    def test_is_display_user_true_with_display_group(self):
        instance = object.__new__(CognitoAuthenticator)
        with patch.object(CognitoAuthenticator, "get_current_user_groups", return_value=["cne-display"]):
            self.assertTrue(instance.is_display_user())

    def test_is_display_user_false_without_display_group(self):
        instance = object.__new__(CognitoAuthenticator)
        with patch.object(CognitoAuthenticator, "get_current_user_groups", return_value=["cne-admin"]):
            self.assertFalse(instance.is_display_user())

    def test_is_display_user_false_with_no_groups(self):
        instance = object.__new__(CognitoAuthenticator)
        with patch.object(CognitoAuthenticator, "get_current_user_groups", return_value=[]):
            self.assertFalse(instance.is_display_user())

    def test_is_display_user_true_for_admin_and_display(self):
        """is_display_user() is a pure group check; admin does not exclude it -- the
        'admin wins' precedence is main.py's responsibility, not this method's."""
        instance = object.__new__(CognitoAuthenticator)
        with patch.object(
                CognitoAuthenticator, "get_current_user_groups", return_value=["cne-admin", "cne-display"]
        ):
            self.assertTrue(instance.is_display_user())
