# content_recorder/tests/test_views_llm.py

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
import json
from ..models import ContentIdea, ScriptBreakdown

# Ensure settings for LLM are mocked or available for the test
settings.OLLAMA_MODEL_NAME = 'llama3:8b'
settings.OLLAMA_HOST = 'http://localhost:11434'

class ScriptGenerationActionViewTest(TestCase):
    """Tests the ScriptGenerationActionView, mocking the external LLM API."""

    def setUp(self):
        self.client = Client()
        self.idea = ContentIdea.objects.create(
            idea_name="LLM Test Idea",
            raw_content="This content needs to be broken down into a script.",
            status=ContentIdea.StatusChoices.DRAFT
        )
        self.url = reverse('content_recorder:generate_script', args=[self.idea.pk])
        self.detail_url = reverse('content_recorder:detail', args=[self.idea.pk])

        # Define a valid mock JSON response from the LLM
        self.mock_llm_output = {
            "script_breakdown": {
                "title": "LLM Generated Script",
                "scenes": [
                    {"id": 1, "description": "Introduction hook", "word_count": 50},
                    {"id": 2, "description": "Main argument", "word_count": 200},
                ]
            }
        }
        self.mock_llm_response_content = {
            "message": {"content": json.dumps(self.mock_llm_output)}
        }
        
    @patch('requests.post')
    def test_script_generation_success(self, mock_post):
        """Test successful API call and database save."""
        # Configure the mock requests.post object
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = self.mock_llm_response_content
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP errors
        mock_post.return_value = mock_response

        # POST data simulating form submission
        data = {
            'target_platform': 'YouTube Shorts',
            'global_mood': 'Informative',
            'llm_prompt_version': 'V2_Pacing'
        }
        
        response = self.client.post(self.url, data, follow=True)

        # 1. Check HTTP response and redirect
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, "Script breakdown for 'LLM Test Idea' created successfully!")
        
        # 2. Check Database State
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, 'Script')
        self.assertTrue(ScriptBreakdown.objects.filter(idea=self.idea).exists())
        
        breakdown = self.idea.breakdown
        self.assertEqual(breakdown.prompt_used, 'V2_Pacing')
        self.assertEqual(breakdown.target_platform, 'YouTube Shorts')
        self.assertEqual(breakdown.breakdown_data['script_breakdown']['title'], "LLM Generated Script")
        
        # 3. Check API Call details
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]['json']
        self.assertEqual(call_kwargs['model'], settings.OLLAMA_MODEL_NAME)
        self.assertEqual(call_kwargs['response_format']['type'], 'json')
        # Check that the V2 prompt template was used in the user message
        self.assertIn('V2_Pacing', call_kwargs['messages'][1]['content'])


    @patch('requests.post')
    def test_api_connection_error_handling(self, mock_post):
        """Test handling a RequestException (e.g., Ollama server is down)."""
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("Connection refused")

        data = {'target_platform': 'YouTube', 'global_mood': 'Serious', 'llm_prompt_version': 'V1_Analytical'}
        response = self.client.post(self.url, data, follow=True)

        # Should redirect back to detail page and show error
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, "Ollama Connection Error: Could not reach Llama 3.")
        self.assertEqual(self.idea.status, 'draft') # Status should not change


    @patch('requests.post')
    def test_invalid_json_response_handling(self, mock_post):
        """Test handling if the LLM returns non-JSON text."""
        mock_response = MagicMock(status_code=200)
        # LLM outputting garbage text instead of pure JSON
        mock_response.json.return_value = {"message": {"content": "Oops, I forgot the JSON structure."}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        data = {'target_platform': 'TikTok', 'global_mood': 'Funny', 'llm_prompt_version': 'V3_Narrative'}
        response = self.client.post(self.url, data, follow=True)

        # Should redirect back to detail page and show error
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, "LLM returned invalid JSON.")
        self.assertEqual(self.idea.status, 'draft') # Status should not change


    @patch('requests.post')
    @patch('content_recorder.models.ScriptBreakdown.save')
    def test_database_save_failure_handling(self, mock_save, mock_post):
        """Test handling a database error during save (e.g., Data too long)."""
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = self.mock_llm_response_content
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Force the save method to raise a generic Exception (like DataError)
        mock_save.side_effect = Exception("Value too long for field breakdown_data")

        data = {'target_platform': 'Blog', 'global_mood': 'Deep', 'llm_prompt_version': 'V1_Analytical'}
        response = self.client.post(self.url, data, follow=True)

        # Should redirect back to detail page and show error
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, "Database SAVE FAILED for breakdown: Exception: Value too long")
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, 'draft') # Status should not change if transaction fails