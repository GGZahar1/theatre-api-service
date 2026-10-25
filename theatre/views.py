from datetime import datetime
from django.db.models import F, Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from theatre.models import (
    Actor, Genre,
    Play, TheatreHall,
    Performance, Reservation
    )
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayRetrieveSerializer,
    TheatreHallSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceRetrieveSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    PlayImageSerializer,
)


class ActorViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenreViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer

    def get_queryset(self):
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actors_ids = [int(actor_id) for actor_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = [int(genre_id) for genre_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        elif self.action == "retrieve":
            return PlayRetrieveSerializer
        elif self.action == "upload-image":
            return PlayImageSerializer
        return PlaySerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtering plays by title",
            ),
            OpenApiParameter(
                name="actors",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtering by actors ids (ex: actors=1,2)",
                many=True
            ),
            OpenApiParameter(
                name="genres",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtering by genres ids (ex: genres=1,2)",
                many=True
            )
        ]
    )
    def list(self, request):
        return super().list(request)

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TheatreHallViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PerformanceViewSet(ModelViewSet):
    queryset = Performance.objects.select_related(
        "play",
        "theatre_hall"
    ).annotate(
        tickets_available=(
            F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
            - Count("tickets")
        )
    )
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        play_id_str = self.request.query_params.get("play")

        queryset = self.queryset

        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError("DATE must be in YYYY-MM-DD format")
            queryset = queryset.filter(show_time__date=date)

        if play_id_str:
            try:
                play_id = int(play_id_str)
            except ValueError:
                raise ValidationError("Play ID must be an integer.")
            queryset = queryset.filter(play_id=play_id)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        elif self.action == "retrieve":
            return PerformanceRetrieveSerializer
        return PerformanceSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filtering by date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="play",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filtering performance by play id",
            )
        ]
    )
    def list(self, request):
        return super().list(request)


class ReservationPagination(PageNumberPagination):
    page_size = 3
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 10


class ReservationViewSet(
    GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ReservationPagination

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__performance__play", "tickets__performance__theatre_hall"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
