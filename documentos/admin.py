from django.contrib import admin
from .models import Company, BusinessEntity, Document, ValidationStep

class ValidationStepInline(admin.TabularInline):
    model = ValidationStep
    extra = 0
    readonly_fields = ("status", "reason", "acted_at")

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "entity", "validation_enabled", "validation_status", "created_at")
    search_fields = ("name", "bucket_key")
    inlines = [ValidationStepInline]

admin.site.register(Company)
admin.site.register(BusinessEntity)
admin.site.register(ValidationStep)

