from rest_framework import serializers
from blog.models import Post, Tag, Comment
from blango_auth.models import User

class TagField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(value=data.lower())[0]
        except (TypeError, ValueError):
            self.fail(f"Tag value {data} is invalid")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class CommentSerializer(serializers.ModelSerializer):
    # required is True by default, we want it to be false so if no id, 
    # treat as new comment and add it
    id = serializers.IntegerField(required=False) 
    # serialize creator so it will not just show the id
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "creator", "content", "modified_at", "created_at"]
        readonly = ["modified_at", "created_at"]


class PostSerializer(serializers.ModelSerializer):

    # return tags as list of strings (since it is to many field) instead of list of primary keys, can be updated
    tags = serializers.SlugRelatedField(
        slug_field="value", many=True, queryset=Tag.objects.all()
    )

    # returns author as link to another API call which is updated in urls.py
    # view name is given under urls.py
    author = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(), view_name="api_user_detail", lookup_field="email"
    )

    class Meta:
        model = Post
        fields = "__all__"
        readonly = ["modified_at", "created_at"]


class PostDetailSerializer(PostSerializer):
    comments = CommentSerializer(many=True)

    def update(self, instance, validated_data):
        # remove comments as we want to update it ourselves
        comments = validated_data.pop("comments")
        # use parent method update to update the rest
        instance = super(PostDetailSerializer, self).update(instance, validated_data)

        # handle comment update ourselves, for each comment, if no id consider as new comment and update
        for comment_data in comments:
            if comment_data.get("id"):
                # comment has an ID so was pre-existing
                continue
            comment = Comment(**comment_data)
            comment.creator = self.context["request"].user
            comment.content_object = instance
            comment.save()

        return instance