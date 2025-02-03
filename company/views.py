from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Company
from rest_framework import status
from .serializers import CompanySerializer
from rest_framework import generics
from rest_framework.views import APIView

@api_view(['POST'])
def save_api_token(request):
    try:
        company_id = request.data.get('company_id')
        api_token = request.data.get('api_token')

        company = Company.objects.get(id=company_id)
        company.api_token = api_token
        company.save()

        return Response({"message": "API token guardado exitosamente."}, status=status.HTTP_200_OK)
    except Company.DoesNotExist:
        return Response({"error": "Company no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompanyCreateView(generics.CreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class CompanyDetailView(generics.RetrieveAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer