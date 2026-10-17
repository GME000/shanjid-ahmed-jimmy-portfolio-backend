from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers
from .models import *

class AbsoluteURLMixin:
    def get_url(self, obj, field):
        value = getattr(obj, field, None)
        return self.context["request"].build_absolute_uri(value.url) if value else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            for field in ("avatar", "resume", "cover_image"):
                if field in data:
                    value = getattr(instance, field, None)
                    data[field] = request.build_absolute_uri(value.url) if value else None
        return data
class ProfileSerializer(AbsoluteURLMixin, serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField(); resume_url = serializers.SerializerMethodField()
    class Meta: model = Profile; fields = "__all__"
    def get_avatar_url(self,o): return self.get_url(o,"avatar")
    def get_resume_url(self,o): return self.get_url(o,"resume")
class SkillSerializer(serializers.ModelSerializer):
    class Meta: model = Skill; fields = "__all__"
    def validate_proficiency(self,v):
        if not 1 <= v <= 100: raise serializers.ValidationError("Proficiency must be between 1 and 100.")
        return v
class ExperienceSerializer(serializers.ModelSerializer):
    class Meta: model = Experience; fields = "__all__"
    def validate(self, d):
        if d.get("start_date") and d["start_date"] > timezone.localdate(): raise serializers.ValidationError("Start date cannot be in the future.")
        if d.get("is_current") and d.get("end_date"): raise serializers.ValidationError("Current experience cannot have an end date.")
        if not d.get("is_current") and not d.get("end_date"): raise serializers.ValidationError({"end_date": "End date is required for past experience."})
        if not d.get("is_current") and d.get("end_date") and d["end_date"] <= d.get("start_date", self.instance.start_date if self.instance else d["end_date"]): raise serializers.ValidationError({"end_date": "End date must be after start date."})
        return d
class EducationSerializer(serializers.ModelSerializer):
    class Meta: model = Education; fields = "__all__"
class ProjectSerializer(AbsoluteURLMixin, serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    class Meta: model = Project; fields = "__all__"
    def get_cover_image_url(self,o): return self.get_url(o,"cover_image")
    def validate(self,d):
        if not d.get("live_url", getattr(self.instance,"live_url","")) and not d.get("github_url", getattr(self.instance,"github_url","")): raise serializers.ValidationError("Provide a live URL or GitHub URL.")
        return d
class TaxonomySerializer(serializers.ModelSerializer):
    posts_count = serializers.IntegerField(read_only=True)
    class Meta: fields = "__all__"
class CategorySerializer(TaxonomySerializer): model = Category
class TagSerializer(TaxonomySerializer): model = Tag
class PostSerializer(AbsoluteURLMixin, serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True); comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField(); cover_image_url = serializers.SerializerMethodField()
    class Meta: model = Post; fields = "__all__"; read_only_fields = ["author","published_at","reading_time","views_count"]
    def get_is_liked(self,o):
        v = self.context.get("request").headers.get("X-Visitor-Id") if self.context.get("request") else None
        return bool(v and o.likes.filter(visitor_id=v).exists())
    def get_cover_image_url(self,o): return self.get_url(o,"cover_image")
    def validate(self,d):
        title=d.get("title", getattr(self.instance,"title",""))
        if len(title.strip())<5: raise serializers.ValidationError({"title":"Title must be at least 5 characters."})
        status=d.get("status", getattr(self.instance,"status",Post.DRAFT))
        if status == Post.PUBLISHED and not d.get("category", getattr(self.instance, "category", None)): raise serializers.ValidationError({"category":"A published post must have a category."})
        if status == Post.PUBLISHED and len(d.get("content", getattr(self.instance,"content","")))<100: raise serializers.ValidationError("Published content must be at least 100 characters.")
        return d
class CommentSerializer(serializers.ModelSerializer):
    class Meta: model=Comment; fields="__all__"; read_only_fields=["post","is_approved","created_at"]
    def validate(self,d):
        if len(d.get("name","").strip())<2: raise serializers.ValidationError({"name":"Name must be at least 2 characters."})
        if not 5 <= len(d.get("content","")) <= 1000: raise serializers.ValidationError({"content":"Content must be 5-1000 characters."})
        return d

class PublicCommentSerializer(CommentSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        extra_kwargs = {"email": {"write_only": True}}

    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True).order_by("-created_at")
        return PublicCommentSerializer(replies, many=True, context=self.context).data
class ContactSerializer(serializers.ModelSerializer):
    class Meta: model=ContactMessage; fields="__all__"; read_only_fields=["is_read","created_at"]
    def validate_message(self,v):
        if not 10 <= len(v) <= 2000: raise serializers.ValidationError("Message must be 10-2000 characters.")
        return v
