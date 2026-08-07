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

    def test_asking_a_question_displays_the_model_used(self):
        """The model that answered should be shown under the response, and persist across reruns."""
        mock_requests = MockRequests(mock_chat_response="answer", mock_chat_model="gemini-2.5-flash-lite")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.chat_input[0].set_value("A question")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        self.assertEqual("gemini-2.5-flash-lite", at.session_state["chat_messages"][-1]["model"])
        captions = [c.value for c in at.caption]
        self.assertIn("Model: gemini-2.5-flash-lite", captions)

    def test_cumulative_tokens_start_at_zero(self):
        """A fresh conversation should report zero cumulative tokens used, for every category."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        expected = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "total_tokens": 0}
        self.assertEqual(expected, at.session_state["chat_token_usage"])
        captions = [c.value for c in at.caption]
        self.assertIn(
            "Tokens used this conversation — input: 0, output: 0, cache: 0, total: 0", captions
        )

    def test_cumulative_tokens_accumulate_across_questions(self):
        """Each answer's token usage (by category) should add to the running conversation totals."""
        mock_requests = MockRequests(
            mock_chat_response="answer",
            mock_chat_input_tokens=100,
            mock_chat_output_tokens=20,
            mock_chat_cache_read_tokens=30,
        )
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.chat_input[0].set_value("First question")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(
            {"input_tokens": 100, "output_tokens": 20, "cache_read_tokens": 30, "total_tokens": 120},
            at.session_state["chat_token_usage"],
        )
        captions = [c.value for c in at.caption]
        self.assertIn(
            "Tokens used this conversation — input: 100, output: 20, cache: 30, total: 120", captions
        )

        at.chat_input[0].set_value("Second question")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(
            {"input_tokens": 200, "output_tokens": 40, "cache_read_tokens": 60, "total_tokens": 240},
            at.session_state["chat_token_usage"],
        )
        captions = [c.value for c in at.caption]
        self.assertIn(
            "Tokens used this conversation — input: 200, output: 40, cache: 60, total: 240", captions
        )

    def test_clear_chat_resets_cumulative_tokens(self):
        """Clearing the conversation should also reset every cumulative token count to zero."""
        mock_requests = MockRequests(
            mock_chat_response="answer", mock_chat_input_tokens=100, mock_chat_output_tokens=20
        )
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.chat_input[0].set_value("A question")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(120, at.session_state["chat_token_usage"]["total_tokens"])

        at.button(key="clear_chat").click()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        expected = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "total_tokens": 0}
        self.assertEqual(expected, at.session_state["chat_token_usage"])
        captions = [c.value for c in at.caption]
        self.assertIn(
            "Tokens used this conversation — input: 0, output: 0, cache: 0, total: 0", captions
        )

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
