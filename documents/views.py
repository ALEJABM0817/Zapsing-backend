from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
import requests
import logging

from .models import Document
from .serializers import DocumentSerializer, SignerSerializer

logger = logging.getLogger(__name__)

class DocumentViewSet(ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        signers = instance.signers.all()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['signers'] = SignerSerializer(signers, many=True).data
        return Response(data)

    def create(self, request, *args, **kwargs):
        try:
            signers = request.data.get('signers', [])
            if not signers:
                return Response({"error": "Debe haber al menos un firmante"}, status=status.HTTP_400_BAD_REQUEST)

            for signer in signers:
                if not all(k in signer for k in ["name", "email"]):
                    return Response({"error": "Todos los firmantes deben tener nombre y correo"}, status=status.HTTP_400_BAD_REQUEST)

            zap_sign_api = 'https://sandbox.api.zapsign.com.br/api/v1/docs/'
            headers = {
                'Authorization': request.headers.get('Authorization'),
                'Content-Type': 'application/json'
            }

            response = requests.post(zap_sign_api, json=request.data, headers=headers)

            logger.error(f"Respuesta de ZapSign: {response.status_code} - {response.text}")

            if response.status_code != 200:
                logger.error(f"Error en API de ZapSign: {response.text}")
                return Response({"error": "Error en la API de ZapSign"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            zap_data = response.json()

            logger.error(f"Contenido de zap_data: {request.data}")

            if not all(k in zap_data for k in ["open_id", "token", "status", "signers"]):
                logger.error(f"ZapSign no devolvió todos los campos esperados: {zap_data}")
                return Response({"error": "Respuesta de ZapSign incompleta"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data_to_save = {
                "openid": zap_data.get("open_id"),
                "token": zap_data.get("token"),
                "name": request.data.get("name", ""),
                "status": zap_data.get("status"),
                "companyid": request.data.get("companyid")
            }

            serializer = self.get_serializer(data=data_to_save)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()

            zap_signers = zap_data.get("signers", [])
            logger.error(f"Firmantes recibidos: {zap_signers}")

            if not zap_signers:
                logger.error("ZapSign no devolvió firmantes en la respuesta")
                return Response({"error": "No se recibieron firmantes desde ZapSign"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            for signer_data in zap_signers:
                if not all(k in signer_data for k in ["name", "email"]):
                    logger.error(f"Firmante incompleto: {signer_data}")
                    return Response({"error": "Todos los firmantes deben tener nombre y correo"}, status=status.HTTP_400_BAD_REQUEST)

                signer_to_save = {
                    "token": signer_data.get("token", ""),
                    "status": signer_data.get("status", ""),
                    "name": signer_data.get("name", ""),
                    "email": signer_data.get("email", ""),
                    "documentid": document.id
                }

                signer_serializer = SignerSerializer(data=signer_to_save)
                if signer_serializer.is_valid():
                    signer_serializer.save()
                else:
                    logger.error(f"Error guardando firmante: {signer_serializer.errors}")
                    return Response({"error": "Error guardando firmante"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(self.get_serializer(document).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error al crear documento: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        documents = self.get_queryset().prefetch_related('signers')
        serializer = self.get_serializer(documents, many=True)
        data = serializer.data
        for document in data:
            document['signers'] = SignerSerializer(Document.objects.get(id=document['id']).signers.all(), many=True).data
        return Response(data)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            document_data = request.data.copy()

            required_fields = ['openid', 'token', 'status', 'companyid']
            for field in required_fields:
                if field not in document_data:
                    document_data[field] = getattr(instance, field)

            signers_data = document_data.pop('signers', None)

            serializer = self.get_serializer(instance, data=document_data, partial=partial)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()

            if signers_data is not None:
                existing_signers = {signer.id: signer for signer in instance.signers.all()}
                updated_signer_ids = set()

                for signer_data in signers_data:
                    signer_id = signer_data.get('id')

                    if signer_id and signer_id in existing_signers:
                        signer_instance = existing_signers[signer_id]
                        signer_serializer = SignerSerializer(signer_instance, data=signer_data, partial=partial)
                    else:
                        signer_serializer = SignerSerializer(data=signer_data)

                    if signer_serializer.is_valid():
                        signer = signer_serializer.save(documentid=document)
                        updated_signer_ids.add(signer.id)
                    else:
                        return Response(signer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                for signer_id in existing_signers:
                    if signer_id not in updated_signer_ids:
                        existing_signers[signer_id].delete()

            return Response(self.get_serializer(document).data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error al actualizar documento: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

