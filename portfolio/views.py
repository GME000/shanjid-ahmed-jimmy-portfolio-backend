from datetime import timedelta
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from .models import *
from .permissions import IsOwnerOrReadOnly
from .serializers import *
from .throttles import *
from .pagination import SixPagination, NinePagination, TenPagination

class PublicOwnerViewSet(viewsets.ModelViewSet):
    permission_classes=[IsOwnerOrReadOnly]
    def perform_create(self,s): s.save()
class ProfileViewSet(viewsets.ViewSet):
    def list(self,request):
        obj=Profile.objects.first()
        return Response(ProfileSerializer(obj,context={"request":request}).data if obj else {})
    def partial_update(self,request,pk=None):
        if not request.user.is_authenticated or not request.user.is_superuser: return Response(status=403)
        obj=Profile.objects.first() or Profile()
        ser=ProfileSerializer(obj,data=request.data,partial=True,context={"request":request}); ser.is_valid(raise_exception=True); ser.save()
        return Response(ser.data)
class SkillViewSet(PublicOwnerViewSet):
    queryset=Skill.objects.all(); serializer_class=SkillSerializer; filterset_fields=["category","is_featured"]; search_fields=["name"]; ordering_fields=["display_order","proficiency"]
class ExperienceViewSet(PublicOwnerViewSet):
    queryset=Experience.objects.all(); serializer_class=ExperienceSerializer; search_fields=["company","role"]
class EducationViewSet(PublicOwnerViewSet):
    queryset=Education.objects.all(); serializer_class=EducationSerializer
class ProjectViewSet(PublicOwnerViewSet):
    queryset=Project.objects.all().order_by("-completed_date", "display_order", "id"); serializer_class=ProjectSerializer; lookup_field="slug"; filterset_fields=["category","is_featured"]; search_fields=["title","summary","description"]; ordering_fields=["completed_date","display_order"]; pagination_class=NinePagination
class CategoryViewSet(PublicOwnerViewSet):
    queryset=Category.objects.annotate(posts_count=Count("posts",filter=Q(posts__status=Post.PUBLISHED))); serializer_class=CategorySerializer; lookup_field="slug"; search_fields=["name"]
    def destroy(self,request,*args,**kwargs):
        from django.db.models import ProtectedError
        try: return super().destroy(request,*args,**kwargs)
        except ProtectedError: return Response({"detail":"Category is in use by a post and cannot be deleted."},status=400)
class TagViewSet(PublicOwnerViewSet):
    queryset=Tag.objects.annotate(posts_count=Count("posts",filter=Q(posts__status=Post.PUBLISHED))); serializer_class=TagSerializer; lookup_field="slug"; search_fields=["name"]
class PostViewSet(PublicOwnerViewSet):
    serializer_class=PostSerializer; lookup_field="slug"; search_fields=["title","excerpt","content"]; filterset_fields=["is_featured","status"]; ordering_fields=["published_at","views_count","title"]; pagination_class=SixPagination
    def get_queryset(self):
        qs=Post.objects.annotate(likes_count=Count("likes"),comments_count=Count("comments")).order_by("-published_at", "-id")
        if not self.request.user.is_authenticated or not self.request.user.is_superuser:
            qs=qs.filter(status=Post.PUBLISHED)
        elif self.request.query_params.get("status") in ("DRAFT","PUBLISHED"):
            qs=qs.filter(status=self.request.query_params["status"])
        return qs
    def perform_create(self,s): s.save(author=self.request.user)
    def retrieve(self,request,*args,**kwargs):
        obj=self.get_object(); visitor=request.headers.get("X-Visitor-Id")
        key=f"viewed:{obj.pk}:{visitor}" if visitor else None
        from django.core.cache import cache
        if visitor and not cache.get(key):
            Post.objects.filter(pk=obj.pk).update(views_count=F("views_count")+1); cache.set(key,True,300); obj.refresh_from_db()
        return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"],permission_classes=[AllowAny],throttle_classes=[LikeThrottle])
    def like(self,request,slug=None):
        visitor=request.headers.get("X-Visitor-Id")
        if not visitor:return Response({"detail":"X-Visitor-Id header is required."},status=400)
        post=self.get_object(); like,created=PostLike.objects.get_or_create(post=post,visitor_id=visitor,defaults={"ip_address":request.META.get("REMOTE_ADDR")})
        if not created: like.delete()
        return Response({"liked":created,"likes_count":post.likes.count()})
    @action(detail=True,methods=["get","post"],permission_classes=[AllowAny],throttle_classes=[CommentThrottle])
    def comments(self,request,slug=None):
        post=self.get_object()
        if request.method=="POST":
            ser=CommentSerializer(data=request.data); ser.is_valid(raise_exception=True); ser.save(post=post)
            return Response({"message":"Your comment is awaiting approval.","comment":PublicCommentSerializer(ser.instance, context={"request": request}).data},status=201)
        roots=post.comments.filter(is_approved=True,parent__isnull=True).prefetch_related("replies").order_by("-created_at")
        return Response(PublicCommentSerializer(roots,many=True, context={"request": request}).data)
class CommentViewSet(viewsets.ModelViewSet):
    queryset=Comment.objects.all().order_by("-created_at"); serializer_class=CommentSerializer; permission_classes=[IsAuthenticated]; filterset_fields=["is_approved"]; pagination_class=TenPagination
class ContactViewSet(viewsets.ModelViewSet):
    queryset=ContactMessage.objects.all().order_by("-created_at"); serializer_class=ContactSerializer; filterset_fields=["is_read"]; permission_classes=[IsOwnerOrReadOnly]; throttle_classes=[ContactThrottle]; pagination_class=TenPagination
    def get_permissions(self): return [AllowAny()] if self.request.method=="POST" else [IsAuthenticated()]
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    user=authenticate(username=request.data.get("username",""),password=request.data.get("password",""))
    if not user or not user.is_active:return Response({"detail":"Invalid credentials."},status=401)
    r=RefreshToken.for_user(user); return Response({"access":str(r.access_token),"refresh":str(r),"user":{"id":user.id,"username":user.username,"email":user.email}})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try: RefreshToken(request.data["refresh"]).blacklist()
    except (KeyError, ValueError): return Response({"detail":"Invalid refresh token."},status=400)
    return Response(status=204)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request): return Response({"id":request.user.id,"username":request.user.username,"email":request.user.email,"is_superuser":request.user.is_superuser})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    if not request.user.check_password(request.data.get("old_password","")): return Response({"detail":"Old password is incorrect."},status=400)
    request.user.set_password(request.data.get("new_password","")); request.user.save(); return Response({"detail":"Password changed."})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    posts=Post.objects.all(); top=posts.order_by("-views_count")[:5]
    months=posts.filter(created_at__gte=timezone.now()-timedelta(days=183)).annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id")).order_by("month")
    return Response({"total_posts":posts.count(),"published_posts":posts.filter(status=Post.PUBLISHED).count(),"draft_posts":posts.filter(status=Post.DRAFT).count(),"total_projects":Project.objects.count(),"total_skills":Skill.objects.count(),"total_comments":Comment.objects.count(),"pending_comments":Comment.objects.filter(is_approved=False).count(),"total_likes":PostLike.objects.count(),"total_views":posts.aggregate(v=Sum("views_count"))["v"] or 0,"unread_messages":ContactMessage.objects.filter(is_read=False).count(),"top_posts":[{"title":p.title,"slug":p.slug,"views":p.views_count,"likes":p.likes.count()} for p in top],"recent_comments":CommentSerializer(Comment.objects.order_by("-created_at")[:5],many=True).data,"posts_per_month":list(months)})
