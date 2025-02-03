from django.db import models
from company.models import Company 

class Document(models.Model):
    id = models.BigAutoField(primary_key=True)
    openid = models.IntegerField()
    token = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    externalid = models.CharField(max_length=255, null=True, blank=True)
    companyid = models.ForeignKey(Company, related_name='documents', on_delete=models.CASCADE, db_column='companyid')


    class Meta:
        db_table = 'document'

class Signer(models.Model):
    token = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    externalid = models.CharField(max_length=255, null=True, blank=True)
    documentid = models.ForeignKey(Document, related_name='signers', on_delete=models.CASCADE, db_column='documentid')

    class Meta:
        db_table = 'signers'