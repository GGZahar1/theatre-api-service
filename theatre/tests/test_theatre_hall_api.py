from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from theatre.models import TheatreHall
from theatre.serializers import TheatreHallSerializer

THEATRE_HALL_URL = reverse("theatre:theatrehall-list")


class UnauthenticatedTheatreHallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_theatre_hall_list_unauthenticated(self):
        res = self.client.get(
            THEATRE_HALL_URL
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTheatreHallAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testemail@gmail.com",
            password="testpassword"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_theatre_hall_list(self):
        TheatreHall.objects.create(
            name="Small",
            rows=10,
            seats_in_row=15
        )
        res = self.client.get(
            THEATRE_HALL_URL
        )
        theatre_halls = TheatreHall.objects.all()
        serializer = TheatreHallSerializer(theatre_halls, many=True)
        self.assertEqual(
            res.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(res.data["count"], theatre_halls.count())
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_theatre_hall_as_non_admin(self):
        res = self.client.post(
            THEATRE_HALL_URL,
            data={
                "name": "Small",
                "rows": 10,
                "seats_in_row": 15
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TheatreHall.objects.count(), 0)

    def test_update_theatre_hall_as_non_admin(self):
        theatre_hall = TheatreHall.objects.create(
            name="Small",
            rows=10,
            seats_in_row=15
        )
        res = self.client.patch(
            reverse("theatre:theatrehall-detail", args=(theatre_hall.id,)),
            data={
                "rows": 15
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        theatre_hall.refresh_from_db()
        self.assertEqual(theatre_hall.rows, 10)

    def test_create_theatre_hall_as_admin(self):
        admin = get_user_model().objects.create_superuser(
            email="admin@gmail.com",
            password="qwerty5"
        )
        self.client.force_authenticate(user=admin)
        res = self.client.post(
            THEATRE_HALL_URL,
            data={
                "name": "Small",
                "rows": 10,
                "seats_in_row": 15
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TheatreHall.objects.count(), 1)

    def test_update_theatre_hall_as_admin(self):
        theatre_hall = TheatreHall.objects.create(
            name="Small",
            rows=10,
            seats_in_row=15
        )
        admin = get_user_model().objects.create_superuser(
            email="admin@gmail.com",
            password="qwerty5"
        )
        self.client.force_authenticate(user=admin)
        res = self.client.patch(
            reverse("theatre:theatrehall-detail", args=(theatre_hall.id,)),
            data={
                "name": "Test"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        theatre_hall.refresh_from_db()
        self.assertEqual(theatre_hall.name, "Test")
