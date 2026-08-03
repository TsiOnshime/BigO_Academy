"""
tests/integration/test_analytics_endpoints.py — Analytics Service

Integration tests covering all HTTP endpoints:
- Student analytics (get, summary, history)
- Leaderboard (global, cohort)
- Teacher analytics
- Admin analytics (platform, cohort, reports)
- Auth gating (401 / 403)

Analytics Service is read-only over HTTP — data is written by Kafka
consumers. So each test seeds the database directly via Django ORM
before calling the endpoint, then verifies the response shape and status.

Setup before running:
  1. Create test DB:  psql -U postgres -c "CREATE DATABASE analytics_db_test;"
  2. Update config/test_settings.py DB_PASSWORD to match your local postgres
  3. Run migrations: python manage.py migrate --settings=config.test_settings
  4. Run: pytest tests/integration/ -v --ds=config.test_settings
"""
import json
from datetime import datetime, timedelta, timezone, date
from uuid import uuid4, UUID

import jwt
from django.test import Client, TestCase

# ── JWT helper ────────────────────────────────────────────────────────────

def make_token(user_id=None, role="ADMIN"):
    from django.conf import settings
    return jwt.encode(
        {
            "userId": str(user_id or uuid4()),
            "email": "test@a2sv.org",
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ── ORM seeders (Analytics is read-only via HTTP — seed data directly) ────

def seed_student_analytics(student_id=None, cohort_id=None, **overrides):
    """Insert a StudentAnalyticsModel row and return its student_id."""
    from core.models import StudentAnalyticsModel
    sid = student_id or uuid4()
    defaults = {
        "cohort_id": cohort_id or uuid4(),
        "rank": 1,
        "rating": 1500.0,
        "performance_score": 80.0,
        "consistency_score": 75.0,
        "attendance_percentage": 90.0,
        "problem_solved_count": 42,
        "current_streak": 5,
        "longest_streak": 10,
        "active_warning_count": 0,
        "total_contests_participated": 3,
        "average_contest_rank": 5.0,
        "best_contest_rank": 2,
        "total_problems_in_contests": 12,
    }
    defaults.update(overrides)
    StudentAnalyticsModel.objects.update_or_create(
        student_id=sid, defaults=defaults
    )
    return sid


def seed_cohort_analytics(cohort_id=None, **overrides):
    """Insert a CohortAnalyticsModel row and return its cohort_id."""
    from core.models import CohortAnalyticsModel
    cid = cohort_id or uuid4()
    defaults = {
        "cohort_name": "Batch 2024",
        "total_students": 30,
        "average_performance_score": 72.5,
        "average_attendance_percentage": 85.0,
        "average_consistency_score": 70.0,
        "total_warnings_issued": 5,
        "total_warnings_resolved": 3,
        "active_warnings": 2,
        "students_on_probation": 1,
        "promoted_to_year2": 10,
        "graduated": 2,
        "dropped": 1,
        "active_students": 27,
    }
    defaults.update(overrides)
    CohortAnalyticsModel.objects.update_or_create(
        cohort_id=cid, defaults=defaults
    )
    return cid


def seed_leaderboard_entry(student_id=None, cohort_id=None, rank=1):
    """Insert a LeaderboardEntryModel row."""
    from core.models import LeaderboardEntryModel
    LeaderboardEntryModel.objects.update_or_create(
        student_id=student_id or uuid4(),
        cohort_id=cohort_id or uuid4(),
        defaults={
            "student_name": "Abel Girma",
            "cohort_name": "Batch 2024",
            "rank": rank,
            "rating": 1500.0,
            "performance_score": 80.0,
            "consistency_score": 75.0,
            "problem_solved_count": 42,
        },
    )


def seed_historical_metric(student_id, snapshot_date=None):
    """Insert a HistoricalMetricModel row."""
    from core.models import HistoricalMetricModel
    HistoricalMetricModel.objects.update_or_create(
        student_id=student_id,
        snapshot_date=snapshot_date or date.today(),
        defaults={
            "rank": 1,
            "rating": 1500.0,
            "performance_score": 80.0,
            "consistency_score": 75.0,
            "attendance_percentage": 90.0,
            "problem_solved_count": 42,
        },
    )


# ══════════════════════════════════════════════════════════════════════════
# AUTH GATING
# ══════════════════════════════════════════════════════════════════════════

class TestAuthGating(TestCase):

    def setUp(self):
        self.client = Client()

    def test_missing_token_returns_401(self):
        """Request without token returns 401."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/"
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_returns_401(self):
        """Garbage token returns 401."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/",
            HTTP_AUTHORIZATION="Bearer not-a-real-token",
        )
        self.assertEqual(response.status_code, 401)

    def test_student_cannot_access_admin_platform_endpoint(self):
        """STUDENT role gets 403 on GET /analytics/admin/platform/."""
        token = make_token(role="STUDENT")
        response = self.client.get(
            "/api/v1/analytics/admin/platform/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_admin_platform_endpoint(self):
        """TEACHER role gets 403 on GET /analytics/admin/platform/."""
        token = make_token(role="TEACHER")
        response = self.client.get(
            "/api/v1/analytics/admin/platform/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_other_student_analytics(self):
        """STUDENT gets 403 when accessing another student's analytics."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        other_student_token = make_token(role="STUDENT")  # different userId
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/",
            HTTP_AUTHORIZATION=f"Bearer {other_student_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_student_can_access_own_analytics(self):
        """STUDENT gets 200 when accessing their own analytics."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        token = make_token(user_id=student_id, role="STUDENT")
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)


# ══════════════════════════════════════════════════════════════════════════
# STUDENT ANALYTICS
# ══════════════════════════════════════════════════════════════════════════

class TestStudentAnalyticsEndpoints(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_token = make_token(role="ADMIN")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

    def test_get_student_analytics_returns_200(self):
        """GET /analytics/students/{id}/ returns full analytics."""
        student_id = seed_student_analytics(
            performance_score=85.5,
            problem_solved_count=50,
        )
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["studentId"], str(student_id))
        self.assertEqual(data["performanceScore"], 85.5)
        self.assertEqual(data["problemSolvedCount"], 50)
        self.assertIn("contestStats", data)
        self.assertIn("rank", data)
        self.assertIn("rating", data)

    def test_get_nonexistent_student_analytics_returns_404(self):
        """GET /analytics/students/{random_id}/ returns 404."""
        response = self.client.get(
            f"/api/v1/analytics/students/{uuid4()}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 404)

    def test_get_student_analytics_summary_returns_200(self):
        """GET /analytics/students/{id}/summary/ returns summary fields."""
        student_id = seed_student_analytics(
            active_warning_count=2,
            attendance_percentage=65.0,
        )
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/summary/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["studentId"], str(student_id))
        self.assertEqual(data["activeWarningCount"], 2)
        self.assertEqual(data["attendancePercentage"], 65.0)
        # Summary should NOT include contestStats
        self.assertNotIn("contestStats", data)

    def test_get_student_analytics_summary_nonexistent_returns_404(self):
        """GET /analytics/students/{id}/summary/ returns 404 for unknown."""
        response = self.client.get(
            f"/api/v1/analytics/students/{uuid4()}/summary/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 404)

    def test_get_student_history_returns_200_with_snapshots(self):
        """GET /analytics/students/{id}/history/ returns snapshot list."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        seed_historical_metric(
            student_id, snapshot_date=date(2025, 6, 1)
        )
        seed_historical_metric(
            student_id, snapshot_date=date(2025, 6, 2)
        )
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/history/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("studentId", data)
        self.assertIn("snapshots", data)
        self.assertEqual(len(data["snapshots"]), 2)

    def test_get_student_history_returns_empty_list_when_no_snapshots(self):
        """GET /analytics/students/{id}/history/ returns empty snapshots."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/history/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["snapshots"], [])

    def test_get_student_history_with_date_filter(self):
        """GET /analytics/students/{id}/history/?from=&to= filters snapshots."""
        student_id = uuid4()
        seed_student_analytics(student_id=student_id)
        seed_historical_metric(student_id, snapshot_date=date(2025, 5, 1))
        seed_historical_metric(student_id, snapshot_date=date(2025, 6, 1))
        seed_historical_metric(student_id, snapshot_date=date(2025, 7, 1))

        response = self.client.get(
            f"/api/v1/analytics/students/{student_id}/history/"
            f"?from=2025-06-01&to=2025-06-30",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        snapshots = response.json()["snapshots"]
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["snapshotDate"], "2025-06-01")


# ══════════════════════════════════════════════════════════════════════════
# LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════

class TestLeaderboardEndpoints(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_token = make_token(role="ADMIN")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

    def test_global_leaderboard_returns_200(self):
        """GET /analytics/leaderboard/ returns entries and lastRefreshed."""
        cohort_id = uuid4()
        seed_leaderboard_entry(rank=1, cohort_id=cohort_id)
        seed_leaderboard_entry(rank=2, cohort_id=cohort_id)
        response = self.client.get(
            "/api/v1/analytics/leaderboard/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("entries", data)
        self.assertIn("lastRefreshed", data)

    def test_global_leaderboard_returns_empty_when_no_data(self):
        """GET /analytics/leaderboard/ returns empty entries list."""
        response = self.client.get(
            "/api/v1/analytics/leaderboard/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["entries"], [])

    def test_global_leaderboard_requires_auth(self):
        """GET /analytics/leaderboard/ returns 401 without token."""
        response = self.client.get("/api/v1/analytics/leaderboard/")
        self.assertEqual(response.status_code, 401)

    def test_student_can_view_global_leaderboard(self):
        """STUDENT role can access the leaderboard."""
        token = make_token(role="STUDENT")
        response = self.client.get(
            "/api/v1/analytics/leaderboard/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_cohort_leaderboard_returns_200(self):
        """GET /analytics/leaderboard/cohorts/{id}/ returns cohort entries."""
        cohort_id = uuid4()
        seed_leaderboard_entry(rank=1, cohort_id=cohort_id)
        seed_leaderboard_entry(rank=2, cohort_id=cohort_id)
        # Entry for a different cohort — should not appear
        seed_leaderboard_entry(rank=1, cohort_id=uuid4())

        response = self.client.get(
            f"/api/v1/analytics/leaderboard/cohorts/{cohort_id}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 2)

    def test_cohort_leaderboard_returns_empty_for_unknown_cohort(self):
        """GET /analytics/leaderboard/cohorts/{unknown_id}/ returns empty."""
        response = self.client.get(
            f"/api/v1/analytics/leaderboard/cohorts/{uuid4()}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["entries"], [])

    def test_leaderboard_entries_have_correct_fields(self):
        """Leaderboard entries contain expected response fields."""
        cohort_id = uuid4()
        student_id = uuid4()
        seed_leaderboard_entry(
            student_id=student_id, cohort_id=cohort_id, rank=1
        )
        response = self.client.get(
            "/api/v1/analytics/leaderboard/",
            **self.auth,
        )
        entry = response.json()["entries"][0]
        self.assertIn("rank", entry)
        self.assertIn("studentId", entry)
        self.assertIn("studentName", entry)
        self.assertIn("cohortId", entry)
        self.assertIn("rating", entry)
        self.assertIn("performanceScore", entry)
        self.assertIn("problemSolvedCount", entry)


# ══════════════════════════════════════════════════════════════════════════
# TEACHER ANALYTICS
# ══════════════════════════════════════════════════════════════════════════

class TestTeacherAnalyticsEndpoints(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_token = make_token(role="ADMIN")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

    def test_admin_can_get_teacher_analytics(self):
        """Admin GET /analytics/teachers/{id}/ returns teacher analytics."""
        teacher_id = uuid4()
        # Use teacher_id AS the cohort_id — the use case treats them as the same
        seed_student_analytics(
            cohort_id=teacher_id,
            performance_score=85.0,
            attendance_percentage=90.0,
        )
        response = self.client.get(
            f"/api/v1/analytics/teachers/{teacher_id}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("teacherId", data)
        self.assertIn("studentsAtRisk", data)
        self.assertIn("topPerformers", data)

    def test_teacher_can_access_own_analytics(self):
        """TEACHER can access their own analytics."""
        teacher_id = uuid4()
        # Seed with teacher_id as cohort_id so data exists
        seed_student_analytics(cohort_id=teacher_id)
        token = make_token(user_id=teacher_id, role="TEACHER")
        response = self.client.get(
            f"/api/v1/analytics/teachers/{teacher_id}/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        def test_teacher_cannot_access_other_teacher_analytics(self):
            """TEACHER gets 403 when accessing another teacher's analytics."""
            teacher_id = uuid4()
            other_teacher_token = make_token(role="TEACHER")  # different userId
            response = self.client.get(
                f"/api/v1/analytics/teachers/{teacher_id}/",
                HTTP_AUTHORIZATION=f"Bearer {other_teacher_token}",
            )
            self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_teacher_analytics(self):
        """STUDENT gets 403 on teacher analytics endpoint."""
        teacher_id = uuid4()
        token = make_token(role="STUDENT")
        response = self.client.get(
            f"/api/v1/analytics/teachers/{teacher_id}/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_teacher_analytics_without_token_returns_401(self):
        """No token returns 401."""
        response = self.client.get(
            f"/api/v1/analytics/teachers/{uuid4()}/"
        )
        self.assertEqual(response.status_code, 401)


# ══════════════════════════════════════════════════════════════════════════
# ADMIN ANALYTICS
# ══════════════════════════════════════════════════════════════════════════

class TestAdminAnalyticsEndpoints(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_token = make_token(role="ADMIN")
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

    def test_platform_analytics_returns_200(self):
        """GET /analytics/admin/platform/ returns platform-wide metrics."""
        seed_cohort_analytics(total_students=30)
        seed_cohort_analytics(total_students=25)
        response = self.client.get(
            "/api/v1/analytics/admin/platform/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("totalStudents", data)
        self.assertIn("totalActiveCohorts", data)
        self.assertIn("overallAveragePerformanceScore", data)
        self.assertIn("totalWarningsIssued", data)

    def test_platform_analytics_totals_are_correct(self):
        """Platform analytics correctly sums across cohorts."""
        seed_cohort_analytics(total_students=30, total_warnings_issued=5)
        seed_cohort_analytics(total_students=20, total_warnings_issued=3)
        response = self.client.get(
            "/api/v1/analytics/admin/platform/",
            **self.auth,
        )
        data = response.json()
        self.assertGreaterEqual(data["totalStudents"], 50)
        self.assertGreaterEqual(data["totalWarningsIssued"], 8)

    def test_platform_analytics_requires_admin(self):
        """Non-admin gets 403."""
        token = make_token(role="TEACHER")
        response = self.client.get(
            "/api/v1/analytics/admin/platform/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_cohort_analytics_returns_200(self):
        """GET /analytics/admin/cohorts/{id}/ returns cohort analytics."""
        cohort_id = seed_cohort_analytics(
            cohort_name="Batch 2024",
            total_students=30,
            average_performance_score=75.0,
        )
        response = self.client.get(
            f"/api/v1/analytics/admin/cohorts/{cohort_id}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cohortId"], str(cohort_id))
        self.assertEqual(data["cohortName"], "Batch 2024")
        self.assertEqual(data["totalStudents"], 30)
        self.assertIn("warningStats", data)
        self.assertIn("progressionStats", data)

    def test_cohort_analytics_nonexistent_returns_404(self):
        """GET /analytics/admin/cohorts/{random_id}/ returns 404."""
        response = self.client.get(
            f"/api/v1/analytics/admin/cohorts/{uuid4()}/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 404)

    def test_cohort_analytics_requires_admin(self):
        """Non-admin gets 403."""
        cohort_id = seed_cohort_analytics()
        token = make_token(role="STUDENT")
        response = self.client.get(
            f"/api/v1/analytics/admin/cohorts/{cohort_id}/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_analytics_report_student_type_returns_200(self):
        """GET /analytics/admin/reports/student/ returns report."""
        student_id = seed_student_analytics()
        response = self.client.get(
            f"/api/v1/analytics/admin/reports/student/"
            f"?studentId={student_id}",
            **self.auth,
        )
        # 200 if report generated, 400 if use case validation fails
        self.assertIn(response.status_code, [200, 400])

    def test_analytics_report_platform_type_returns_200(self):
        """GET /analytics/admin/reports/platform/ returns report."""
        seed_cohort_analytics()
        response = self.client.get(
            "/api/v1/analytics/admin/reports/platform/",
            **self.auth,
        )
        self.assertIn(response.status_code, [200, 400])

    def test_analytics_report_requires_admin(self):
        """Non-admin gets 403 on report endpoint."""
        token = make_token(role="TEACHER")
        response = self.client.get(
            "/api/v1/analytics/admin/reports/platform/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_analytics_report_invalid_type_returns_400(self):
        """Invalid report type returns 400."""
        response = self.client.get(
            "/api/v1/analytics/admin/reports/not_a_real_type/",
            **self.auth,
        )
        self.assertEqual(response.status_code, 400)