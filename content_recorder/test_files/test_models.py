# content_recorder/tests/test_models.py

from django.test import TestCase
from django.contrib.auth.models import User
from ..models import ContentIdea, ContentSource, IdeaLog, ScriptBreakdown

class ModelIntegrityTest(TestCase):
    """Tests the integrity and relationships of core data models."""
    
    def setUp(self):
        # Create a test user for log entries
        self.user = User.objects.create_user(username='testuser', password='password')
        # Create a base Idea object
        self.idea = ContentIdea.objects.create(
            idea_name="Base Model Test Idea",
            raw_content="This is raw content.",
            status=ContentIdea.StatusChoices.DRAFT
        )

    def test_content_idea_creation(self):
        """Ensure ContentIdea is created with correct fields and status."""
        self.assertEqual(self.idea.idea_name, "Base Model Test Idea")
        self.assertEqual(self.idea.status, 'draft')
        self.assertTrue(self.idea.pk is not None)

    def test_content_source_link(self):
        """Ensure ContentSource links correctly to ContentIdea."""
        source = ContentSource.objects.create(
            idea=self.idea,
            source_type=ContentSource.SourceType.TEXT,
            source_data="Pasted Text Data"
        )
        self.assertEqual(source.idea, self.idea)
        self.assertEqual(source.source_type, ContentSource.SourceType.TEXT)

    def test_idea_log_creation(self):
        """Ensure IdeaLog records actions correctly."""
        log = IdeaLog.objects.create(
            idea=self.idea,
            user=self.user,
            action="Status changed"
        )
        self.assertEqual(log.idea, self.idea)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "Status changed")

    def test_script_breakdown_relationship(self):
        """Test the one-to-one relationship between Idea and Breakdown."""
        test_data = {"scenes": [{"id": 1, "description": "Intro"}]}
        breakdown = ScriptBreakdown.objects.create(
            idea=self.idea,
            breakdown_data=test_data,
            prompt_used='V1_Analytical'
        )
        # Check reverse relationship
        self.assertEqual(self.idea.breakdown, breakdown)
        # Check JSON field access
        self.assertEqual(self.idea.breakdown.breakdown_data['scenes'][0]['description'], "Intro")