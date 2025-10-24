from django.contrib.auth import get_user_model
from django.test import TestCase

from PlayerClub_Data.models import Club

from .models import ADMIN_USERNAMES, Profile


class ProfileModelTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.club = Club.objects.create(
            name="Goalytics FC",
            league="EPL",
            season="2425",
            total_goal=50,
            total_assist=30,
        )

    def test_profile_str_representation(self):
        user = self.User.objects.create_user(username="regular_user", password="pass123")
        profile = Profile.objects.create(user=user, role="basic")
        self.assertEqual(str(profile), "regular_user (basic)")

    def test_admin_usernames_locked_to_admin_role(self):
        username = ADMIN_USERNAMES[0]
        user = self.User.objects.get(username=username)
        profile = user.profile
        profile.role = "analyst"
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.role, "admin")

    def test_favorite_team_relationship_optional(self):
        user = self.User.objects.create_user(username="fan_user", password="pass123")
        profile = Profile.objects.create(user=user, role="analyst", favorite_team=self.club)
        self.assertEqual(profile.favorite_team, self.club)
        profile.favorite_team = None
        profile.save()
        profile.refresh_from_db()
        self.assertIsNone(profile.favorite_team)
