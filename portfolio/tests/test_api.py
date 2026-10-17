from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from portfolio.models import Category, Post
class ApiTests(APITestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_superuser("owner","o@example.com","pass12345")
        self.cat=Category.objects.create(name="Tech")
        self.post=Post.objects.create(title="Published post",content="x"*120,category=self.cat,author=self.owner,status="PUBLISHED")
    def test_registration_missing_and_public_drafts_hidden(self):
        self.assertEqual(self.client.post("/api/auth/register/").status_code,404)
        draft=Post.objects.create(title="Draft post",content="x"*120,category=self.cat,author=self.owner)
        self.assertEqual(self.client.get("/api/posts/").status_code,200)
        self.assertEqual(self.client.get(f"/api/posts/{draft.slug}/").status_code,404)
    def test_like_toggle_and_comment_moderation(self):
        url=f"/api/posts/{self.post.slug}/like/"
        self.assertEqual(self.client.post(url,HTTP_X_VISITOR_ID="abc").data["liked"],True)
        self.assertEqual(self.client.post(url,HTTP_X_VISITOR_ID="abc").data["liked"],False)
        response=self.client.post(f"/api/posts/{self.post.slug}/comments/",{"name":"Jane","email":"jane@example.com","content":"hello world"})
        self.assertEqual(response.status_code,201)
        self.assertEqual(self.client.get(f"/api/posts/{self.post.slug}/comments/").data,[])
