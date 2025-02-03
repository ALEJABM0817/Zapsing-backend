from django.urls import path
from .views import save_api_token
from .views import CompanyCreateView
from .views import CompanyDetailView

urlpatterns = [
    path('save-api-token/', save_api_token, name='save_api_token'),
    path('create/', CompanyCreateView.as_view(), name='create_company'),
    path('detail/<int:pk>/', CompanyDetailView.as_view(), name='company_detail'),
]
