from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests


class TestChatbot(BaseTestCases.BaseUIPageTest):
    """Class for testing the Chatbot page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/chatbot.py"

    def test_page_renders_chat_input(self):
        """The page should render without errors and present a chat input."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        self.assertEqual(1, len(at.chat_input), "The chatbot page should render a single chat input")

    def test_asking_a_question_displays_the_answer(self):
        """Submitting a question should display the chatbot's answer and store the conversation."""
        mock_requests = MockRequests(mock_chat_response="There is 1 rental in progress today.")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.chat_input[0].set_value("How many rentals are in progress?")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        rendered = [md.value for md in at.markdown]
        self.assertIn("How many rentals are in progress?", rendered)
        self.assertIn("There is 1 rental in progress today.", rendered)
        self.assertEqual(2, len(at.session_state["chat_messages"]))

    def test_clear_chat_button_disabled_when_conversation_is_empty(self):
        """There is nothing to clear on a fresh page, so the button should be disabled."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        self.assertTrue(at.button(key="clear_chat").disabled, "The clear chat button should start disabled")

    def test_clear_chat_button_removes_the_conversation(self):
        """Clicking clear chat should empty the history and stop rendering the prior messages."""
        mock_requests = MockRequests(mock_chat_response="There is 1 rental in progress today.")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.chat_input[0].set_value("How many rentals are in progress?")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertFalse(at.button(key="clear_chat").disabled, "The clear chat button should enable once a "
                                                               "conversation exists")

        at.button(key="clear_chat").click()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        self.assertEqual([], at.session_state["chat_messages"])
        rendered = [md.value for md in at.markdown]
        self.assertNotIn("How many rentals are in progress?", rendered)
        self.assertNotIn("There is 1 rental in progress today.", rendered)
