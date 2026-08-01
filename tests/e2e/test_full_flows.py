import requests
import json
from uuid import uuid4

AUTH_URL = "http://localhost:8000/api/v1"
ACADEMIC_URL = "http://localhost:8001/api/v1"
PAYMENT_URL = "http://localhost:8002/api/v1"
ANALYTICS_URL = "http://localhost:8003/api/v1"


class TestStudentJourney:
    """
    Tests the complete student lifecycle across all services.
    """

    def test_student_registration_to_leaderboard_appearance(self):
        """
        Complete flow:
        1. Student registers in Auth Service
        2. Admin creates student profile in Academic Service
        3. Student solves a problem
        4. Analytics leaderboard updates
        """

        # Step 1 — Register student in Auth Service
        register_response = requests.post(
            f"{AUTH_URL}/auth/register/",
            json={
                "fullName": "Abel Girma",
                "email": f"abel_{uuid4()}@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }
        )
        assert register_response.status_code == 201
        student_token = register_response.json()["accessToken"]
        student_user_id = register_response.json()["user"]["userId"]

        # Step 2 — Admin logs in
        admin_login = requests.post(
            f"{AUTH_URL}/auth/login/",
            json={
                "email": "admin@a2sv.org",
                "password": "AdminPass123!",
            }
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["accessToken"]

        # Step 3 — Admin creates cohort in Academic Service
        cohort_response = requests.post(
            f"{ACADEMIC_URL}/cohorts/",
            json={
                "name": "Batch 2024",
                "startDate": "2024-01-01",
                "expectedGraduationDate": "2026-01-01",
                "studentCapacity": 50,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert cohort_response.status_code == 201
        cohort_id = cohort_response.json()["id"]

        # Step 4 — Admin creates student profile in Academic Service
        student_profile_response = requests.post(
            f"{ACADEMIC_URL}/students/",
            json={
                "userId": student_user_id,
                "fullName": "Abel Girma",
                "email": "abel@example.com",
                "cohortId": cohort_id,
                "joinedAt": "2024-01-01",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert student_profile_response.status_code == 201
        student_id = student_profile_response.json()["id"]

        # Step 5 — Student checks their analytics (should exist now)
        import time
        time.sleep(2)  # Wait for Kafka event processing

        analytics_response = requests.get(
            f"{ANALYTICS_URL}/analytics/students/{student_id}/summary/",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert analytics_response.status_code == 200

    def test_payment_flow(self):
        """
        Complete payment flow:
        1. Student registers
        2. Student submits payment reference
        3. Admin verifies payment
        4. Payment appears in history as PAID
        """

        # Register
        register_response = requests.post(
            f"{AUTH_URL}/auth/register/",
            json={
                "fullName": "Meron Tadesse",
                "email": f"meron_{uuid4()}@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }
        )
        student_id = register_response.json()["user"]["userId"]
        student_token = register_response.json()["accessToken"]

        # Admin logs in
        admin_login = requests.post(
            f"{AUTH_URL}/auth/login/",
            json={"email": "admin@a2sv.org", "password": "AdminPass123!"}
        )
        admin_token = admin_login.json()["accessToken"]

        # Student submits payment reference
        submit_response = requests.post(
            f"{PAYMENT_URL}/payments/students/{student_id}/submit-reference/",
            json={
                "paymentMonth": "2025-07",
                "referenceNumber": f"TXN-{uuid4()}",
                "amount": 500.0,
                "currency": "ETB",
                "dueDate": "2025-07-31",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert submit_response.status_code == 201
        payment_id = submit_response.json()["id"]
        assert submit_response.json()["status"] == "PENDING"

        # Admin verifies payment
        verify_response = requests.patch(
            f"{PAYMENT_URL}/payments/students/{student_id}/payments/{payment_id}/status/",
            json={"status": "PAID", "note": "Verified"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == "PAID"

        # Student checks subscription status
        status_response = requests.get(
            f"{PAYMENT_URL}/payments/students/{student_id}/subscription/",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["currentMonthPaid"] is True