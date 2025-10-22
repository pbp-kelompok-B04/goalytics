import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import Post, Comment
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from . import views as forum_views
import unittest


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
        payload = json.loads(resp.content)
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


class ForumViewMoreTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="u1", password="pw12345678")
        self.other = User.objects.create_user(username="u2", password="pw12345678")

    def _json_request(self, method, path="/", data=None):
        body = json.dumps(data or {})
        req = getattr(self.factory, method)(path, data=body, content_type="application/json")
        return req

    def test_update_post_updates_content(self):
        post = Post.objects.create(author=self.user, title="T", content="C")
        req = self._json_request("patch", data={"post_id": post.id, "content": "New Content"})
        req.user = self.user
        resp = forum_views.update_post(req)
        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content)
        self.assertEqual(payload["id"], post.id)
        self.assertEqual(payload["content"], "New Content")

    def test_update_comment_validation_and_permissions(self):
        post = Post.objects.create(author=self.user, title="T", content="C")
        comment = Comment.objects.create(post=post, user=self.user, content="old")

        # invalid JSON
        req = self.factory.patch("/api/comments/update", data="not-json", content_type="application/json")
        req.user = self.user
        resp = forum_views.update_comment(req)
        self.assertEqual(resp.status_code, 400)

        # empty content
        req = self._json_request("patch", data={"post_id": post.id, "comment_id": comment.id, "content": "  "})
        req.user = self.user
        resp = forum_views.update_comment(req)
        self.assertEqual(resp.status_code, 400)

        # forbidden when not owner
        req = self._json_request("patch", data={"post_id": post.id, "comment_id": comment.id, "content": "x"})
        req.user = self.other
        resp = forum_views.update_comment(req)
        self.assertEqual(resp.status_code, 400)

        # success as owner
        req = self._json_request("patch", data={"post_id": post.id, "comment_id": comment.id, "content": "updated"})
        req.user = self.user
        resp = forum_views.update_comment(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["new_content"], "updated")

    def test_delete_post_requires_author_and_id(self):
        post = Post.objects.create(author=self.user, title="T", content="C")

        # missing id
        req = self._json_request("delete", data={})
        req.user = self.user
        resp = forum_views.delete_post(req)
        self.assertEqual(resp.status_code, 400)

        # forbidden for non-author
        req = self._json_request("delete", data={"post_id": post.id})
        req.user = self.other
        resp = forum_views.delete_post(req)
        self.assertEqual(resp.status_code, 400)

        # author can delete
        req = self._json_request("delete", data={"post_id": post.id})
        req.user = self.user
        resp = forum_views.delete_post(req)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_delete_comment_requires_owner_and_ids(self):
        post = Post.objects.create(author=self.user, title="T", content="C")
        comment = Comment.objects.create(post=post, user=self.user, content="c")

        # missing post_id
        req = self._json_request("delete", data={})
        req.user = self.user
        resp = forum_views.delete_comment(req)
        self.assertEqual(resp.status_code, 400)

        # missing comment_id
        req = self._json_request("delete", data={"post_id": post.id})
        req.user = self.user
        resp = forum_views.delete_comment(req)
        self.assertEqual(resp.status_code, 400)

        # forbidden for non-owner
        req = self._json_request("delete", data={"post_id": post.id, "comment_id": comment.id})
        req.user = self.other
        resp = forum_views.delete_comment(req)
        self.assertEqual(resp.status_code, 400)

        # owner can delete
        req = self._json_request("delete", data={"post_id": post.id, "comment_id": comment.id})
        req.user = self.user
        resp = forum_views.delete_comment(req)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_like_post_toggle(self):
        post = Post.objects.create(author=self.user, title="T", content="C")
        req = self._json_request("patch", data={"post_id": post.id})
        req.user = self.user
        resp = forum_views.like_post(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)["liked"])
        self.assertTrue(Post.objects.get(id=post.id).likes.filter(id=self.user.id).exists())

        # toggle back
        req = self._json_request("patch", data={"post_id": post.id})
        req.user = self.user
        resp = forum_views.like_post(req)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content)["liked"])
        self.assertFalse(Post.objects.get(id=post.id).likes.filter(id=self.user.id).exists())

    def test_like_comment_toggle(self):
        post = Post.objects.create(author=self.user, title="T", content="C")
        comment = Comment.objects.create(post=post, user=self.user, content="c")
        req = self._json_request("patch", data={"post_id": post.id, "comment_id": comment.id})
        req.user = self.user
        resp = forum_views.like_comment(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)["liked"])
        self.assertTrue(Comment.objects.get(id=comment.id).likes.filter(id=self.user.id).exists())

        # toggle back
        req = self._json_request("patch", data={"post_id": post.id, "comment_id": comment.id})
        req.user = self.user
        resp = forum_views.like_comment(req)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content)["liked"])
        self.assertFalse(Comment.objects.get(id=comment.id).likes.filter(id=self.user.id).exists())


class ForumAuthAndEdgeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="u1", password="pw12345678")
        self.other = User.objects.create_user(username="u2", password="pw12345678")

    def _auth(self):
        self.client.login(username="u1", password="pw12345678")

    def _rf(self, method, data=None):
        body = json.dumps(data or {})
        return getattr(self.factory, method)("/", data=body, content_type="application/json")

    def test_login_required_redirects_on_views(self):
        # Using RequestFactory with AnonymousUser to hit @login_required wrappers
        rf = self.factory
        anon = AnonymousUser()
        # update_post
        req = self._rf("patch", {"post_id": 1})
        req.user = anon
        resp = forum_views.update_post(req)
        self.assertEqual(resp.status_code, 302)
        # update_comment
        req = self._rf("patch", {"post_id": 1, "comment_id": 1, "content": "x"})
        req.user = anon
        resp = forum_views.update_comment(req)
        self.assertEqual(resp.status_code, 302)
        # delete_post
        req = self._rf("delete", {"post_id": 1})
        req.user = anon
        resp = forum_views.delete_post(req)
        self.assertEqual(resp.status_code, 302)
        # delete_comment
        req = self._rf("delete", {"post_id": 1, "comment_id": 1})
        req.user = anon
        resp = forum_views.delete_comment(req)
        self.assertEqual(resp.status_code, 302)
        # like_post
        req = self._rf("patch", {"post_id": 1})
        req.user = anon
        resp = forum_views.like_post(req)
        self.assertEqual(resp.status_code, 302)
        # like_comment
        req = self._rf("patch", {"post_id": 1, "comment_id": 1})
        req.user = anon
        resp = forum_views.like_comment(req)
        self.assertEqual(resp.status_code, 302)

    def test_update_post_title_strip_and_both_fields(self):
        p = Post.objects.create(author=self.user, title="Old", content="OldC")
        req = self._rf("patch", {"post_id": p.id, "title": "  New Title  ", "content": "  NewC  "})
        req.user = self.user
        resp = forum_views.update_post(req)
        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content)
        self.assertEqual(payload["title"], "New Title")
        self.assertEqual(payload["content"], "NewC")

    def test_update_post_invalid_id_404(self):
        req = self._rf("patch", {"post_id": 999999, "content": "x"})
        req.user = self.user
        with self.assertRaises(Http404):
            forum_views.update_post(req)

    def test_like_post_invalid_id_404(self):
        req = self._rf("patch", {"post_id": 123456})
        req.user = self.user
        with self.assertRaises(Http404):
            forum_views.like_post(req)

    def test_like_comment_invalid_ids_404(self):
        p = Post.objects.create(author=self.user, title="T", content="C")
        req = self._rf("patch", {"post_id": p.id, "comment_id": 987654})
        req.user = self.user
        with self.assertRaises(Http404):
            forum_views.like_comment(req)

    def test_get_post_comment_invalid_post_404(self):
        url = reverse("get_post_comment", args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
