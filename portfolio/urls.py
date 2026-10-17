from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *
router=DefaultRouter()
for prefix, cls in [("skills",SkillViewSet),("experiences",ExperienceViewSet),("education",EducationViewSet),("projects",ProjectViewSet),("categories",CategoryViewSet),("tags",TagViewSet),("posts",PostViewSet),("comments",CommentViewSet),("contact",ContactViewSet)]:
    router.register(prefix,cls,basename=prefix)
urlpatterns=[
    path("auth/login/",login), path("auth/refresh/",TokenRefreshView.as_view()), path("auth/logout/",logout),
    path("auth/me/",me), path("auth/change-password/",change_password),
    path("profile/",ProfileViewSet.as_view({"get":"list","patch":"partial_update"})),
    path("dashboard/stats/",dashboard), path("",include(router.urls)),
]
