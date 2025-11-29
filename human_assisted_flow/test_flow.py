import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add the directory to path so we can import main
sys.path.append(os.path.abspath("."))

from main import ensure_directories, append_to_final_article, get_latest_response

class TestHumanAssistedFlow(unittest.TestCase):
    
    def setUp(self):
        # Create dummy config if needed, but we rely on the real one or mocked one
        pass

    def test_ensure_directories(self):
        ensure_directories()
        self.assertTrue(os.path.exists("screenshots"))
        self.assertTrue(os.path.exists("gemini_output"))
        self.assertTrue(os.path.exists("chatgpt_output"))

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_append_to_final_article(self, mock_file):
        append_to_final_article("Test Content", "Test Phase")
        mock_file.assert_called_with("final_article.md", "a", encoding="utf-8")
        mock_file().write.assert_any_call("\n\n## Phase: Test Phase\n\n")
        mock_file().write.assert_any_call("Test Content")

    def test_get_latest_response_success(self):
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Generated Response"
        
        # Setup query_selector_all to return a list with our element
        mock_page.query_selector_all.return_value = [mock_element]
        
        text, element = get_latest_response(mock_page, ".selector")
        
        self.assertEqual(text, "Generated Response")
        self.assertEqual(element, mock_element)

    def test_get_latest_response_failure(self):
        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = []
        
        text, element = get_latest_response(mock_page, ".selector")
        
        self.assertIsNone(text)
        self.assertIsNone(element)

    @patch("main.sync_playwright")
    @patch("main.pyperclip.copy")
    @patch("builtins.input", return_value="") # Mock user pressing Enter
    @patch("main.get_latest_response")
    def test_main_flow_logic(self, mock_get_response, mock_input, mock_copy, mock_playwright):
        # Mock Playwright context and pages
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch_persistent_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Mock response extraction
        mock_get_response.return_value = ("Mocked Response", MagicMock())
        
        # Import main inside test to avoid early execution
        from main import main
        
        # Run main (we need to limit the loop or mock config to 1 phase to avoid infinite if logic was different)
        # But main iterates over config['phases']. Let's mock config to have 1 phase.
        with patch("main.config", {'browser_config': {'user_data_dir': 'test', 'headless': True, 'gemini_url': '', 'chatgpt_url': ''}, 
                                  'phases': [{'id': 1, 'name': 'Test', 'source': 'gemini', 'target': 'chatgpt', 'prompt_template': 'Test {previous_response}'}],
                                  'selectors': {'gemini': {'input_area': '', 'latest_response': ''}, 'chatgpt': {'input_area': '', 'latest_response': ''}}}):
            main()
            
        # Verify interactions
        self.assertTrue(mock_copy.called)
        self.assertTrue(mock_get_response.called)

if __name__ == "__main__":
    unittest.main()
