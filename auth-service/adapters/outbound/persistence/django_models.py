"""
Django ORM model for the User table.

This is the ONLY file allowed to use Django's models.Model. It defines the
actual database table. It is NOT the same as the domain User dataclass
(domain/models.py) — this is Django's representation of that same data for
storage purposes.

The repository layer is responsible for converting between DjangoUser and
domain.models.User.
"""

import uuid

from django.db import models

from domain.enums import UserRole, AccountStatus


class DjangoUser(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
    )

    full_name = models.CharField(
        max_length=150,
    )

    role = models.CharField(
        max_length=10,
        choices=[(role.value, role.name) for role in UserRole],
    )

    status = models.CharField(
        max_length=10,
        choices=[(status.value, status.name) for status in AccountStatus],
    )

    hashed_password = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    oauth_providers = models.JSONField(
        default=list,
    )

    must_change_password = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "core_user"
        app_label = "core"
    def __str__(self) -> str:
        return f"{self.email} ({self.role})"