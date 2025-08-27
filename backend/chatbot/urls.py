from django.urls import path
from .views import (
    ChatView, DocumentUploadView, DocumentListView,
    InitializeKnowledgeBaseView, DeleteLogsView, health_check
)

urlpatterns = [
    path('ask/', ChatView.as_view(), name='chat'),
    path('upload-docs/', DocumentUploadView.as_view(), name='upload_document'),
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('initialize-kb/', InitializeKnowledgeBaseView.as_view(), name='initialize_kb'),
    path('delete-logs/', DeleteLogsView.as_view(), name='delete_logs'),
    path('health/', health_check, name='health_check'),
]