from django.db import models


class DocumentType(models.Model):
    name = models.CharField("Nome", max_length=100)
    reusable = models.BooleanField("Reutilizável", default=False)
    required = models.BooleanField("Obrigatório", default=False)
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DocumentSubType(models.Model):
    name = models.CharField("Nome", max_length=100)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Tipo de Documento")
    
    class Meta:
        verbose_name = "Subtipo de Documento"
        verbose_name_plural = "Subtipos de Documentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name
