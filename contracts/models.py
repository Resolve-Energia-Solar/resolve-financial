from django.db import models


class DocumentType(models.Model):
    
    APP_LABEL_CHOICES = (
        ('accounts', 'Contas'),
        ('contracts', 'Contratos'),
        ('inspections', 'Inspeções'),
        ('logistics', 'Logística'),
        ('resolve_crm', 'CRM'),
        ('core', 'Core'),
        ('engineering', 'Engenharia'),
        ('financial', 'Financeiro'),
    )
    
    name = models.CharField("Nome", max_length=100)
    app_label = models.CharField("App Label", max_length=100, choices=APP_LABEL_CHOICES)
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
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Tipo de Documento", related_name="subtypes")
    
    class Meta:
        verbose_name = "Subtipo de Documento"
        verbose_name_plural = "Subtipos de Documentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name
