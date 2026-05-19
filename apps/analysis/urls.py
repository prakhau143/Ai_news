from django.urls import path
from . import views

urlpatterns = [
    path('ai-analysis/', views.ai_analysis, name='ai_analysis'),
    path('api/ai-metrics/', views.ai_metrics_api, name='ai_metrics_api'),
]
