from abc import ABC, abstractmethod 
 
 
class OverduePaymentJobPort(ABC): 
    """ 
    Abstract contract for the scheduled job that marks 
    student payments as OVERDUE when their due date passes. 
 
    Production implementation: Celery periodic task 
    Test implementation: call execute() directly 
    """ 
 
    @abstractmethod 
    def execute(self) -> int: 
        """ 
        Find all PENDING student payments past their due_date 
        and mark them as OVERDUE. 
        Returns the number of payments marked as overdue. 
        """ 
