from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Performance, TheatreHall
from theatre.tests.test_play_api import create_play, create_performance


PERFORMANCE_URL = reverse("theatre:performance-list")


class UnauthenticatedPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_performance_list_unauthenticated(self):
        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(
            res.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class AuthenticatedPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="useremail@gmail.com",
            password="userpassword",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_performance_list(self):
        performance = create_performance(play=create_play())

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(
            res.data["results"][0]["id"],
            performance.id,
        )
        self.assertEqual(
            res.data["results"][0]["tickets_available"],
            225,
        )

    def test_get_performance_retrieve(self):
        performance = create_performance(play=create_play())

        res = self.client.get(
            reverse(
                "theatre:performance-detail",
                args=(performance.id,),
            )
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], performance.id)

    def test_filter_performance_by_play(self):
        play1 = create_play()
        play2 = create_play(title="Romeo and Juliet")

        performance1 = create_performance(play=play1)
        create_performance(play=play2)

        res = self.client.get(
            PERFORMANCE_URL,
            {"play": play1.id},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(
            res.data["results"][0]["id"],
            performance1.id,
        )

    def test_filter_performance_by_date(self):
        performance1 = create_performance(
            play=create_play(),
            show_time="2026-11-15 14:00:00",
        )
        create_performance(
            play=create_play(title="Romeo and Juliet"),
            show_time="2026-11-16 14:00:00",
        )

        res = self.client.get(
            PERFORMANCE_URL,
            {"date": "2026-11-15"},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(
            res.data["results"][0]["id"],
            performance1.id,
        )

    def test_create_performance_as_non_admin(self):
        play = create_play()
        theatre_hall = TheatreHall.objects.create(
            name="Hall",
            rows=10,
            seats_in_row=10,
        )

        res = self.client.post(
            PERFORMANCE_URL,
            data={
                "play": play.id,
                "theatre_hall": theatre_hall.id,
                "show_time": "2026-11-15 14:00:00",
            },
            format="json",
        )

        self.assertEqual(
            res.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Performance.objects.count(), 0)

    def test_create_performance_as_admin(self):
        play = create_play()
        theatre_hall = TheatreHall.objects.create(
            name="Hall",
            rows=10,
            seats_in_row=10,
        )
        admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            password="qwerty3",
        )
        self.client.force_authenticate(user=admin)

        res = self.client.post(
            PERFORMANCE_URL,
            data={
                "play": play.id,
                "theatre_hall": theatre_hall.id,
                "show_time": "2026-11-15 14:00:00",
            },
            format="json",
        )

        self.assertEqual(
            res.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Performance.objects.count(), 1)

    def test_create_performance_with_invalid_date(self):
        admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            password="admpassword",
        )
        self.client.force_authenticate(user=admin)
        res = self.client.post(
            PERFORMANCE_URL,
            data={
                "play": create_play().id,
                "theatre_hall": TheatreHall.objects.create(
                    name="Hall",
                    rows=10,
                    seats_in_row=10,
                ).id,
                "show_time": "2000-11-15 14:00:00",
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
