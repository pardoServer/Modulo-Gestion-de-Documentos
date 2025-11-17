import uuid
from django.db import models
from django.conf import settings

# get AUTH user model string from settings to avoid import loops
User = settings.AUTH_USER_MODEL

class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class BusinessEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=100)  # e.g., vehicle, employee
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.entity_type} - {self.id}"

class Document(models.Model):
    STATUS_CHOICES = [
        ("P", "Pending"),
        ("A", "Approved"),
        ("R", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # relaciones
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    entity = models.ForeignKey(BusinessEntity, on_delete=models.CASCADE)

    # metadatos (guardados en BD)
    name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.IntegerField(null=True, blank=True)
    bucket_key = models.CharField(max_length=500)  # ruta relativa en local_bucket

    sha256 = models.CharField(max_length=128, null=True, blank=True)  # hash opcional

    # validacion
    validation_enabled = models.BooleanField(default=False)
    validation_status = models.CharField(max_length=1, choices=STATUS_CHOICES, null=True, blank=True)

    # trazabilidad
    creator_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.id})"

class ValidationStep(models.Model):
    """
    Cada paso/approver del flujo.
    order: entero (mayor = mayor jerarquía)
    approver_user: FK al modelo de usuarios (UUID)
    status: 'P','A','R'
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="steps")
    order = models.IntegerField()
    approver_user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, null=True, blank=True)  # 'P','A','R'
    reason = models.TextField(null=True, blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
