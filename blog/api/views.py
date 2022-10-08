from rest_framework import generics

from blog.models import Post

from blango_auth.models import User
from blog.api.serializers import PostSerializer, UserSerializer, PostDetailSerializer

from blog.api.permissions import AuthorModifyOrReadOnly, IsAdminUserForObject

class UserDetail(generics.RetrieveAPIView):
    lookup_field = "email" # use email so people cannot just change the id to different numbers
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PostList(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AuthorModifyOrReadOnly | IsAdminUserForObject]
    queryset = Post.objects.all()
    # serializer_class = PostSerializer
    serializer_class = PostDetailSerializer