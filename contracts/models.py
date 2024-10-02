from django.db import models


class DocumentType(models.Model):
    name = models.CharField("Nome", max_length=100)
    description = models.TextField("Descrição")
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
    
    def __str__(self):
        return self.name
