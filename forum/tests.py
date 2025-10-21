import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Post, Comment


class ForumModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass12345")

    def test_post_str(self):
        p = Post.objects.create(author=self.user, title="Hello", content="World")
        self.assertEqual(str(p), "Hello")

    def test_comment_is_parent_and_relations(self):
        p = Post.objects.create(author=self.user, title="T", content="C")
        parent = Comment.objects.create(post=p, user=self.user, content="parent")
        child = Comment.objects.create(post=p, user=self.user, content="child", parent=parent)
        self.assertTrue(parent.is_parent)
        self.assertFalse(child.is_parent)
        self.assertEqual(parent.replies.count(), 1)
        self.assertEqual(parent.replies.first().id, child.id)


class ForumViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="bob", password="secret123")
        self.other = User.objects.create_user(username="jane", password="secret123")

    def _auth(self):
        self.client.login(username="bob", password="secret123")

    def test_get_all_post_returns_posts_and_counts(self):
        p1 = Post.objects.create(author=self.other, title="A", content="a")
        p2 = Post.objects.create(author=self.user, title="B", content="b")
        Comment.objects.create(post=p2, user=self.user, content="c1")
        Comment.objects.create(post=p2, user=self.other, content="c2")

        url = reverse("get_all_post")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("data", payload)
        self.assertEqual(len(payload["data"]), 2)
        ids = [item["id"] for item in payload["data"]]
        self.assertEqual(ids, [p2.id, p1.id])
        self.assertEqual(payload["data"][0]["comment_count"], 2)

    def test_get_post_by_id(self):
        p = Post.objects.create(author=self.user, title="T", content="C")
        url = reverse("get_post_by_id", args=[p.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["id"], p.id)
        self.assertEqual(data["author"], self.user.username)

    def test_get_post_comment_nested(self):
        p = Post.objects.create(author=self.user, title="T", content="C")
        c1 = Comment.objects.create(post=p, user=self.user, content="p1")
        c2 = Comment.objects.create(post=p, user=self.other, content="p2")
        Comment.objects.filter(id=c1.id).update(created_at=timezone.now() - timedelta(seconds=2))
        Comment.objects.filter(id=c2.id).update(created_at=timezone.now() - timedelta(seconds=1))
        c1.refresh_from_db(); c2.refresh_from_db()
        r1 = Comment.objects.create(post=p, user=self.other, content="r1", parent=c1)
        r2 = Comment.objects.create(post=p, user=self.user, content="r2", parent=c1)

        url = reverse("get_post_comment", args=[p.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["data"]
        self.assertEqual([i["id"] for i in items], [c2.id, c1.id])
        replies = [i for i in items if i["id"] == c1.id][0]["replies"]
        self.assertEqual([r["id"] for r in replies], [r1.id, r2.id])

    def test_get_my_posts_requires_login(self):
        url = reverse("get_my_post")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_create_post_requires_login(self):
        url = reverse("create_post")
        resp = self.client.post(url, data=json.dumps({"title": "x", "content": "y"}), content_type="application/json")
        self.assertEqual(resp.status_code, 302)

    def test_create_comment_requires_login(self):
        p = Post.objects.create(author=self.user, title="T", content="C")
        url = reverse("create_comment", args=[p.id])
        resp = self.client.post(url, data=json.dumps({"content": "hi"}), content_type="application/json")
        self.assertEqual(resp.status_code, 302)

    def test_get_post_by_id_404(self):
        url = reverse("get_post_by_id", args=[9999])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_method_not_allowed(self):
        self.assertEqual(self.client.post(reverse("get_all_post")).status_code, 405)
        self._auth()
        p = Post.objects.create(author=self.user, title="T", content="C")
        self.assertEqual(self.client.get(reverse("create_post")).status_code, 405)
        self.assertEqual(self.client.get(reverse("create_comment", args=[p.id])).status_code, 405)

    def test_get_my_posts_and_create_post_authenticated(self):
        self._auth()
        resp = self.client.get(reverse("get_my_post"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"], [])
        resp = self.client.post(reverse("create_post"), data=json.dumps({"title": "", "content": "  "}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        payload = {"title": "New", "content": "Post"}
        resp = self.client.post(reverse("create_post"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()["data"]
        self.assertEqual(data["title"], "New")
        resp = self.client.get(reverse("get_my_post"))
        self.assertEqual(len(resp.json()["data"]), 1)

    def test_create_comment_flows(self):
        self._auth()
        p = Post.objects.create(author=self.other, title="T", content="C")
        url = reverse("create_comment", args=[p.id])
        resp = self.client.post(url, data=json.dumps({"content": "   "}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(url, data=json.dumps({"content": "hello"}), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        c_id = resp.json()["data"]["id"]
        resp = self.client.post(url, data=json.dumps({"content": "reply", "parent_id": c_id}), content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        other_post = Post.objects.create(author=self.other, title="X", content="Y")
        other_comment = Comment.objects.create(post=other_post, user=self.other, content="zzz")
        resp = self.client.post(url, data=json.dumps({"content": "bad", "parent_id": other_comment.id}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)
