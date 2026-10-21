from rest_framework.serializers import ModelSerializer

from theatre.models import Actor, Genre


class ActorSerializer(ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name")


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")
