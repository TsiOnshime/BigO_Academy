from django.conf import settings

from adapters.outbound.persistence.student_payment_repo import DjangoStudentPaymentRepository
from adapters.outbound.persistence.teacher_payment_repo import DjangoTeacherPaymentRepository


def get_student_payment_repo() -> DjangoStudentPaymentRepository:
    return DjangoStudentPaymentRepository()


def get_teacher_payment_repo() -> DjangoTeacherPaymentRepository:
    return DjangoTeacherPaymentRepository()


    
def get_event_publisher():
    from adapters.outbound.messaging.kafka_publisher import ConsoleEventPublisher
    return ConsoleEventPublisher()

# ── Use Case Factories ────────────────────────────────────────────────────

def get_record_student_payment_use_case():
    from application.use_cases.student_payment.record_student_payment import RecordStudentPaymentUseCase
    return RecordStudentPaymentUseCase(
        student_payment_repository=get_student_payment_repo(),
        event_publisher=get_event_publisher(),
    )


def get_submit_payment_reference_use_case():
    from application.use_cases.student_payment.submit_payment_reference import SubmitPaymentReferenceUseCase
    return SubmitPaymentReferenceUseCase(
        student_payment_repository=get_student_payment_repo(),
        event_publisher=get_event_publisher(),
    )


def get_student_payment_history_use_case():
    from application.use_cases.student_payment.get_student_payment_history import GetStudentPaymentHistoryUseCase
    return GetStudentPaymentHistoryUseCase(
        student_payment_repository=get_student_payment_repo(),
    )


def get_subscription_status_use_case():
    from application.use_cases.student_payment.get_subscription_status import GetSubscriptionStatusUseCase
    return GetSubscriptionStatusUseCase(
        student_payment_repository=get_student_payment_repo(),
    )


def get_update_student_payment_status_use_case():
    from application.use_cases.student_payment.update_student_payment_status import UpdateStudentPaymentStatusUseCase
    return UpdateStudentPaymentStatusUseCase(
        student_payment_repository=get_student_payment_repo(),
        event_publisher=get_event_publisher(),
    )


def get_list_overdue_students_use_case():
    from application.use_cases.student_payment.list_overdue_students import ListOverdueStudentsUseCase
    return ListOverdueStudentsUseCase(
        student_payment_repository=get_student_payment_repo(),
    )


def get_list_pending_verification_use_case():
    from application.use_cases.student_payment.list_pending_verification import ListPendingVerificationUseCase
    return ListPendingVerificationUseCase(
        student_payment_repository=get_student_payment_repo(),
    )


def get_record_teacher_payment_use_case():
    from application.use_cases.teacher_payment.record_teacher_payment import RecordTeacherPaymentUseCase
    return RecordTeacherPaymentUseCase(
        teacher_payment_repository=get_teacher_payment_repo(),
        event_publisher=get_event_publisher(),
    )


def get_teacher_payment_history_use_case():
    from application.use_cases.teacher_payment.get_teacher_payment_history import GetTeacherPaymentHistoryUseCase
    return GetTeacherPaymentHistoryUseCase(
        teacher_payment_repository=get_teacher_payment_repo(),
    )


def get_update_teacher_payment_status_use_case():
    from application.use_cases.teacher_payment.update_teacher_payment_status import UpdateTeacherPaymentStatusUseCase
    return UpdateTeacherPaymentStatusUseCase(
        teacher_payment_repository=get_teacher_payment_repo(),
        event_publisher=get_event_publisher(),
    )


def get_list_pending_teacher_payments_use_case():
    from application.use_cases.teacher_payment.list_pending_teacher_payments import ListPendingTeacherPaymentsUseCase
    return ListPendingTeacherPaymentsUseCase(
        teacher_payment_repository=get_teacher_payment_repo(),
    )


def get_payment_summary_use_case():
    from application.use_cases.reports.get_payment_summary import GetPaymentSummaryUseCase
    return GetPaymentSummaryUseCase(
        student_payment_repository=get_student_payment_repo(),
        teacher_payment_repository=get_teacher_payment_repo(),
    )


def get_student_payment_report_use_case():
    from application.use_cases.reports.get_student_payment_report import GetStudentPaymentReportUseCase
    return GetStudentPaymentReportUseCase(
        student_payment_repository=get_student_payment_repo(),
    )


def get_teacher_payment_report_use_case():
    from application.use_cases.reports.get_teacher_payment_report import GetTeacherPaymentReportUseCase
    return GetTeacherPaymentReportUseCase(
        teacher_payment_repository=get_teacher_payment_repo(),
    )