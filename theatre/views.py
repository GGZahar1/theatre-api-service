from rest_framework.viewsets import ModelViewSet

from theatre.models import Actor, Genre
from theatre.serializers import ActorSerializer, GenreSerializer


class ActorViewSet(ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
