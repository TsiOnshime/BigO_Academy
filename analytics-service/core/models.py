from django.db import models
import uuid


class StudentAnalyticsModel(models.Model):
    '''Stores current analytics state for each student'''
    student_id = models.UUIDField(primary_key=True)
    cohort_id = models.UUIDField(null=True, blank=True, db_index=True)
    year_level = models.IntegerField(default=1)
    rank = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    performance_score = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    attendance_percentage = models.FloatField(default=0.0)
    problem_solved_count = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    active_warning_count = models.IntegerField(default=0)
    # Contest stats stored as JSON
    total_contests_participated = models.IntegerField(default=0)
    average_contest_rank = models.FloatField(default=0.0)
    best_contest_rank = models.IntegerField(default=0)
    total_problems_in_contests = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        db_table = "student_analytics"
        indexes = [
            # Top performers per cohort — used by teacher analytics
            models.Index(
                fields=["cohort_id", "-performance_score"],
                name="idx_analytics_cohort_perf",
            ),
            # At-risk students query: attendance < 60 OR performance < 40
            models.Index(
                fields=["cohort_id", "attendance_percentage"],
                name="idx_analytics_attendance",
            ),
            # Global rank ordering — used by leaderboard
            models.Index(
                fields=["rank"],
                name="idx_analytics_rank",
            ),
            # Warning count filter — finds at-risk students
            models.Index(
                fields=["active_warning_count"],
                name="idx_analytics_warnings",
            ),
        ]
    def __str__(self):
        return f"StudentAnalytics({self.student_id}, rank={self.rank})"


class LeaderboardEntryModel(models.Model):
    """Stores leaderboard positions. Refreshed every 5 minutes."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    student_id = models.UUIDField(db_index=True)
    student_name = models.CharField(max_length=200)

    cohort_id = models.UUIDField(db_index=True)
    cohort_name = models.CharField(max_length=200)

    rank = models.IntegerField(db_index=True)
    rating = models.FloatField(default=0.0)
    performance_score = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)

    problem_solved_count = models.IntegerField(default=0)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leaderboard_entry"
        ordering = ["rank"]
        unique_together = [("student_id", "cohort_id")]
        indexes = [
            # Global leaderboard — most common query, ORDER BY rank
            models.Index(
                fields=["rank"],
                name="idx_leaderboard_rank",
            ),
            # Cohort leaderboard — filter by cohort then order by rank
            models.Index(
                fields=["cohort_id", "rank"],
                name="idx_leaderboard_cohort_rank",
            ),
            # Lookup by student — used in student analytics view
            models.Index(
                fields=["student_id"],
                name="idx_leaderboard_student",
            ),
        ]

    def __str__(self):
        return (
            f"LeaderboardEntry("
            f"rank={self.rank}, "
            f"student={self.student_id})"
        )


class HistoricalMetricModel(models.Model):
    """Daily snapshots of student analytics for trend analysis."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    student_id = models.UUIDField(db_index=True)
    snapshot_date = models.DateField(db_index=True)

    rank = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    performance_score = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    attendance_percentage = models.FloatField(default=0.0)

    problem_solved_count = models.IntegerField(default=0)

    class Meta:
        db_table = "historical_metric"
        unique_together = [("student_id", "snapshot_date")]
        ordering = ["snapshot_date"]
        indexes = [
            # Student history queries — filter by student, order by date
            models.Index(
                fields=["student_id", "snapshot_date"],
                name="idx_history_student_date",
            ),
            # Date range queries — from/to date filtering
            models.Index(
                fields=["snapshot_date"],
                name="idx_history_date",
            ),
        ]
    def __str__(self):
        return (
            f"HistoricalMetric("
            f"{self.student_id}, "
            f"{self.snapshot_date})"
        )


class CohortAnalyticsModel(models.Model):
    """Aggregated analytics for each cohort."""

    cohort_id = models.UUIDField(primary_key=True)
    cohort_name = models.CharField(max_length=200)

    total_students = models.IntegerField(default=0)

    average_performance_score = models.FloatField(default=0.0)
    average_attendance_percentage = models.FloatField(default=0.0)
    average_consistency_score = models.FloatField(default=0.0)

    # Warning statistics
    total_warnings_issued = models.IntegerField(default=0)
    total_warnings_resolved = models.IntegerField(default=0)
    active_warnings = models.IntegerField(default=0)
    students_on_probation = models.IntegerField(default=0)

    # Progression statistics
    promoted_to_year2 = models.IntegerField(default=0)
    graduated = models.IntegerField(default=0)
    dropped = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cohort_analytics"
        indexes = [
            # Sort cohorts by performance for admin dashboard
            models.Index(
                fields=["-average_performance_score"],
                name="idx_cohort_perf",
            ),
        ]


class AnalyticsReportModel(models.Model):
    """Stored generated analytics reports."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    report_type = models.CharField(max_length=20)
    generated_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(default=dict)

    class Meta:
        db_table = "analytics_report"
        ordering = ["-generated_at"]

    def __str__(self):
        return (
            f"AnalyticsReport("
            f"{self.report_type}, "
            f"{self.generated_at})"
        )