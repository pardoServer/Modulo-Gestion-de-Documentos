# Contiene: DocumentCreateView, LocalUploadView, LocalDownloadView,
# DocumentDownloadView, DocumentApproveView, DocumentRejectView

import os
import hashlib
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction
from django.http import FileResponse, HttpResponseNotAllowed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from .models import Company, BusinessEntity, Document, ValidationStep
from .serializers import DocumentCreateSerializer
from .utils.presign import generate_presigned_token, get_presign_meta
from .services.validation import approve_step_and_cascade, reject_step_and_terminate

User = get_user_model()

def disk_path_for_bucket_key(bucket_key: str) -> str:
    """
    Construye ruta absoluta en disco para un bucket_key relativo.
    e.g., 'companies/<cid>/vehicles/<vid>/soat.pdf' -> MEDIA_ROOT/local_bucket/companies/...
    """
    safe = bucket_key.strip("/")
    return os.path.join(settings.MEDIA_ROOT, "local_bucket", safe)

# Authorization stub: update with real rules (UserCompany, roles, etc.)
def user_can_access_company(user, company: Company) -> bool:
    if user is None or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    # TODO: implementar relaciones reales, ej: UserCompany model
    return False

class DocumentCreateView(APIView):
    """
    POST /api/documents/  -> crea metadatos, crea pasos si hay validation_flow,
    genera upload_url (presigned local) y devuelve document_id + upload_url.
    """
    def post(self, request):
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        company = get_object_or_404(Company, id=data["company_id"])
        entity_data = data["entity"]
        entity = get_object_or_404(BusinessEntity, id=entity_data["entity_id"])

        doc_info = data["document"]
        # atomic: document + steps + token generation
        with transaction.atomic():
            doc = Document.objects.create(
                company=company,
                entity=entity,
                name=doc_info["name"],
                mime_type=doc_info["mime_type"],
                size_bytes=doc_info.get("size_bytes"),
                bucket_key=doc_info["bucket_key"],
                validation_enabled=data.get("validation_flow", {}).get("enabled", False),
                validation_status="P" if data.get("validation_flow", {}).get("enabled", False) else None,
                creator_user=request.user if request.user.is_authenticated else None
            )

            # crear pasos (si vienen)
            for s in data.get("validation_flow", {}).get("steps", []):
                approver = get_object_or_404(User, id=s["approver_user_id"])
                ValidationStep.objects.create(
                    document=doc,
                    order=s["order"],
                    approver_user=approver,
                    status="P"
                )

            # crear carpeta local y token presign
            disk_path = disk_path_for_bucket_key(doc.bucket_key)
            os.makedirs(os.path.dirname(disk_path), exist_ok=True)
            token = generate_presigned_token(disk_path, mode="upload")

        upload_url = request.build_absolute_uri(f"/api/documents/local-upload/{token}/")
        return Response({"document_id": str(doc.id), "upload_url": upload_url}, status=status.HTTP_201_CREATED)


class LocalUploadView(APIView):
    """
    PUT /api/documents/local-upload/<token>/  => sube bytes al server local
    - valida token
    - escribe bytes en disk_path
    - calcula size y sha256 y actualiza Document si bucket_key coincide
    """
    def put(self, request, token):
        meta = get_presign_meta(token)
        if not meta:
            return Response({"detail": "invalid-or-expired-token"}, status=status.HTTP_400_BAD_REQUEST)
        if meta.get("mode") != "upload":
            return Response({"detail": "invalid-mode"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = meta.get("file_path")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # escribir binario
        body = request.body
        with open(file_path, "wb") as f:
            f.write(body)

        # calcular size y sha256
        size = os.path.getsize(file_path)
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        digest = sha.hexdigest()

        # intentar actualizar Document que coincida con bucket_key relativa
        prefix = os.path.join(settings.MEDIA_ROOT, "local_bucket") + os.sep
        rel = file_path
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
            try:
                doc = Document.objects.get(bucket_key=rel)
                doc.size_bytes = size
                doc.sha256 = digest
                doc.save()
            except Document.DoesNotExist:
                pass

        return Response({"detail": "uploaded", "size_bytes": size}, status=status.HTTP_200_OK)

    def post(self, request, token):
        return HttpResponseNotAllowed(["PUT"])


class LocalDownloadView(APIView):
    """
    GET /api/documents/local-download/<token>/  => entrega el archivo (FileResponse)
    """
    def get(self, request, token):
        meta = get_presign_meta(token)
        if not meta:
            return Response({"detail": "invalid-or-expired-token"}, status=status.HTTP_400_BAD_REQUEST)
        if meta.get("mode") != "download":
            return Response({"detail": "invalid-mode"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = meta.get("file_path")
        if not os.path.exists(file_path):
            return Response({"detail": "file-not-found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(file_path, "rb"))


class DocumentDownloadView(APIView):
    """
    Endpoint para obtener una URL simulada (mock) que representa una
    URL pre-firmada de descarga desde un bucket.
    """

    def get(self, request, document_id):
        # Obtiene el documento o 404 si no existe
        doc = get_object_or_404(Document, id=document_id)

        # URL de descarga simulada — NO usa AWS/GCP/Azure
        download_url = f"https://bucket.mock/{doc.bucket_key}?presigned-get-url"

        # Retorna exactamente lo solicitado
        return Response({"download_url": download_url}, status=200)


class DocumentApproveView(APIView):
    """
    POST /api/documents/<document_id>/approve/ with body {"actor_user_id": "<uuid>", "reason": "..." }
    - aplica reglas jerárquicas: auto-aprueba previos si actor es mayor jerarquía
    - si el actor es el de mayor orden (max) o ya no quedan pendientes => document.validation_status = 'A'
    """
    def post(self, request, document_id):
        actor_id = request.data.get("actor_user_id")
        reason = request.data.get("reason", "")

        doc = get_object_or_404(Document, id=document_id)
        actor = get_object_or_404(User, id=actor_id)

        # autorización (stub)
        if not user_can_access_company(actor, doc.company):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        step = get_object_or_404(ValidationStep, document=doc, approver_user=actor)

        if step.status != "P":
            return Response({"detail": "step-already-acted"}, status=status.HTTP_400_BAD_REQUEST)

        approve_step_and_cascade(step, reason)
        return Response({"detail": "approved"}, status=status.HTTP_200_OK)


class DocumentRejectView(APIView):
    """
    POST /api/documents/<document_id>/reject/ with {"actor_user_id":..., "reason":...}
    - rechazo terminal: pone paso en 'R' y doc.validation_status = 'R'
    """
    def post(self, request, document_id):
        actor_id = request.data.get("actor_user_id")
        reason = request.data.get("reason", "")

        doc = get_object_or_404(Document, id=document_id)
        actor = get_object_or_404(User, id=actor_id)

        if not user_can_access_company(actor, doc.company):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        step = get_object_or_404(ValidationStep, document=doc, approver_user=actor)
        if step.status == "R":
            return Response({"detail": "step-already-rejected"}, status=status.HTTP_400_BAD_REQUEST)

        reject_step_and_terminate(step, reason)
        return Response({"detail": "rejected"}, status=status.HTTP_200_OK)
