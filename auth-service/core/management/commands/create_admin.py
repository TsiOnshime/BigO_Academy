from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
import uuid


class Command(BaseCommand):
    help = 'Create initial users for BigO Academy'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        fields = [f.name for f in User._meta.get_fields()]
        self.stdout.write(f"User model fields: {fields}")
        return  # stop here for now
        users = [
            {
                "email": "tshimelis23@gmail.com",
                "username": "tshimelis23@gmail.com",
                "full_name": "Admin User",
                "role": "ADMIN",
                "status": "ACTIVE",
                "password": make_password("-00C#n*&,49jJ"),
                "must_change_password": False,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "abelmesfin123@gmail.com",
                "username": "abelmesfin123@gmail.com",
                "full_name": "Abel Mesfin",
                "role": "TEACHER",
                "status": "ACTIVE",
                "password": make_password("G9dcboZ6Jg&7"),
                "must_change_password": True,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "abebe1989@gmail.com",
                "username": "abebe1989@gmail.com",
                "full_name": "Abebe Bekele",
                "role": "STUDENT",
                "status": "ACTIVE",
                "password": make_password("X9b9f#tb3ec2"),
                "must_change_password": True,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "saribeyene183@gmail.com",
                "username": "saribeyene183@gmail.com",
                "full_name": "Sara Beyene",
                "role": "STUDENT",
                "status": "ACTIVE",
                "password": make_password("mRtUsMVwjxkf"),
                "must_change_password": True,
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for u in users:
            if User.objects.filter(email=u["email"]).exists():
                self.stdout.write(f"User {u['email']} already exists — skipping")
                continue

            User.objects.create(id=uuid.uuid4(), **u)
            self.stdout.write(f"Created: {u['full_name']} ({u['email']}) — {u['role']}")

        self.stdout.write("Done.")