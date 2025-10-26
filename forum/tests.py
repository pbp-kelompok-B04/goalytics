
import json
from types import SimpleNamespace

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse, NoReverseMatch, resolve

from forum.admin import PostAdmin, CommentAdmin
from forum.models import Post, Comment


# ---------- Helpers ----------
def jpost(client: Client, urlname: str, payload: dict, **kwargs):
    """
    POST JSON helper (content_type application/json) with optional url kwargs.
    """
    return client.post(
        reverse(urlname, kwargs=kwargs),
        data=json.dumps(payload),
        content_type="application/json",
    )


# ---------- Model basics ----------
class ModelBasicsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass123")

    def test_post_str_and_comment_is_parent(self):
        p = Post.objects.create(author=self.user, title="Hello", content="World")
        c_root = Comment.objects.create(post=p, user=self.user, content="Root")
        c_child = Comment.objects.create(post=p, user=self.user, content="Child", parent=c_root)

        self.assertEqual(str(p), "Hello")
        self.assertTrue(c_root.is_parent)
        self.assertFalse(c_child.is_parent)


# ---------- Admin helpers ----------
class AdminHelpersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass123")
        self.user2 = User.objects.create_user(username="bob", password="pass123")
        self.post = Post.objects.create(author=self.user, title="A", content="B")
        self.comment = Comment.objects.create(post=self.post, user=self.user, content="Hi")

    def test_post_admin_like_and_comment_count(self):
        pa = PostAdmin(Post, admin.site)
        self.post.likes.add(self.user, self.user2)
        Comment.objects.create(post=self.post, user=self.user, content="Another")
        self.assertEqual(pa.like_count(self.post), 2)
        self.assertEqual(pa.comment_total(self.post), 2)

    def test_comment_admin_helpers(self):
        ca = CommentAdmin(Comment, admin.site)
        self.comment.likes.add(self.user)
        # short_content: shorter than 60 -> returned as-is
        self.assertEqual(ca.short_content(self.comment), "Hi")
        self.assertEqual(ca.like_count(self.comment), 1)


# ---------- URL reverse/resolve smoke test ----------
class UrlsSmokeTests(TestCase):
    def test_named_urls_reverse_and_resolve(self):
        name_kwargs = {
            "forum_home": {},
            "forum_post_detail": {"post_id": 1},
            "get_all_post": {},
            "get_my_posts": {},
            "create_post": {},
            "get_post_by_id": {"post_id": 1},
            "update_post": {"post_id": 1},
            "delete_post": {"post_id": 1},
            "like_post": {"post_id": 1},
            "get_post_comment": {"post_id": 1},
            "create_comment": {"post_id": 1},
            "update_comment": {"comment_id": 1},
            "delete_comment": {"comment_id": 1},
            "like_comment": {"comment_id": 1},
        }
        for name, kwargs in name_kwargs.items():
            try:
                url = reverse(name, kwargs=kwargs)
            except NoReverseMatch:
                self.fail(f"reverse() failed for url name {name} with kwargs={kwargs}")
            resolved = resolve(url)
            self.assertIsNotNone(resolved.func, f"Could not resolve url {url}")


# ---------- Page views ----------
class ForumHomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="alice", password="pass123")

    def test_forum_home_not_admin(self):
        self.client.login(username="alice", password="pass123")
        resp = self.client.get(reverse("forum_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("forum_is_admin", resp.context)
        self.assertFalse(resp.context["forum_is_admin"])

    def test_forum_home_admin_via_requestfactory(self):
        # bypass auth by crafting a user-like object with role='admin'
        rf = RequestFactory()
        req = rf.get("/")
        req.user = SimpleNamespace(is_authenticated=True, username="adminuser", profile=SimpleNamespace(role="admin"))
        from forum import views
        resp = views.forum_home(req)
        self.assertEqual(resp.status_code, 200)


# ---------- API views ----------
class ForumApiViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.u1 = User.objects.create_user(username="alice", password="pass123", first_name="Alice", last_name="Doe")
        self.u2 = User.objects.create_user(username="bob", password="pass123")
        self.post1 = Post.objects.create(author=self.u1, title="P1", content="C1", league="EPL")
        self.post2 = Post.objects.create(author=self.u2, title="P2", content="C2", league="LALIGA")

    # --- Auth guards ---
    def test_create_post_requires_login(self):
        resp = jpost(self.client, "create_post", {"title": "X", "content": "Y"})
        self.assertEqual(resp.status_code, 302)  # login redirect

    def test_get_my_posts_requires_login(self):
        resp = self.client.get(reverse("get_my_posts"))
        self.assertEqual(resp.status_code, 302)

    # --- List & detail ---
    def test_get_all_post_filters_and_flags(self):
        self.client.login(username="alice", password="pass123")
        # Alice likes her own post
        self.post1.likes.add(self.u1)
        # Filter by league + mine + sort=oldest
        resp = self.client.get(reverse("get_all_post"), {"league": "EPL", "mine": "true", "sort": "oldest"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data), 1)
        one = data[0]
        self.assertEqual(one["id"], self.post1.id)
        self.assertTrue(one["is_author"])
        self.assertTrue(one["is_liked"])
        self.assertIn("https://ui-avatars.com/api/?name", one["avatar"])

    def test_get_post_by_id(self):
        self.client.login(username="alice", password="pass123")
        resp = self.client.get(reverse("get_post_by_id", kwargs={"post_id": self.post1.id}))
        self.assertEqual(resp.status_code, 200)
        d = resp.json()["data"]
        self.assertEqual(d["id"], self.post1.id)
        self.assertTrue(d["is_author"])

    # --- Create / Update / Delete Post ---
    def test_create_post_success_and_invalid_league(self):
        self.client.login(username="alice", password="pass123")
        resp_ok = jpost(self.client, "create_post", {"title": "New", "content": "Body", "league": "EPL"})
        self.assertEqual(resp_ok.status_code, 201)
        self.assertEqual(resp_ok.json()["data"]["title"], "New")

        resp_bad = jpost(self.client, "create_post", {"title": "New", "content": "Body", "league": "INVALID"})
        self.assertEqual(resp_bad.status_code, 400)

    def test_update_post_success_and_forbidden(self):
        self.client.login(username="alice", password="pass123")
        # Bob's post cannot be updated by Alice
        resp_forbidden = jpost(self.client, "update_post",
                               {"_method": "PATCH", "post_id": self.post2.id, "title": "Hacked"},
                               post_id=self.post2.id)
        self.assertEqual(resp_forbidden.status_code, 400)

        # Alice can update her post
        resp_ok = jpost(self.client, "update_post",
                        {"_method": "PATCH", "post_id": self.post1.id, "title": "Updated", "league": "LALIGA"},
                        post_id=self.post1.id)
        self.assertEqual(resp_ok.status_code, 200)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, "Updated")
        self.assertEqual(self.post1.league, "LALIGA")

    def test_delete_post_success_and_forbidden(self):
        self.client.login(username="alice", password="pass123")
        # Can't delete other's post
        resp_forbidden = jpost(self.client, "delete_post", {"_method": "DELETE", "post_id": self.post2.id},
                               post_id=self.post2.id)
        self.assertEqual(resp_forbidden.status_code, 400)

    # Delete own post
        resp_ok = jpost(self.client, "delete_post", {"_method": "DELETE", "post_id": self.post1.id},
                        post_id=self.post1.id)
        self.assertEqual(resp_ok.status_code, 200)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    # --- Like toggles ---
    def test_like_post_toggle(self):
        self.client.login(username="alice", password="pass123")
        # Like
        resp1 = jpost(self.client, "like_post", {"_method": "PATCH", "post_id": self.post2.id}, post_id=self.post2.id)
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(resp1.json()["liked"])
        # Unlike
        resp2 = jpost(self.client, "like_post", {"_method": "PATCH", "post_id": self.post2.id}, post_id=self.post2.id)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json()["liked"])

    # --- Comments ---
    def test_comments_tree_and_crud(self):
        self.client.login(username="alice", password="pass123")

        # Create a root comment
        c1 = jpost(self.client, "create_comment", {"content": "Root!"}, post_id=self.post2.id)
        self.assertEqual(c1.status_code, 201)
        c1_id = c1.json()["data"]["id"]

        # Create a reply to root
        c2 = jpost(self.client, "create_comment", {"content": "Child", "parent_id": c1_id}, post_id=self.post2.id)
        self.assertEqual(c2.status_code, 201)
        c2_id = c2.json()["data"]["id"]

        # Invalid parent id -> 400
        bad = jpost(self.client, "create_comment", {"content": "Invalid", "parent_id": 9999}, post_id=self.post2.id)
        self.assertEqual(bad.status_code, 400)

        # Fetch full tree
        tree = self.client.get(reverse("get_post_comment", kwargs={"post_id": self.post2.id}))
        self.assertEqual(tree.status_code, 200)
        nodes = tree.json()["data"]
        self.assertEqual(len(nodes), 1)  # single root
        self.assertEqual(nodes[0]["replies"][0]["content"], "Child")

        # Update child
        upd = jpost(self.client, "update_comment",
                    {"_method": "PATCH", "post_id": self.post2.id, "comment_id": c2_id, "content": "Edited"},
                    comment_id=c2_id)
        self.assertEqual(upd.status_code, 200)

        # Like toggle on child
        like1 = jpost(self.client, "like_comment",
                      {"_method": "PATCH", "post_id": self.post2.id, "comment_id": c2_id}, comment_id=c2_id)
        self.assertEqual(like1.status_code, 200)
        self.assertTrue(like1.json()["liked"])
        like2 = jpost(self.client, "like_comment",
                      {"_method": "PATCH", "post_id": self.post2.id, "comment_id": c2_id}, comment_id=c2_id)
        self.assertEqual(like2.status_code, 200)
        self.assertFalse(like2.json()["liked"])

        # Delete root comment (owner OK)
        del_ok = jpost(self.client, "delete_comment",
                       {"_method": "DELETE", "post_id": self.post2.id, "comment_id": c1_id}, comment_id=c1_id)
        self.assertEqual(del_ok.status_code, 200)

    def test_update_comment_forbidden(self):
        # Two users and a comment owned by u2
        self.client.login(username="alice", password="pass123")
        c_u2 = Comment.objects.create(post=self.post1, user=self.u2, content="Owned by bob")
        resp = jpost(self.client, "update_comment",
                     {"_method": "PATCH", "post_id": self.post1.id, "comment_id": c_u2.id, "content": "try"},
                     comment_id=c_u2.id)
        self.assertEqual(resp.status_code, 400)

    # --- Simple page ---
    def test_post_detail_renders(self):
        resp = self.client.get(reverse("forum_post_detail", kwargs={"post_id": self.post1.id}))
        self.assertEqual(resp.status_code, 200)
