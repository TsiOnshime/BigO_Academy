from abc import ABC, abstractmethod 
 
from domain.models import StudentPayment, TeacherPayment 
 
 
class EventPublisherPort(ABC): 
    """ 
    Abstract contract for publishing payment events to Kafka. 
    Consumed by Analytics Service (future) for payment metrics. 
    """ 
 
    @abstractmethod 
    def publish_student_payment_recorded( 
        self, payment: StudentPayment 
    ) -> None: 
        """ 
        Published when: admin records a student payment. 
        Analytics uses this for payment statistics. 
        """ 
        ... 
 
    @abstractmethod 
    def publish_student_payment_status_changed( 
        self, 
        payment: StudentPayment, 
        old_status: str, 
    ) -> None: 
        """ 
        Published when: admin verifies, rejects, or marks overdue. 
        Analytics uses this for overdue statistics. 
        """ 
        ... 
 
    @abstractmethod 
    def publish_teacher_payment_recorded( 
        self, payment: TeacherPayment 
    ) -> None: 
        """ 
        Published when: admin records a teacher payment. 
        Analytics uses this for teacher payment metrics. 
        """ 
        ... 
 
    @abstractmethod 
    def publish_teacher_payment_status_changed( 
        self, 
        payment: TeacherPayment, 
        old_status: str, 
    ) -> None: 
        """ 
        Published when: admin updates teacher payment status. 
        Analytics uses this for payment monitoring. 
        """ 