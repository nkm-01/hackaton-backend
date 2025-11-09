"""URL маршруты для модуля консультаций"""
from django.urls import path
from .views import (
    AskConsultationView,
    ConsultationHistoryView,
    ConsultationDetailView
)

app_name = 'consultation'

urlpatterns = [
    path('ask/', AskConsultationView.as_view(), name='ask'),
    path('history/', ConsultationHistoryView.as_view(), name='history'),
    path('<uuid:consultation_id>/', ConsultationDetailView.as_view(), name='detail'),
]
