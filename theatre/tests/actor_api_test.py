from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse

from theatre.models import Actor
from theatre.serializers import ActorSerializer


ACTOR_URL = reverse("theatre:actor-list")


def create_actor(**params):
    defaults = {
        "first_name": "Brad",
        "last_name": "Pitt",
    }
    defaults.update(params)
    return Actor.objects.create(**defaults)


class UnauthenticatedActorApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def get_unauthenticated_user(self):
        res = self.client.get(ACTOR_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@gmail.com",
            password="testpassword",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_actor_list(self):
        create_actor()
        res = self.client.get(ACTOR_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        actors = Actor.objects.all()
        serializer = ActorSerializer(actors, many=True)
        self.assertEqual(res.data["count"], actors.count())
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_actor_as_non_admin(self):
        res = self.client.post(
            ACTOR_URL,
            data={
                "first_name": "Brad",
                "last_name": "Pitt",
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Actor.objects.count(), 0)

    def test_create_actor_as_admin(self):
        user_admin = get_user_model().objects.create_superuser(
            email="adminuser@gmail.com",
            password="adminpassword"
        )
        self.client.force_authenticate(user=user_admin)

        res = self.client.post(
            ACTOR_URL,
            data={
                "first_name": "Tom",
                "last_name": "Welling"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Actor.objects.count(), 1)
