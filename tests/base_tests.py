import unittest
from unittest.mock import Mock

import streamlit as st
from streamlit.testing.v1 import AppTest

from ui.src import auth_utils


class BaseTestCases:
    class BaseUIPageTest(unittest.TestCase):

        def setUp(self):
            self.page_path = None

        def test_unauthenticated_user(self):
            """Test if unauthenticated user is redirected to login page."""
            # mock the switch_page method so we can check whether the user was redirected to login
            auth_utils.initialize_authenticator = Mock()
            st.switch_page = Mock()

            at = AppTest.from_file(self.page_path)
            at.run()
            st.switch_page.assert_called_once_with("ui/ui_pages/login.py")
