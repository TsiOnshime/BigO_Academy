import threading
from django.core.management.base import BaseCommand
from adapters.inbound.kafka.consumers import (ProblemSolvedConsumer, AttendanceUpdatedConsumer, ContestFinishedConsumer, WarningIssuedConsumer, WarningResolvedConsumer, StudentPromotedConsumer, StudentStatusChangedConsumer)

class Command(BaseCommand):
    help = "Start all Kafka consumers for the Analytics Service"
    
    def handle(self, *args, **options):
        self.stdout.write("Starting Analytics Kafka consumers...")
        
        consumers = [
            ProblemSolvedConsumer(),
            AttendanceUpdatedConsumer(),
            ContestFinishedConsumer(),
            WarningIssuedConsumer(),
            WarningResolvedConsumer(),
            StudentPromotedConsumer(),
            StudentStatusChangedConsumer()
            
        ]
        
        threads = []
        
        for consumer in consumers:
            t = threading.Thread(target=consumer.run, daemon=True)
            t.start()
            threads.append(t)
            self.stdout.write(
                f"  Started consumer: {consumer.__class__.__name__}"
            )
        self.stdout.write("All consumers running. Press Ctrl+C to stop.")
        
        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            self.stdout.write("Stopping consumers...")
            