from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
import uuid


class Command(BaseCommand):
    help = 'Create initial users for BigO Academy'

    def handle(self, *args, **options):
        # Import inside handle to avoid circular imports at startup
        from django.apps import apps
        DjangoUser = apps.get_model('core', 'DjangoUser')

        users = [
            {
                "email": "tshimelis23@gmail.com",
                "full_name": "Admin User",
                "role": "ADMIN",
                "status": "ACTIVE",
                "hashed_password": make_password("-00C#n*&,49jJ"),
                "must_change_password": False,
                "oauth_providers": [],
            },
            {
                "email": "abelmesfin123@gmail.com",
                "full_name": "Abel Mesfin",
                "role": "TEACHER",
                "status": "ACTIVE",
                "hashed_password": make_password("G9dcboZ6Jg&7"),
                "must_change_password": True,
                "oauth_providers": [],
            },
            {
                "email": "abebe1989@gmail.com",
                "full_name": "Abebe Bekele",
                "role": "STUDENT",
                "status": "ACTIVE",
                "hashed_password": make_password("X9b9f#tb3ec2"),
                "must_change_password": True,
                "oauth_providers": [],
            },
            {
                "email": "saribeyene183@gmail.com",
                "full_name": "Sara Beyene",
                "role": "STUDENT",
                "status": "ACTIVE",
                "hashed_password": make_password("mRtUsMVwjxkf"),
                "must_change_password": True,
                "oauth_providers": [],
            },
        ]

        for u in users:
            if DjangoUser.objects.filter(email=u["email"]).exists():
                self.stdout.write(f"User {u['email']} already exists — skipping")
                continue

            DjangoUser.objects.create(id=uuid.uuid4(), **u)
            self.stdout.write(
                f"Created: {u['full_name']} ({u['email']}) — {u['role']}"
            )

        self.stdout.write("Done.")