from uuid import UUID
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from adapters.inbound.rest.auth import JWTAuthMixin
from adapters.inbound.rest.serializers import (
    RecordStudentPaymentSerializer,
    SubmitPaymentReferenceSerializer,
    UpdateStudentPaymentStatusSerializer,
    RecordTeacherPaymentSerializer,
    UpdateTeacherPaymentStatusSerializer,
    StudentPaymentResponseSerializer,
    TeacherPaymentResponseSerializer,
    SubscriptionStatusResponseSerializer,
)
from domain.exceptions import (
    DuplicatePaymentError,
    StudentPaymentNotFoundError,
    TeacherPaymentNotFoundError,
    InvalidPaymentStatusTransitionError,
)
from domain.enums import StudentPaymentStatus, TeacherPaymentStatus


def error_response(status_code: int, error: str, message: str) -> Response:
    return Response(
        {
            "status": status_code,
            "error": error,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        status=status_code,
    )


# ── Student Payment Views ─────────────────────────────────────────────────

class StudentPaymentListView(JWTAuthMixin, APIView):
    """
    GET  /payments/students/{studentId}  — payment history
    POST /payments/students/{studentId}  — admin records payment
    """

    def get(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_student_payment_history_use_case,
        )
        from application.use_cases.student_payment.get_student_payment_history import (
            GetStudentPaymentHistoryCommand,
        )

        use_case = get_student_payment_history_use_case()
        result = use_case.execute(
            GetStudentPaymentHistoryCommand(student_id=UUID(str(student_id)))
        )

        return Response({
            "studentId": str(result.student_id),
            "payments": StudentPaymentResponseSerializer(
                result.payments, many=True
            ).data,
        })

    def post(self, request, student_id):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        serializer = RecordStudentPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(400, "BAD_REQUEST", str(serializer.errors))

        from infrastructure.config.dependencies import (
            get_record_student_payment_use_case,
        )
        from application.use_cases.student_payment.record_student_payment import (
            RecordStudentPaymentCommand,
        )

        try:
            use_case = get_record_student_payment_use_case()
            result = use_case.execute(RecordStudentPaymentCommand(
                student_id=UUID(str(student_id)),
                payment_month=serializer.validated_data["paymentMonth"],
                amount=serializer.validated_data["amount"],
                currency=serializer.validated_data["currency"],
                due_date=serializer.validated_data["dueDate"],
                reference_number=serializer.validated_data.get(
                    "referenceNumber"
                ),
                note=serializer.validated_data.get("note"),
            ))
            return Response(
                StudentPaymentResponseSerializer(result.payment).data,
                status=201,
            )
        except DuplicatePaymentError as e:
            return error_response(409, "CONFLICT", str(e))


class StudentPaymentSubscriptionView(JWTAuthMixin, APIView):
    """
    GET /payments/students/{studentId}/subscription
    """

    def get(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_subscription_status_use_case,
        )
        from application.use_cases.student_payment.get_subscription_status import (
            GetSubscriptionStatusCommand,
        )

        current_month = datetime.now().strftime("%Y-%m")
        use_case = get_subscription_status_use_case()
        result = use_case.execute(GetSubscriptionStatusCommand(
            student_id=UUID(str(student_id)),
            current_month=current_month,
        ))

        return Response(
            SubscriptionStatusResponseSerializer(result).data
        )


class SubmitPaymentReferenceView(JWTAuthMixin, APIView):
    """
    POST /payments/students/{studentId}/submit-reference
    """

    def post(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)
        if isinstance(user, Response):
            return user

        serializer = SubmitPaymentReferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(400, "BAD_REQUEST", str(serializer.errors))

        from infrastructure.config.dependencies import (
            get_submit_payment_reference_use_case,
        )
        from application.use_cases.student_payment.submit_payment_reference import (
            SubmitPaymentReferenceCommand,
        )

        try:
            use_case = get_submit_payment_reference_use_case()
            result = use_case.execute(SubmitPaymentReferenceCommand(
                student_id=UUID(str(student_id)),
                payment_month=serializer.validated_data["paymentMonth"],
                reference_number=serializer.validated_data["referenceNumber"],
                due_date=serializer.validated_data["dueDate"],
                amount=serializer.validated_data["amount"],
                currency=serializer.validated_data["currency"],
                note=serializer.validated_data.get("note"),
            ))
            return Response(
                StudentPaymentResponseSerializer(result.payment).data,
                status=201,
            )
        except DuplicatePaymentError as e:
            return error_response(409, "CONFLICT", str(e))


class StudentPaymentStatusView(JWTAuthMixin, APIView):
    """
    PATCH /payments/students/{studentId}/payments/{paymentId}/status
    """

    def patch(self, request, student_id, payment_id):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        serializer = UpdateStudentPaymentStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(400, "BAD_REQUEST", str(serializer.errors))

        from infrastructure.config.dependencies import (
            get_update_student_payment_status_use_case,
        )
        from application.use_cases.student_payment.update_student_payment_status import (
            UpdateStudentPaymentStatusCommand,
        )

        try:
            use_case = get_update_student_payment_status_use_case()
            result = use_case.execute(UpdateStudentPaymentStatusCommand(
                student_id=UUID(str(student_id)),
                payment_id=UUID(str(payment_id)),
                new_status=StudentPaymentStatus(
                    serializer.validated_data["status"]
                ),
                verified_by=UUID(str(user["userId"])),
                note=serializer.validated_data.get("note"),
            ))
            return Response(
                StudentPaymentResponseSerializer(result).data
            )
        except StudentPaymentNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))
        except InvalidPaymentStatusTransitionError as e:
            return error_response(400, "BAD_REQUEST", str(e))


class ListOverdueStudentsView(JWTAuthMixin, APIView):
    """
    GET /payments/students/overdue
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_list_overdue_students_use_case,
        )
        from application.use_cases.student_payment.list_overdue_students import (
            ListOverdueStudentsCommand,
        )

        use_case = get_list_overdue_students_use_case()
        result = use_case.execute(ListOverdueStudentsCommand())

        return Response({
            "overdueCount": result.overdue_count,
            "students": StudentPaymentResponseSerializer(
                result.payments, many=True
            ).data,
        })


class ListPendingVerificationView(JWTAuthMixin, APIView):
    """
    GET /payments/students/pending-verification
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_list_pending_verification_use_case,
        )
        from application.use_cases.student_payment.list_pending_verification import (
            ListPendingVerificationCommand,
        )

        use_case = get_list_pending_verification_use_case()
        result = use_case.execute(ListPendingVerificationCommand())

        return Response({
            "payments": StudentPaymentResponseSerializer(
                result, many=True
            ).data,
        })


# ── Teacher Payment Views ─────────────────────────────────────────────────

class TeacherPaymentListView(JWTAuthMixin, APIView):
    """
    GET  /payments/teachers/{teacherId} — payment history
    POST /payments/teachers/{teacherId} — admin records payment
    """

    def get(self, request, teacher_id):
        user = self.require_admin_or_self(request, teacher_id)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_teacher_payment_history_use_case,
        )
        from application.use_cases.teacher_payment.get_teacher_payment_history import (
            GetTeacherPaymentHistoryCommand,
        )

        use_case = get_teacher_payment_history_use_case()
        result = use_case.execute(
            GetTeacherPaymentHistoryCommand(
                teacher_id=UUID(str(teacher_id))
            )
        )

        return Response({
            "teacherId": str(result.teacher_id),
            "payments": TeacherPaymentResponseSerializer(
                result.payments, many=True
            ).data,
        })

    def post(self, request, teacher_id):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        serializer = RecordTeacherPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(400, "BAD_REQUEST", str(serializer.errors))

        from infrastructure.config.dependencies import (
            get_record_teacher_payment_use_case,
        )
        from application.use_cases.teacher_payment.record_teacher_payment import (
            RecordTeacherPaymentCommand,
        )

        use_case = get_record_teacher_payment_use_case()
        result = use_case.execute(RecordTeacherPaymentCommand(
            teacher_id=UUID(str(teacher_id)),
            payment_month=serializer.validated_data["paymentMonth"],
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data["currency"],
            note=serializer.validated_data.get("note"),
        ))

        return Response(
            TeacherPaymentResponseSerializer(result.payment).data,
            status=201,
        )


class TeacherPaymentStatusView(JWTAuthMixin, APIView):
    """
    PATCH /payments/teachers/{teacherId}/payments/{paymentId}/status
    """

    def patch(self, request, teacher_id, payment_id):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        serializer = UpdateTeacherPaymentStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(400, "BAD_REQUEST", str(serializer.errors))

        from infrastructure.config.dependencies import (
            get_update_teacher_payment_status_use_case,
        )
        from application.use_cases.teacher_payment.update_teacher_payment_status import (
            UpdateTeacherPaymentStatusCommand,
        )

        try:
            use_case = get_update_teacher_payment_status_use_case()
            result = use_case.execute(UpdateTeacherPaymentStatusCommand(
                teacher_id=UUID(str(teacher_id)),
                payment_id=UUID(str(payment_id)),
                new_status=TeacherPaymentStatus(
                    serializer.validated_data["status"]
                ),
                processed_by=UUID(str(user["userId"])),
                note=serializer.validated_data.get("note"),
            ))
            return Response(
                TeacherPaymentResponseSerializer(result).data
            )
        except TeacherPaymentNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))
        except InvalidPaymentStatusTransitionError as e:
            return error_response(400, "BAD_REQUEST", str(e))


class ListPendingTeacherPaymentsView(JWTAuthMixin, APIView):
    """
    GET /payments/teachers/pending
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_list_pending_teacher_payments_use_case,
        )
        from application.use_cases.teacher_payment.list_pending_teacher_payments import (
            ListPendingTeacherPaymentsCommand,
        )

        use_case = get_list_pending_teacher_payments_use_case()
        result = use_case.execute(ListPendingTeacherPaymentsCommand())

        return Response({
            "payments": TeacherPaymentResponseSerializer(
                result, many=True
            ).data,
        })


# ── Report Views ──────────────────────────────────────────────────────────

class PaymentSummaryView(JWTAuthMixin, APIView):
    """
    GET /payments/reports/summary
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        month = request.query_params.get("month")

        from infrastructure.config.dependencies import (
            get_payment_summary_use_case,
        )
        from application.use_cases.reports.get_payment_summary import (
            GetPaymentSummaryCommand,
        )

        use_case = get_payment_summary_use_case()
        result = use_case.execute(GetPaymentSummaryCommand(month=month))

        return Response({
            "month": result.month,
            "studentPayments": {
                "totalPaid": result.student_payments.total_paid,
                "totalPending": result.student_payments.total_pending,
                "totalOverdue": result.student_payments.total_overdue,
                "totalAmountCollected": result.student_payments.total_amount_collected,
                "currency": result.student_payments.currency,
            },
            "teacherPayments": {
                "totalPaid": result.teacher_payments.total_paid,
                "totalPending": result.teacher_payments.total_pending,
                "totalAmountPaid": result.teacher_payments.total_amount_paid,
                "totalAmountPending": result.teacher_payments.total_amount_pending,
                "currency": result.teacher_payments.currency,
            },
        })


class StudentPaymentReportView(JWTAuthMixin, APIView):
    """
    GET /payments/reports/student-payments
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        status_param = request.query_params.get("status")
        status = StudentPaymentStatus(status_param) if status_param else None
        month = request.query_params.get("month")
        cohort_id = request.query_params.get("cohortId")

        from infrastructure.config.dependencies import (
            get_student_payment_report_use_case,
        )
        from application.use_cases.reports.get_student_payment_report import (
            GetStudentPaymentReportCommand,
        )

        use_case = get_student_payment_report_use_case()
        result = use_case.execute(GetStudentPaymentReportCommand(
            status=status,
            month=month,
            cohort_id=UUID(cohort_id) if cohort_id else None,
        ))

        return Response({
            "month": result.month,
            "cohortId": str(result.cohort_id) if result.cohort_id else None,
            "payments": StudentPaymentResponseSerializer(
                result.payments, many=True
            ).data,
        })


class TeacherPaymentReportView(JWTAuthMixin, APIView):
    """
    GET /payments/reports/teacher-payments
    """

    def get(self, request):
        user = self.require_admin(request)
        if isinstance(user, Response):
            return user

        status_param = request.query_params.get("status")
        status = TeacherPaymentStatus(status_param) if status_param else None
        month = request.query_params.get("month")

        from infrastructure.config.dependencies import (
            get_teacher_payment_report_use_case,
        )
        from application.use_cases.reports.get_teacher_payment_report import (
            GetTeacherPaymentReportCommand,
        )

        use_case = get_teacher_payment_report_use_case()
        result = use_case.execute(GetTeacherPaymentReportCommand(
            status=status,
            month=month,
        ))

        return Response({
            "month": result.month,
            "payments": TeacherPaymentResponseSerializer(
                result.payments, many=True
            ).data,
        })