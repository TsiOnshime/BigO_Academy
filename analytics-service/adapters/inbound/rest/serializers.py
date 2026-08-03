from rest_framework import serializers


class ContestStatsSerializer(serializers.Serializer):
    totalContestsParticipated = serializers.IntegerField(
        source="total_contests_participated"
    )
    averageRank = serializers.FloatField(source="average_rank")
    bestRank = serializers.IntegerField(source="best_rank")
    totalProblemsSolvedInContests = serializers.IntegerField(
        source="total_problems_solved_in_contests"
    )


class StudentAnalyticsSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    rank = serializers.IntegerField()
    rating = serializers.FloatField()
    performanceScore = serializers.FloatField(source="performance_score")
    consistencyScore = serializers.FloatField(source="consistency_score")
    attendancePercentage = serializers.FloatField(
        source="attendance_percentage"
    )
    problemSolvedCount = serializers.IntegerField(
        source="problem_solved_count"
    )
    currentStreak = serializers.IntegerField(source="current_streak")
    longestStreak = serializers.IntegerField(source="longest_streak")
    contestStats = ContestStatsSerializer(source="contest_stats")
    lastUpdated = serializers.DateTimeField(source="last_updated")


class StudentAnalyticsSummarySerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    rank = serializers.IntegerField()
    rating = serializers.FloatField()
    performanceScore = serializers.FloatField(source="performance_score")
    consistencyScore = serializers.FloatField(source="consistency_score")
    attendancePercentage = serializers.FloatField(
        source="attendance_percentage"
    )
    activeWarningCount = serializers.IntegerField(
        source="active_warning_count"
    )
    lastUpdated = serializers.DateTimeField(source="last_updated")


class HistoricalMetricSnapshotSerializer(serializers.Serializer):
    snapshotDate = serializers.DateField(source="snapshot_date")
    rank = serializers.IntegerField()
    rating = serializers.FloatField()
    performanceScore = serializers.FloatField(source="performance_score")
    consistencyScore = serializers.FloatField(source="consistency_score")
    attendancePercentage = serializers.FloatField(
        source="attendance_percentage"
    )
    problemSolvedCount = serializers.IntegerField(
        source="problem_solved_count"
    )


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    studentId = serializers.UUIDField(source="student_id")
    studentName = serializers.CharField(source="student_name")
    cohortId = serializers.UUIDField(source="cohort_id")
    cohortName = serializers.CharField(source="cohort_name")
    rating = serializers.FloatField()
    performanceScore = serializers.FloatField(source="performance_score")
    problemSolvedCount = serializers.IntegerField(
        source="problem_solved_count"
    )
    consistencyScore = serializers.FloatField(
        source="consistency_score"
    )


class StudentAtRiskSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    studentName = serializers.CharField(source="student_name")
    riskReasons = serializers.ListField(
        source="risk_reasons",
        child=serializers.CharField(),
    )
    attendancePercentage = serializers.FloatField(
        source="attendance_percentage"
    )
    performanceScore = serializers.FloatField(
        source="performance_score"
    )
    activeWarningCount = serializers.IntegerField(
        source="active_warning_count"
    )


class TopPerformerSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    studentName = serializers.CharField(source="student_name")
    rank = serializers.IntegerField()
    performanceScore = serializers.FloatField(
        source="performance_score"
    )
    problemSolvedCount = serializers.IntegerField(
        source="problem_solved_count"
    )


class WarningStatsSerializer(serializers.Serializer):
    totalIssued = serializers.IntegerField(source="total_issued")
    totalResolved = serializers.IntegerField(source="total_resolved")
    activeWarnings = serializers.IntegerField(
        source="active_warnings"
    )
    studentsOnProbation = serializers.IntegerField(
        source="students_on_probation"
    )


class ProgressionStatsSerializer(serializers.Serializer):
    promotedToYear2 = serializers.IntegerField(
        source="promoted_to_year2"
    )
    graduated = serializers.IntegerField()
    dropped = serializers.IntegerField()
    active = serializers.IntegerField()


class CohortAnalyticsSerializer(serializers.Serializer):
    cohortId = serializers.UUIDField(source="cohort_id")
    cohortName = serializers.CharField(source="cohort_name")
    totalStudents = serializers.IntegerField(source="total_students")
    averagePerformanceScore = serializers.FloatField(
        source="average_performance_score"
    )
    averageAttendancePercentage = serializers.FloatField(
        source="average_attendance_percentage"
    )
    averageConsistencyScore = serializers.FloatField(
        source="average_consistency_score"
    )
    warningStats = WarningStatsSerializer(source="warning_stats")
    progressionStats = ProgressionStatsSerializer(
        source="progression_stats"
    )
    lastUpdated = serializers.CharField(source="last_updated")


class PlatformAnalyticsSerializer(serializers.Serializer):
    totalStudents = serializers.IntegerField(source="total_students")
    totalTeachers = serializers.IntegerField(source="total_teachers")
    totalActiveCohorts = serializers.IntegerField(
        source="total_active_cohorts"
    )
    totalArchivedCohorts = serializers.IntegerField(
        source="total_archived_cohorts"
    )
    overallAveragePerformanceScore = serializers.FloatField(
        source="overall_average_performance_score"
    )
    overallAverageAttendancePercentage = serializers.FloatField(
        source="overall_average_attendance_percentage"
    )
    totalWarningsIssued = serializers.IntegerField(
        source="total_warnings_issued"
    )
    studentsOnProbation = serializers.IntegerField(
        source="students_on_probation"
    )
    studentsDropped = serializers.IntegerField(
        source="students_dropped"
    )
    totalGraduates = serializers.IntegerField(
        source="total_graduates"
    )
    lastUpdated = serializers.CharField(source="last_updated")