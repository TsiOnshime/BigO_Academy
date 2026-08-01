import pytest
from django.test import TestCase, Client
from django.urls import reverse
import json


class TestAuthEndpoints(TestCase):

    def setUp(self):
        self.client = Client()

    def test_register_student_returns_201_with_tokens(self):
        """
        POST /api/v1/auth/register
        A new student can register and receives JWT tokens.
        """
        response = self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert data["user"]["email"] == "abel@example.com"
        assert data["user"]["role"] == "STUDENT"

    def test_register_duplicate_email_returns_409(self):
        """Cannot register with an already taken email."""
        payload = {
            "fullName": "Abel Girma",
            "email": "abel@example.com",
            "password": "SecurePass123!",
            "confirmPassword": "SecurePass123!",
        }
        self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Second registration with same email
        response = self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 409

    def test_login_with_correct_credentials_returns_200(self):
        """Registered user can log in and receive tokens."""
        # Register first
        self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )

        # Now login
        response = self.client.post(
            "/api/v1/auth/login/",
            data=json.dumps({
                "email": "abel@example.com",
                "password": "SecurePass123!",
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data

    def test_login_wrong_password_returns_401(self):
        """Wrong password returns 401."""
        self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )

        response = self.client.post(
            "/api/v1/auth/login/",
            data=json.dumps({
                "email": "abel@example.com",
                "password": "WrongPassword!",
            }),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_get_current_user_with_valid_token(self):
        """GET /auth/me returns user info with valid token."""
        # Register and get token
        register_response = self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )
        token = register_response.json()["accessToken"]

        # Use token to get current user
        response = self.client.get(
            "/api/v1/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        assert response.status_code == 200
        assert response.json()["email"] == "abel@example.com"

    def test_get_current_user_without_token_returns_401(self):
        """GET /auth/me without token returns 401."""
        response = self.client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    def test_refresh_token_returns_new_access_token(self):
        """POST /auth/refresh with valid refresh token returns new tokens."""
        register_response = self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )
        refresh_token = register_response.json()["refreshToken"]

        response = self.client.post(
            "/api/v1/auth/refresh/",
            data=json.dumps({"refreshToken": refresh_token}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert "accessToken" in response.json()

    def test_logout_invalidates_refresh_token(self):
        """After logout, the refresh token cannot be used again."""
        register_response = self.client.post(
            "/api/v1/auth/register/",
            data=json.dumps({
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }),
            content_type="application/json",
        )
        tokens = register_response.json()
        access_token = tokens["accessToken"]
        refresh_token = tokens["refreshToken"]

        # Logout
        self.client.post(
            "/api/v1/auth/logout/",
            data=json.dumps({"refreshToken": refresh_token}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        # Try to use the refresh token again
        response = self.client.post(
            "/api/v1/auth/refresh/",
            data=json.dumps({"refreshToken": refresh_token}),
            content_type="application/json",
        )

        assert response.status_code == 401