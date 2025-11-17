# Funciones para manejar la lógica jerárquica de aprobaciones/rechazos

from django.utils import timezone
from documentos.models import ValidationStep, Document

def approve_step_and_cascade(step: ValidationStep, reason: str = ""):
    """
    Marca el paso dado como A y auto-aprueba pasos previos pendientes
    segun regla: order mayor = mayor jerarquía. Retorna True si documento pasa a A.
    """
    doc = step.document
    # auto-aprobar pasos con order < step.order que estén en 'P'
    ValidationStep.objects.filter(document=doc, order__lt=step.order, status="P").update(
        status="A", acted_at=timezone.now(), reason="Auto-approved by higher approver"
    )
    # marcar el step actual
    step.status = "A"
    step.reason = reason
    step.acted_at = timezone.now()
    step.save()

    # comprobar si queda algún pendiente
    pending = ValidationStep.objects.filter(document=doc, status="P").exists()
    max_step = ValidationStep.objects.filter(document=doc).order_by("-order").first()
    if (not pending) or (max_step and step.order == max_step.order):
        # aprobar documento
        doc.validation_status = "A"
        doc.save()
        return True
    return False

def reject_step_and_terminate(step: ValidationStep, reason: str = ""):
    """
    Marca step como R y pone el documento en R (terminal).
    """
    doc = step.document
    step.status = "R"
    step.reason = reason
    step.acted_at = timezone.now()
    step.save()
    doc.validation_status = "R"
    doc.save()
    return True
