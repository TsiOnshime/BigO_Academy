"""
core/management/commands/run_kafka_consumer.py — Academic Service

Entry point for the Kafka consumer worker:

    python manage.py run_kafka_consumer

Run as a separate long-lived process alongside the Django app server
(e.g. its own container/systemd unit/Procfile entry) — it blocks
forever polling Kafka, it is not part of the request/response cycle.
A plain management command was chosen over adding Celery (mentioned in
the README's tech stack but not present anywhere in this codebase yet)
to avoid pulling in a new dependency for a single always-on consumer
loop; confluent_kafka.Consumer.poll() already blocks efficiently on its
own.
"""
from django.core.management.base import BaseCommand

from infrastructure.kafka.consumers import AcademicKafkaConsumer


class Command(BaseCommand):
    help = "Run the Academic Service Kafka consumer (Auth Service event intake)."

    def handle(self, *args, **options):
        consumer = AcademicKafkaConsumer()
        consumer.run()