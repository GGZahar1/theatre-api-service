from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from theatre.tests.test_actor_api import create_actor
from theatre.tests.test_genre_api import create_genre
from theatre.tests.test_play_api import create_performance, create_play
from theatre.models import TheatreHall, Reservation, Ticket, Performance

RESERVATION_URL = reverse("theatre:reservation-list")


class TestReservation(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="useremail@gmail.com",
            password="qwerty"
        )
        self.theatre_hall = TheatreHall.objects.create(
            name="Hall",
            rows=10,
            seats_in_row=10
        )
        self.actor = create_actor()
        self.genre = create_genre()
        self.play = create_play()
        self.play.actors.add(self.actor)
        self.play.genres.add(self.genre)
        self.performance = create_performance(play=self.play, theatre_hall=self.theatre_hall)
        self.client.force_authenticate(user=self.user)

    def test_create_reservation(self):
        res = self.client.post(
            RESERVATION_URL,
            data={
                "tickets":[
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    }
                ]
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 1)

        reservation = Reservation.objects.get()
        self.assertEqual(reservation.user, self.user)

    def test_user_sees_only_own_reservations(self):
        other_user = get_user_model().objects.create_user(
            email="other@gmail.com",
            password="qwerty"
        )

        own_reservation = Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=other_user)

        self.client.force_authenticate(user=self.user)

        response = self.client.get(RESERVATION_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        reservations = response.data["results"]
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations[0]["id"], own_reservation.id)

    def test_unauthorized_user_cannot_create_reservation(self):
        self.client = APIClient()
        res = self.client.post(
            RESERVATION_URL,
            data={
                "tickets":[
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    }
                ]
            }
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_cannot_create_reservation_with_duplicate_seats(self):
        res = self.client.post(
            RESERVATION_URL,
            data={
                "tickets":[
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    },
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    }
                ]
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_cannot_create_reservation_with_different_performances(self):
        performance = Performance.objects.create(
            play=self.play,
            theatre_hall=self.theatre_hall,
            show_time="2022-06-02 14:00:00"
        )
        res = self.client.post(
            RESERVATION_URL,
            data={
                "tickets":[
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    },
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": performance.id,
                    }
                ]
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_reservation_creation_is_atomic(self):
        res = self.client.post(
            RESERVATION_URL,
            data={
                "tickets":[
                    {
                        "row": 1,
                        "seat": 5,
                        "performance": self.performance.id,
                    },
                    {
                        "row": 1000,
                        "seat": 5,
                        "performance": self.performance.id,
                    }
                ]
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
