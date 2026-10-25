from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from theatre.models import Genre
from django.urls import reverse

from theatre.serializers import GenreSerializer

GENRE_URL = reverse("theatre:genre-list")


def create_genre(**params):
    defaults = {
        "name": "Comedy"
    }
    defaults.update(params)
    return Genre.objects.create(**defaults)


class UnauthenticatedGenreApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def get_unauthenticated_user(self):
        res = self.client.get(GENRE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedGenreAPiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="usertest@gmail.com",
            password="userpassword"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_genre_list(self):
        create_genre()
        res = self.client.get(GENRE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)
        self.assertEqual(res.data["count"], genres.count())
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_genre_as_non_admin(self):
        res = self.client.post(
            GENRE_URL,
            data={
                "name": "Tragedy"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Genre.objects.count(), 0)

    def test_create_genre_as_admin(self):
        admin_user = get_user_model().objects.create_superuser(
            email="admin123@gmail.com",
            password="adminpassword"
        )
        self.client.force_authenticate(user=admin_user)
        res = self.client.post(
            GENRE_URL,
            data={
                "name": "Tragedy"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.count(), 1)