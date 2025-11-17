from django.urls import path
from .views import (
    DocumentCreateView,
    LocalUploadView,
    LocalDownloadView,
    DocumentDownloadView,
    DocumentApproveView,
    DocumentRejectView,
)

urlpatterns = [
    path("", DocumentCreateView.as_view(), name="document-create"),
    path("<uuid:document_id>/download/", DocumentDownloadView.as_view(), name="document-download"),
    path("<uuid:document_id>/approve/", DocumentApproveView.as_view(), name="document-approve"),
    path("<uuid:document_id>/reject/", DocumentRejectView.as_view(), name="document-reject"),
    path("local-upload/<str:token>/", LocalUploadView.as_view(), name="local-upload"),
    path("local-download/<str:token>/", LocalDownloadView.as_view(), name="local-download"),
]
