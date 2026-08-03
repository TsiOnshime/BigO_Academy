import pytest
import jwt
from datetime import datetime, timedelta, timezone
from django.test import TestCase, Client
import json
from uuid import uuid4

from domain.enums import StudentPaymentStatus


def make_token(user_id=None, role="ADMIN", secret="django-insecure-^s0)!65!%2sgjnpdp%_v__!)353^s^sscl=mi(!tjfge_scf!9"):
    """Helper to generate a test JWT."""
    return jwt.encode({
        "userId": str(user_id or uuid4()),
        "email": "test@example.com",
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }, secret, algorithm="HS256")


class TestStudentPaymentEndpoints(TestCase):

    def setUp(self):
        self.client = Client()
        self.student_id = str(uuid4())
        self.admin_token = make_token(role="ADMIN")
        self.student_token = make_token(
            user_id=self.student_id, role="STUDENT"
        )

    def test_admin_can_record_student_payment(self):
        """Admin records a payment — returns 201 with PENDING status."""
        response = self.client.post(
            f"/api/v1/payments/students/{self.student_id}/",
            data=json.dumps({
                "paymentMonth": "2025-07",
                "amount": 500.0,
                "currency": "ETB",
                "dueDate": "2025-07-31",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == StudentPaymentStatus.PENDING.value
        assert data["amount"] == 500.0
        assert data["paymentMonth"] == "2025-07"

    def test_duplicate_payment_returns_409(self):
        """Recording payment for same student and month twice returns 409."""
        payload = {
            "paymentMonth": "2025-07",
            "amount": 500.0,
            "currency": "ETB",
            "dueDate": "2025-07-31",
        }
        self.client.post(
            f"/api/v1/payments/students/{self.student_id}/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        response = self.client.post(
            f"/api/v1/payments/students/{self.student_id}/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        assert response.status_code == 409

    def test_student_can_submit_reference(self):
        """Student submits payment reference — returns 201."""
        response = self.client.post(
            f"/api/v1/payments/students/{self.student_id}/submit-reference/",
            data=json.dumps({
                "paymentMonth": "2025-07",
                "referenceNumber": "TXN-2025-07-ABC123",
                "amount": 500.0,
                "currency": "ETB",
                "dueDate": "2025-07-31",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}",
        )

        assert response.status_code == 201
        assert response.json()["referenceNumber"] == "TXN-2025-07-ABC123"

    def test_admin_can_verify_payment(self):
        """Admin verifies a PENDING payment — status becomes PAID."""
        # Record payment first
        record_response = self.client.post(
            f"/api/v1/payments/students/{self.student_id}/",
            data=json.dumps({
                "paymentMonth": "2025-07",
                "amount": 500.0,
                "currency": "ETB",
                "dueDate": "2025-07-31",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )
        payment_id = record_response.json()["id"]

        # Verify it
        response = self.client.patch(
            f"/api/v1/payments/students/{self.student_id}/payments/{payment_id}/status/",
            data=json.dumps({
                "status": "PAID",
                "note": "Verified with bank",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StudentPaymentStatus.PAID.value
        assert data["verifiedAt"] is not None

    def test_invalid_status_transition_returns_400(self):
        """PAID → PENDING transition returns 400."""
        # Record and verify
        record_response = self.client.post(
            f"/api/v1/payments/students/{self.student_id}/",
            data=json.dumps({
                "paymentMonth": "2025-07",
                "amount": 500.0,
                "currency": "ETB",
                "dueDate": "2025-07-31",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )
        payment_id = record_response.json()["id"]

        self.client.patch(
            f"/api/v1/payments/students/{self.student_id}/payments/{payment_id}/status/",
            data=json.dumps({"status": "PAID"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        # Try invalid transition PAID → PENDING
        response = self.client.patch(
            f"/api/v1/payments/students/{self.student_id}/payments/{payment_id}/status/",
            data=json.dumps({"status": "PENDING"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        assert response.status_code == 400

    def test_student_cannot_access_another_students_payments(self):
        """Student cannot view another student's payment history."""
        other_student_id = str(uuid4())
        response = self.client.get(
            f"/api/v1/payments/students/{other_student_id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}",
        )

        assert response.status_code == 403

    def test_unauthenticated_request_returns_401(self):
        """Request without token returns 401."""
        response = self.client.get(
            f"/api/v1/payments/students/{self.student_id}/"
        )
        assert response.status_code == 401

    def test_payment_summary_report(self):
        """Admin can get payment summary with correct counts."""
        # Record some payments
        for i in range(3):
            sid = str(uuid4())
            self.client.post(
                f"/api/v1/payments/students/{sid}/",
                data=json.dumps({
                    "paymentMonth": "2025-07",
                    "amount": 500.0,
                    "currency": "ETB",
                    "dueDate": "2025-07-31",
                }),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
            )

        response = self.client.get(
            "/api/v1/payments/reports/summary/?month=2025-07",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
        )

        assert response.status_code == 200
        data = response.json()
        assert "studentPayments" in data
        assert data["studentPayments"]["totalPending"] >= 3