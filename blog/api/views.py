from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers, vary_on_cookie

from rest_framework.exceptions import PermissionDenied

from django.db.models import Q
from django.utils import timezone

from datetime import timedelta
from django.http import Http404

from blog.api.serializers import (
    PostSerializer,
    UserSerializer,
    PostDetailSerializer,
    TagSerializer,
)
from blog.models import Post, Tag

from blango_auth.models import User

from blog.api.permissions import AuthorModifyOrReadOnly, IsAdminUserForObject

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    # own custom action to get posts with tags
    @action(methods=["get"], detail=True, name="Posts with the Tag")
    def posts(self, request, pk=None):
        tag = self.get_object()
        post_serializer = PostSerializer(
            tag.posts, many=True, context={"request": request}
        )
        return Response(post_serializer.data)

    @method_decorator(cache_page(300))
    def list(self, *args, **kwargs):
        return super(TagViewSet, self).list(*args, **kwargs)

    @method_decorator(cache_page(300))
    def retrieve(self, *args, **kwargs):
        return super(TagViewSet, self).retrieve(*args, **kwargs)

# not converted to viewset as not all functionality needed
# would have to strip out the functions if used
class UserDetail(generics.RetrieveAPIView):
    lookup_field = "email" # use email so people cannot just change the id to different numbers
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # this is not view set, GET call is get() method
    @method_decorator(cache_page(300))
    def get(self, *args, **kwargs):
        return super(UserDetail, self).get(*args, *kwargs)


# class PostList(generics.ListCreateAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer


# class PostDetail(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [AuthorModifyOrReadOnly | IsAdminUserForObject]
#     queryset = Post.objects.all()
#     # serializer_class = PostSerializer
#     serializer_class = PostDetailSerializer


# using viewsets
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [AuthorModifyOrReadOnly | IsAdminUserForObject]
    queryset = Post.objects.all()

    # user based filtering
    def get_queryset(self):
        if self.request.user.is_anonymous:
            # published only
            queryset = self.queryset.filter(published_at__lte=timezone.now())

        elif not self.request.user.is_staff:
            # allow all
            queryset = self.queryset
        else:
            queryset = self.queryset.filter(
                Q(published_at__lte=timezone.now()) | Q(author=self.request.user)
            )

        time_period_name = self.kwargs.get("period_name")

        if not time_period_name:
            # no further filtering required
            return queryset

        if time_period_name == "new":
            return queryset.filter(
                published_at__gte=timezone.now() - timedelta(hours=1)
            )
        elif time_period_name == "today":
            return queryset.filter(
                published_at__date=timezone.now().date(),
            )
        elif time_period_name == "week":
            return queryset.filter(published_at__gte=timezone.now() - timedelta(days=7))
        else:
            raise Http404(
                f"Time period {time_period_name} is not valid, should be "
                f"'new', 'today' or 'week'"
            )


    def get_serializer_class(self):
        # need this for different returns for GET and POST (list and create)
        if self.action in ("list", "create"): 
            return PostSerializer
        return PostDetailSerializer

    # get own posts
    @method_decorator(cache_page(300))
    @method_decorator(vary_on_headers("Authorization"))
    @method_decorator(vary_on_cookie)
    @action(methods=["get"], detail=False, name="Posts by the logged in user")
    def mine(self, request):
        if request.user.is_anonymous:
            raise PermissionDenied("You must be logged in to see which Posts are yours")
        posts = self.get_queryset().filter(author=request.user)
        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response(serializer.data)

    # cache only list API, in viewset, GET call is list() method
    @method_decorator(cache_page(120))
    @method_decorator(vary_on_headers("Authorization", "Cookie")) # since query set chagnes according to user
    def list(self, *args, **kwargs):
        return super(PostViewSet, self).list(*args, **kwargs)     