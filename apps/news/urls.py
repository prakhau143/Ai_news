from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('news-catalogue/', views.news_catalogue, name='news_catalogue'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('api/news/', views.fetch_ai_news_api, name='fetch_real_ai_news'),
    path('api/search/', views.search_news, name='search_news'),
    path('generate-article-content/', views.generate_article_content, name='generate_article_content'),
]
