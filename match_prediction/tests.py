from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# --- Safe import for Club model ---
try:
    from PlayerClub_Data.models import Club
except Exception:
    from django.db import models
    class Club(models.Model):
        name = models.CharField(max_length=100)
        class Meta:
            app_label = 'PlayerClub_Data'

from match_prediction.models import Match, Prediction, PredictionUpvote
from match_prediction.forms import MatchForm, PredictionForm
from match_prediction.admin import MatchAdmin, PredictionAdmin, PredictionUpvoteAdmin


User = get_user_model()


class MatchPredictionTests(TestCase):
    """Unified tests for match_prediction module (models, forms, views, admin)."""

    @classmethod
    def setUpTestData(cls):
        cls.club_a = Club.objects.create(name="Alpha FC")
        cls.club_b = Club.objects.create(name="Beta FC")
        cls.user = User.objects.create_user(username="user", password="pass")
        cls.admin = User.objects.create_superuser(username="admin", password="adminpass")

        cls.match = Match.objects.create(home_club=cls.club_a, away_club=cls.club_b, venue="Old Stadium")

    # ----------------------------------------------------------------------
    # MODEL TESTS
    # ----------------------------------------------------------------------
    def test_match_str_and_title(self):
        m = Match.objects.first()
        self.assertIn("Alpha", str(m))
        self.assertEqual(m.title, str(m))

    def test_prediction_model_and_recalc(self):
        p = Prediction.objects.create(match=self.match, user=self.user,
                                      predicted_home_score=1, predicted_away_score=0)
        PredictionUpvote.objects.create(prediction=p, user=self.admin)
        p.recalc_upvote_count()
        self.assertEqual(p.upvote_count, 1)

    def test_match_same_club_validation(self):
        m = Match(home_club=self.club_a, away_club=self.club_a)
        with self.assertRaises(ValidationError):
            m.clean()

    # ----------------------------------------------------------------------
    # FORM TESTS
    # ----------------------------------------------------------------------
    def test_match_form_same_club_invalid(self):
        data = {
            'home_club': self.club_a.id,
            'away_club': self.club_a.id,
            'match_datetime': '2025-01-01T12:00',
            'venue': 'Stadium'
        }
        form = MatchForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('Home and Away clubs cannot be the same.', form.errors['__all__'])

    def test_match_form_valid_different_clubs(self):
        data = {
            'home_club': self.club_a.id,
            'away_club': self.club_b.id,
            'match_datetime': '2025-01-01T12:00',
            'venue': 'Stadium'
        }
        form = MatchForm(data)
        self.assertTrue(form.is_valid())

    def test_prediction_form_score_fields(self):
        form = PredictionForm({'predicted_home_score': '', 'predicted_away_score': ''})
        self.assertFalse(form.is_valid())

    # ----------------------------------------------------------------------
    # VIEW TESTS
    # ----------------------------------------------------------------------
    def setUp(self):
        self.client = Client()

    def test_match_list_view(self):
        url = reverse('match_prediction:match_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_create_match_ajax(self):
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_create')
        data = {
            'home_club': self.club_a.id,
            'away_club': self.club_b.id,
            'match_datetime': '2025-01-02T12:00',
            'venue': 'Arena'
        }
        resp = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Match created successfully', resp.content.decode())

    def test_create_match_non_ajax(self):
        """Covers normal (non-AJAX) POST path."""
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_create')
        data = {
            'home_club': self.club_a.id,
            'away_club': self.club_b.id,
            'match_datetime': '2025-01-02T12:00',
            'venue': 'Arena'
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)  # redirect on success

    def test_edit_match_ajax(self):
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_edit', args=[self.match.id])
        data = {
            'home_club': self.club_b.id,
            'away_club': self.club_a.id,
            'match_datetime': '2025-03-01T14:00',
            'venue': 'Updated Venue'
        }
        resp = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.match.refresh_from_db()
        self.assertEqual(self.match.venue, "Updated Venue")

    def test_edit_match_non_ajax(self):
        """Covers normal (non-AJAX) POST path."""
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_edit', args=[self.match.id])
        data = {
            'home_club': self.club_b.id,
            'away_club': self.club_a.id,
            'match_datetime': '2025-03-01T14:00',
            'venue': 'Venue'
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)

    def test_delete_match_ajax(self):
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_delete', args=[self.match.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Match.objects.filter(id=self.match.id).exists())

    def test_delete_match_non_ajax(self):
        """Covers fallback non-AJAX delete."""
        m = Match.objects.create(home_club=self.club_a, away_club=self.club_b)
        self.client.force_login(self.admin)
        url = reverse('match_prediction:match_delete', args=[m.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

    def test_prediction_add_edit_delete(self):
        self.client.force_login(self.user)
        add_url = reverse('match_prediction:ajax_add_prediction', args=[self.match.id])
        data = {'predicted_home_score': 2, 'predicted_away_score': 1}
        resp = self.client.post(add_url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        p = Prediction.objects.first()
        edit_url = reverse('match_prediction:edit_prediction', args=[p.id])
        self.client.post(edit_url, {'predicted_home_score': 3, 'predicted_away_score': 1},
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        delete_url = reverse('match_prediction:delete_prediction', args=[p.id])
        resp = self.client.post(delete_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        p.refresh_from_db()
        self.assertTrue(p.is_deleted)

    def test_upvote_toggle(self):
        self.client.force_login(self.user)
        p = Prediction.objects.create(match=self.match, user=self.admin,
                                      predicted_home_score=1, predicted_away_score=0)
        url = reverse('match_prediction:ajax_toggle_upvote', args=[p.id])
        self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        p.refresh_from_db()
        self.assertEqual(p.upvote_count, 0)

    # ----------------------------------------------------------------------
    # ADMIN TESTS (to cover readonly permissions)
    # ----------------------------------------------------------------------
    def test_admin_permissions(self):
        """Covers has_add/change/delete_permission logic for all admin classes."""
        rf = RequestFactory()
        req = rf.get('/')
        admin_obj = MatchAdmin(Match, None)
        pred_admin = PredictionAdmin(Prediction, None)
        upvote_admin = PredictionUpvoteAdmin(PredictionUpvote, None)

        # add permission should always be False
        self.assertFalse(admin_obj.has_add_permission(req))
        self.assertFalse(pred_admin.has_add_permission(req))
        self.assertFalse(upvote_admin.has_add_permission(req))

        # delete permission should always be False
        self.assertFalse(admin_obj.has_delete_permission(req))
        self.assertFalse(pred_admin.has_delete_permission(req))
        self.assertFalse(upvote_admin.has_delete_permission(req))

        # change permission True for GET, False for POST
        self.assertTrue(admin_obj.has_change_permission(req))
        req_post = rf.post('/')
        self.assertFalse(admin_obj.has_change_permission(req_post))
