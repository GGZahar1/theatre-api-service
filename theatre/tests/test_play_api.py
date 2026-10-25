from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from theatre.models import Play, Actor, Genre, TheatreHall, Performance
from theatre.serializers import PlaySerializer, PlayRetrieveSerializer

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")


def create_play(**params):
    defaults = {
        "title": "Hamlet",
        "description":
            "Prince Hamlet seeks revenge"
            " for his father's murder and"
            " struggles with betrayal, justice, and death.",
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


def create_actor(**params):
    defaults = {
        "first_name": "William",
        "last_name": "Shakespeare",
    }
    defaults.update(params)
    return Actor.objects.create(**defaults)


def create_genre(**params):
    defaults = {
        "name": "Tragedy"
    }
    defaults.update(params)
    return Genre.objects.create(**defaults)


def create_performance(**params):
    theatre_hall = TheatreHall.objects.create(
        name="Test Hall",
        rows=15,
        seats_in_row=15
    )
    defaults = {
        "play": None,
        "show_time": "2022-06-02 14:00:00",
        "theatre_hall": theatre_hall
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


class UnauthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_play_list_unauthenticated(self):
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="useremail@gmail.com",
            password="userpassword"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_play_list(self):
        create_play()
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        plays = Play.objects.all()
        serializer = PlaySerializer(plays, many=True)
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(res.data["count"], plays.count())

    def test_get_play_retrieve(self):
        play = create_play()
        res = self.client.get(reverse("theatre:play-detail", args=(play.id,)))
        serializer = PlayRetrieveSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_play_as_non_admin(self):
        res = self.client.post(
            PLAY_URL,
            data={
                "title":
                    "Hamlet", "description": "Prince Hamlet seeks"
                    " revenge for his father's murder and"
                    " struggles with betrayal, justice, and death.",
            },
            format="json"
        )
        plays = Play.objects.all()
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(plays.count(), 0)

    def test_create_play_as_admin(self):
        actor = create_actor()
        genre = create_genre()
        user_admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            password="qwerty3"
        )
        self.client.force_authenticate(user=user_admin)
        res = self.client.post(
            PLAY_URL,
            data={
                "title": "Hamlet",
                "description": "Prince Hamlet seeks revenge"
                               " for his father's murder and"
                               " struggles with betrayal,"
                               " justice, and death.",
                "actors": [actor.id,],
                "genres": [genre.id,],
            },
            format="json"
        )
        plays = Play.objects.all()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(plays.count(), 1)

    def test_filter_play_by_title(self):
        play1 = create_play()
        play2 = create_play(title="TestTitle")
        actor1 = create_actor()
        genre1 = create_genre()
        play1.actors.add(actor1)
        play1.genres.add(genre1)
        play2.actors.add(actor1)
        play2.genres.add(genre1)
        res = self.client.get(PLAY_URL, {"title": "Ham"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], play1.id)

    def test_filter_play_by_actors(self):
        play1 = create_play()
        play2 = create_play()
        actor1 = create_actor()
        actor2 = create_actor(first_name="John")
        genre = create_genre()
        play1.actors.add(actor1)
        play1.genres.add(genre)
        play2.actors.add(actor2)
        play2.genres.add(genre)
        res = self.client.get(PLAY_URL, {"actors": [actor1.id,]})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], play1.id)

    def test_filter_play_by_genres(self):
        play1 = create_play()
        play2 = create_play()
        actor = create_actor()
        genre1 = create_genre()
        genre2 = create_genre(name="Comedy")
        play1.actors.add(actor)
        play1.genres.add(genre1)
        play2.actors.add(actor)
        play2.genres.add(genre2)
        res = self.client.get(PLAY_URL, {"genres": [genre1.id,]})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], play1.id)
