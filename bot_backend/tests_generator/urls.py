"""URL маршруты для модуля генерации тестов"""
from django.urls import path
from .views import (
    GenerateTestView,
    TestDetailView,
    TestHistoryView
)

app_name = 'tests_generator'

urlpatterns = [
    path('generate/', GenerateTestView.as_view(), name='generate'),
    path('history/', TestHistoryView.as_view(), name='history'),
    path('<uuid:test_id>/', TestDetailView.as_view(), name='detail'),
]
