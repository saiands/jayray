# content_recorder/tests/test_views_record.py

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from ..models import ContentIdea
from ..views import extract_text_from_file

class ContentRecordViewTest(TestCase):
    """Tests the ContentRecordView (GET and POST)."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_recorder:record')
        # Define the redirect target name
        self.detail_url_name = 'content_recorder:detail'

    def test_get_request(self):
        """Ensure GET request returns 200 and uses correct template."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'content_recorder/record_content.html')

    def test_post_pasted_content_success(self):
        """Test successful submission via pasted content."""
        data = {
            'idea_name': 'Pasted Idea',
            'raw_content': 'This is sample content pasted directly into the form.'
        }
        response = self.client.post(self.url, data, follow=True)
        
        self.assertEqual(ContentIdea.objects.count(), 1)
        idea = ContentIdea.objects.first()
        
        self.assertRedirects(response, reverse(self.detail_url_name, args=[idea.pk]))
        self.assertContains(response, "Content Idea 'Pasted Idea' saved successfully!")
        self.assertEqual(idea.raw_content, data['raw_content'])
        self.assertEqual(idea.source.source_type, 'text')
    
    @patch('content_recorder.views.extract_text_from_file')
    def test_post_uploaded_file_success(self, mock_extract):
        """Test successful submission via an uploaded file."""
        mock_extract.return_value = "Content extracted from file."
        
        # Create a dummy file object
        test_file = SimpleUploadedFile("test.txt", b"dummy content", content_type="text/plain")
        
        data = {
            'idea_name': 'File Upload Idea',
            'uploaded_file': test_file
        }
        response = self.client.post(self.url, data, follow=True)
        
        self.assertEqual(ContentIdea.objects.count(), 1)
        idea = ContentIdea.objects.first()

        self.assertRedirects(response, reverse(self.detail_url_name, args=[idea.pk]))
        self.assertEqual(idea.raw_content, "Content extracted from file.")
        self.assertEqual(idea.source.source_type, 'file')

    def test_post_empty_submission_failure(self):
        """Test submission fails if both fields are empty."""
        data = {'idea_name': 'Empty Idea', 'raw_content': ''}
        response = self.client.post(self.url, data, follow=True)
        
        self.assertEqual(ContentIdea.objects.count(), 0)
        self.assertContains(response, "Submission failed: Please paste content or upload a valid file.")


# --- Test Helper Function: extract_text_from_file ---

class FileParsingTest(TestCase):
    """Tests the utility function for extracting text from files."""

    def test_txt_file_parsing(self):
        """Test basic .txt file content extraction."""
        test_file = SimpleUploadedFile("doc.txt", b"Hello World", content_type="text/plain")
        text = extract_text_from_file(test_file)
        self.assertEqual(text, "Hello World")
        
    def test_empty_file_handling(self):
        """Test handling of a zero-byte file."""
        test_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")
        text = extract_text_from_file(test_file)
        self.assertIn("ERROR: Empty file uploaded.", text)

    # Use unittest.mock to simulate successful/failed library operations
    @patch('content_recorder.views.Document')
    def test_docx_file_parsing(self, MockDocument):
        """Test .docx file parsing using the mocked python-docx library."""
        # Setup mock document object to return paragraphs
        mock_doc_instance = MockDocument.return_value
        mock_doc_instance.paragraphs = [
            MagicMock(text="First paragraph."),
            MagicMock(text="Second paragraph.")
        ]
        
        test_file = SimpleUploadedFile("doc.docx", b"dummy docx bytes", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        text = extract_text_from_file(test_file)
        
        self.assertEqual(text, "First paragraph.\nSecond paragraph.")

    @patch('content_recorder.views.PdfReader')
    def test_pdf_file_parsing(self, MockPdfReader):
        """Test .pdf file parsing using the mocked pypdf library."""
        # Setup mock reader instance
        mock_reader_instance = MockPdfReader.return_value
        
        # Setup mock pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page one content."
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page two content."
        
        mock_reader_instance.pages = [mock_page1, mock_page2]
        
        test_file = SimpleUploadedFile("doc.pdf", b"dummy pdf bytes", content_type="application/pdf")
        text = extract_text_from_file(test_file)
        
        expected_text = "Page one content.\nPage two content.\n"
        self.assertEqual(text, expected_text)