from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

REGISTRATION_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
REFRESH_TOKEN_URL = reverse("user:token_refresh")
ME_URL = reverse("user:me")

class UserTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="userwindows@gmail.com",
            password="grapes888"
        )
        self.client = APIClient()

    def test_user_registration(self):
        res = self.client.post(
                REGISTRATION_URL,
                data={
                    "email": "useremail@gmail.com",
                    "password": "qwerty123"
                },
                format="json"
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_get_token_for_valid_user(self):
        res = self.client.post(
            TOKEN_URL,
            data={
                "email": self.user.email,
                "password": "grapes888"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_get_token_with_invalid_password(self):
        res = self.client.post(
            TOKEN_URL,
            data={
                "email": self.user.email,
                "password": "qwerty"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)

    def test_get_token_for_nonexistent_user(self):
        res = self.client.post(
            TOKEN_URL,
            data={
                "email": "anonuser@gmail.com",
                "password": "anonuser1"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_refresh_token(self):
        res = self.client.post(
                TOKEN_URL,
                data={
                    "email": self.user.email,
                    "password": "grapes888"
                },
                format="json"
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", res.data)
        self.assertIn("access", res.data)
        refresh = res.data["refresh"]
        res2 = self.client.post(
            REFRESH_TOKEN_URL,
            data={
                "refresh": refresh,
            },
            format="json"
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertIn("access", res2.data)


    def test_get_refresh_token_with_invalid_token(self):
        res = self.client.post(
            REFRESH_TOKEN_URL,
            data={
                "refresh": "yyi42428hhftQu048klkjhf09"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", res.data)

    def test_get_get_me(self):
        res = self.client.post(
            TOKEN_URL,
            data={
                "email": self.user.email,
                "password": "grapes888"
            },
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        access_token = res.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        res2 = self.client.get(ME_URL)

        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["email"], self.user.email)

    def test_get_me_for_unauthenticated_user(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
