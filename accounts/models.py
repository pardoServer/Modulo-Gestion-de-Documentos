# accounts/models.py
# Custom user con UUID primary key

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    User con id tipo UUID. Conservamos AbstractUser para mantener username/email/permisos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.username} ({self.id})"

