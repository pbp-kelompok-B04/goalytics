from django.test import TestCase, Client
from django.urls import reverse
from PlayerClub_Data.models import Player, Club

class ComparisonTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.club = Club.objects.create(name="FC Test")
        self.player1 = Player.objects.create(name="Player One", position="FW", club=self.club, goals=10, assists=3)
        self.player2 = Player.objects.create(name="Player Two", position="FW", club=self.club, goals=8, assists=5)

    def test_comparison_view_loads(self):
        response = self.client.get(reverse('comparison'))
        self.assertEqual(response.status_code, 200)

    def test_player_search_api(self):
        response = self.client.get(reverse('player_search_api'), {'q': 'Player'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('players', data)
        self.assertGreaterEqual(len(data['players']), 1)

    def test_compare_players_api(self):
        response = self.client.get(reverse('compare_players_api'), {
            'player1_id': self.player1.id,
            'player2_id': self.player2.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('html', data)

