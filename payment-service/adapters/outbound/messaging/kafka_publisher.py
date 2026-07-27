import json
from django.conf import settings
from domain.models import StudentPayment, TeacherPayment
from application.ports.outbound.event_publisher import EventPublisherPort

class KafkaEventPublisher(EventPublisherPort):
    
    def __init__(self):
        from confluent_kafka import Producer
        self._producer = Producer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        })
    
    def _publish(self, topic: str, payload: dict) -> None:
        self._producer.produce(
            topic, 
            value=json.dumps(payload, default=str).encode("utf-8")
            
    
        )
        self._producer.flush()
    
    def publish_student_payment_recorded(self, payment: StudentPayment)-> None:
        self._publish("payment.student.recorded", {
            "paymentId": str(payment.id),
            "studentId": str(payment.student_id),
            "paymentMonth": payment.payment_month,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
        })
    def publish_student_payment_status_changed(
        self, payment: StudentPayment, old_status: str
    ) -> None:
        self._publish("payment.student.status_changed", {
            "paymentId": str(payment.id),
            "studentId": str(payment.student_id),
            "paymentMonth": payment.payment_month,
            "oldStatus": old_status,
            "newStatus": payment.status.value,
        })
class ConsoleEventPublisher(EventPublisherPort):
    """
    Development-only publisher that prints events to console
    instead of sending to Kafka. Use when Kafka is not running locally.
    """

    def _publish(self, topic: str, payload: dict) -> None:
        print(f"\n[EVENT] Topic: {topic}")
        print(f"        Payload: {payload}\n")

    def publish_student_payment_recorded(self, payment):
        self._publish("payment.student.recorded", {
            "paymentId": str(payment.id),
            "studentId": str(payment.student_id),
        })

    def publish_student_payment_status_changed(self, payment, old_status):
        self._publish("payment.student.status_changed", {
            "paymentId": str(payment.id),
            "oldStatus": old_status,
            "newStatus": payment.status.value,
        })
    def publish_teacher_payment_recorded(self, payment):
        self._publish("payment.teacher.recorded", {
            "paymentId": str(payment.id),
            "teacherId": str(payment.teacher_id),
        })

    def publish_teacher_payment_status_changed(self, payment, old_status):
        self._publish("payment.teacher.status_changed", {
            "paymentId": str(payment.id),
            "oldStatus": old_status,
            "newStatus": payment.status.value,
        })