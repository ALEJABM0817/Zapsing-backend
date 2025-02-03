from rest_framework import serializers
from .models import Document, Signer

class SignerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signer
        fields = ['id', 'token', 'status', 'name', 'email', 'externalid', 'documentid']
        extra_kwargs = {
            'documentid': {'required': False},
            'token': {'required': False},
            'status': {'required': False}
        }

    def update(self, instance, validated_data):
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class DocumentSerializer(serializers.ModelSerializer):
    signers = SignerSerializer(many=True, required=False)

    class Meta:
        model = Document
        fields = ['id', 'openid', 'token', 'name', 'status', 'created_at', 'last_updated_at', 'externalid', 'companyid', 'signers']

    def create(self, validated_data):
        signers_data = validated_data.pop('signers', [])

        document = Document.objects.create(**validated_data)
        
        for signer_data in signers_data:
            Signer.objects.create(document=document, **signer_data)

        return document

    def update(self, instance, validated_data):
        signers_data = validated_data.pop('signers', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if signers_data is not None:
            
            existing_signers = {signer.id: signer for signer in instance.signers.all()}
            updated_signer_ids = set()

            for signer_data in signers_data:
                signer_id = signer_data.get('id')

                if signer_id and signer_id in existing_signers:
                    signer_instance = existing_signers[signer_id]
                    signer_serializer = SignerSerializer(signer_instance, data=signer_data, partial=True)
                else:
                    signer_serializer = SignerSerializer(data=signer_data)

                if signer_serializer.is_valid():
                    signer = signer_serializer.save(documentid=instance)
                    updated_signer_ids.add(signer.id)
                else:
                    raise serializers.ValidationError(signer_serializer.errors)

            
            for signer_id in existing_signers:
                if signer_id not in updated_signer_ids:
                    existing_signers[signer_id].delete()

        return instance