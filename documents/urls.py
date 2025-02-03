from django.urls import path, include
from .views import DocumentViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    path('create/document/', DocumentViewSet.as_view({'post': 'create'}), name='create-document'),
    path('documents/', DocumentViewSet.as_view({'get': 'list'}), name='list-documents'),
]
