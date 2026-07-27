from django.urls import path
from adapters.inbound.rest.views import (
    StudentPaymentListView,
    StudentPaymentSubscriptionView,
    SubmitPaymentReferenceView,
    StudentPaymentStatusView,
    ListOverdueStudentsView,
    ListPendingVerificationView,
    TeacherPaymentListView,
    TeacherPaymentStatusView,
    ListPendingTeacherPaymentsView,
    PaymentSummaryView,
    StudentPaymentReportView,
    TeacherPaymentReportView,
)

urlpatterns = [
    # Student payments
    path(
        "payments/students/overdue/",
        ListOverdueStudentsView.as_view(),
    ),
    path(
        "payments/students/pending-verification/",
        ListPendingVerificationView.as_view(),
    ),
    path(
        "payments/students/<uuid:student_id>/",
        StudentPaymentListView.as_view(),
    ),
    path(
        "payments/students/<uuid:student_id>/subscription/",
        StudentPaymentSubscriptionView.as_view(),
    ),
    path(
        "payments/students/<uuid:student_id>/submit-reference/",
        SubmitPaymentReferenceView.as_view(),
    ),
    path(
        "payments/students/<uuid:student_id>/payments/<uuid:payment_id>/status/",
        StudentPaymentStatusView.as_view(),
    ),

    # Teacher payments
    path(
        "payments/teachers/pending/",
        ListPendingTeacherPaymentsView.as_view(),
    ),
    path(
        "payments/teachers/<uuid:teacher_id>/",
        TeacherPaymentListView.as_view(),
    ),
    path(
        "payments/teachers/<uuid:teacher_id>/payments/<uuid:payment_id>/status/",
        TeacherPaymentStatusView.as_view(),
    ),

    # Reports
    path(
        "payments/reports/summary/",
        PaymentSummaryView.as_view(),
    ),
    path(
        "payments/reports/student-payments/",
        StudentPaymentReportView.as_view(),
    ),
    path(
        "payments/reports/teacher-payments/",
        TeacherPaymentReportView.as_view(),
    ),
]