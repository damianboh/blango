from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken import views
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
import os
from rest_framework.routers import DefaultRouter
#from blog.api.views import PostList, PostDetail, UserDetail, TagViewSet
from blog.api.views import PostViewSet, UserDetail, TagViewSet

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register("tags", TagViewSet)
router.register("posts", PostViewSet)

# for yasg library swagger test
schema_view = get_schema_view(
    openapi.Info(
        title="Blango API",
        default_version="v1",
        description="API for Blango Blog",
    ),
    url=f"https://{os.environ.get('CODIO_HOSTNAME')}-8000.codio.io/api/v1/",
    public=True,
)

urlpatterns = [
    # below not needed when using PostViewSet, register as router above instead
    # path("posts/", PostList.as_view(), name="api_post_list"),
    # path("posts/<int:pk>", PostDetail.as_view(), name="api_post_detail"),
    
    path("users/<str:email>", UserDetail.as_view(), name="api_user_detail"), 
    # use email so people cannot just change the id to different numbers
]
urlpatterns = format_suffix_patterns(urlpatterns)

urlpatterns += [
    path("auth/", include("rest_framework.urls")),
    
    # for basic token authentication
    path("token-auth/", views.obtain_auth_token),

    # for simple jwt authentication with djangorestframework-simplejwt library
    # get refresh and temp access token
    path("jwt/", TokenObtainPairView.as_view(), name="jwt_obtain_pair"),
    # generate access token again using refresh token
    # can be decoded at jwt.io, but need a secret to verify signature
    # can decode contents but can't change them without secret
    path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
    
    # lists all request urls when ended with .json or .yaml
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    # api/v1/swagger/ gives UI to test APIs
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("", include(router.urls)), # for PostViewSet and TagViewSet

    # customize PostViewSet by time
    path(
        "posts/by-time/<str:period_name>/",
        PostViewSet.as_view({"get": "list"}),
        name="posts-by-time",
    ),
]