from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import Profile

from .models import TransferRumour


class TransferRumourTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(username="admin_user", password="pass123")
        Profile.objects.create(user=self.admin_user, role="admin")

        self.analyst_user = self.User.objects.create_user(username="analyst_user", password="pass123")
        Profile.objects.create(user=self.analyst_user, role="analyst")

        self.basic_user = self.User.objects.create_user(username="basic_user", password="pass123")
        Profile.objects.create(user=self.basic_user, role="basic")

    def test_slug_generated_and_unique(self):
        rumour1 = TransferRumour.objects.create(
            title="Sensational Signing",
            summary="Rumour summary",
            content="Full rumour content",
            author=self.admin_user,
        )
        rumour2 = TransferRumour.objects.create(
            title="Sensational Signing",
            summary="Another summary",
            content="Another content",
            author=self.admin_user,
        )
        self.assertNotEqual(rumour1.slug, "")
        self.assertNotEqual(rumour2.slug, "")
        self.assertNotEqual(rumour1.slug, rumour2.slug)

    def test_ajax_create_success_for_privileged_user(self):
        self.client.force_login(self.analyst_user)
        url = reverse("transfer_rumour:create")
        payload = {
            "title": "Fresh Transfer Rumour",
            "summary": "Short summary",
            "content": "Detailed rumour information",
            "source_url": "https://example.com/source",
        }
        response = self.client.post(
            url,
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("card_html", data)
        self.assertEqual(TransferRumour.objects.count(), 1)

    def test_ajax_create_denied_for_basic_user(self):
        self.client.force_login(self.basic_user)
        url = reverse("transfer_rumour:create")
        payload = {
            "title": "Denied Rumour",
            "summary": "Should not be allowed",
            "content": "Content shouldn't persist",
        }
        response = self.client.post(
            url,
            payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(TransferRumour.objects.count(), 0)
