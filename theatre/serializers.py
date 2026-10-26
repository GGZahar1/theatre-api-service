from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)


class ActorSerializer(ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class PlaySerializer(ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres", "image")


class PlayListSerializer(ModelSerializer):
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres", "image")


class PlayImageSerializer(ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "image")


class PlayRetrieveSerializer(ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres", "image")


class TheatreHallSerializer(ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PerformanceSerializer(ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall")

    def validate_show_time(self, value):
        if self.instance and self.instance.show_time == value:
            return value

        if value < timezone.now():
            raise ValidationError(
               "The performance time cannot be in the past."
            )
        return value


class PerformanceListSerializer(ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
    theatre_hall_capacity = serializers.IntegerField(
        source="theatre_hall.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "show_time",
            "play_title",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "tickets_available",
        )


class TicketSeatsSerializer(ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class PerformanceRetrieveSerializer(ModelSerializer):
    play = PlayListSerializer(read_only=True, many=False)
    theatre_hall = TheatreHallSerializer(read_only=True, many=False)
    taken_places = TicketSeatsSerializer(
        source="tickets",
        read_only=True,
        many=True
    )

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall", "taken_places")


class TicketSerializer(ModelSerializer):
    def validate(self, attrs):
        data = super().validate(attrs=attrs)

        row = attrs.get("row", self.instance.row if self.instance else None)
        seat = attrs.get("seat", self.instance.seat if self.instance else None)
        performance = attrs.get(
            "performance",
            self.instance.performance if self.instance else None,
        )

        if row is not None and seat is not None and performance is not None:
            Ticket.validate_ticket(
                row,
                seat,
                performance.theatre_hall,
                ValidationError,
            )

        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(read_only=True, many=False)


class ReservationSerializer(ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
