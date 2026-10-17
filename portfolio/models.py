import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import PROTECT
from django.utils.text import slugify

class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Profile(Timestamped):
    full_name = models.CharField(max_length=200, default="Shanjid Ahmed Jimmy")
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="profile/", blank=True, null=True)
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    github_url = models.URLField(blank=True); linkedin_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True); website_url = models.URLField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_available_for_hire = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.pk and Profile.objects.exists():
            raise ValidationError("Only one profile is allowed.")
        return super().save(*args, **kwargs)

class Skill(Timestamped):
    CATEGORIES = [(x, x.replace("_", " ").title()) for x in ["FRONTEND","BACKEND","DATABASE","DEVOPS","TOOLS","SOFT_SKILL"]]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    proficiency = models.PositiveSmallIntegerField(default=50)
    icon = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    class Meta: ordering = ["display_order", "-proficiency"]

class Experience(Timestamped):
    EMPLOYMENT = [(x, x.replace("_", " ").title()) for x in ["FULL_TIME","PART_TIME","INTERNSHIP","FREELANCE","CONTRACT"]]
    company = models.CharField(max_length=200); role = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT)
    location = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(); end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False); description = models.TextField()
    company_url = models.URLField(blank=True); display_order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ["-start_date"]

class Education(Timestamped):
    institution = models.CharField(max_length=200); degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200); start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(null=True, blank=True); grade = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)

class Project(Timestamped):
    CATEGORIES = [(x, x.title()) for x in ["WEB","MOBILE","API","ML","OTHER"]]
    title = models.CharField(max_length=200, unique=True); slug = models.SlugField(unique=True, blank=True)
    summary = models.CharField(max_length=200); description = models.TextField()
    cover_image = models.ImageField(upload_to="projects/", blank=True, null=True)
    tech_stack = models.ManyToManyField(Skill, blank=True, related_name="projects")
    category = models.CharField(max_length=10, choices=CATEGORIES)
    live_url = models.URLField(blank=True); github_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False); completed_date = models.DateField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Category(Timestamped):
    name = models.CharField(max_length=100, unique=True); slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Tag(Timestamped):
    name = models.CharField(max_length=80, unique=True); slug = models.SlugField(unique=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Post(Timestamped):
    DRAFT = "DRAFT"; PUBLISHED = "PUBLISHED"
    STATUS = [(DRAFT, "Draft"), (PUBLISHED, "Published")]
    title = models.CharField(max_length=250); slug = models.SlugField(unique=True, blank=True)
    excerpt = models.CharField(max_length=300, blank=True); content = models.TextField()
    cover_image = models.ImageField(upload_to="posts/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=PROTECT, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    status = models.CharField(max_length=12, choices=STATUS, default=DRAFT)
    published_at = models.DateTimeField(null=True, blank=True); views_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=1); is_featured = models.BooleanField(default=False)
    class Meta: ordering = ["-published_at"]
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        self.reading_time = max(1, round(len(self.content.split()) / 200))
        if self.status == self.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    visitor_id = models.CharField(max_length=100); ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["post","visitor_id"], name="unique_post_visitor_like")]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=120); email = models.EmailField(); website = models.URLField(blank=True)
    content = models.TextField(); parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    is_approved = models.BooleanField(default=False); created_at = models.DateTimeField(auto_now_add=True)

class ContactMessage(models.Model):
    name = models.CharField(max_length=120); email = models.EmailField(); subject = models.CharField(max_length=200)
    message = models.TextField(); is_read = models.BooleanField(default=False); created_at = models.DateTimeField(auto_now_add=True)
