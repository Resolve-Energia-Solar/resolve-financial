from django.db import models
from simple_history.models import HistoricalRecords


class MaterialTypes(models.Model):

    name = models.CharField(max_length=50, verbose_name="Nome")
    description = models.CharField(max_length=255, verbose_name="Descrição")
    created_at = models.DateTimeField(verbose_name="Criado em")

    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Materiais"


class Materials(models.Model):

    bar_code = models.CharField(max_length=20, verbose_name="Código de Barras")
    image = models.CharField(max_length=100, verbose_name="Imagem")
    description = models.CharField(max_length=80, verbose_name="Descrição")
    technical_description = models.CharField(max_length=50, null=True, verbose_name="Descrição Técnica")
    type = models.ForeignKey(MaterialTypes, on_delete=models.CASCADE, verbose_name="Tipo")
    measure_unit = models.CharField(max_length=8, verbose_name="Unidade de Medida")
    is_serialized = models.BooleanField(default=False, verbose_name="Serializado")
    current_type = models.CharField(max_length=8, verbose_name="Tipo Atual")
    current_type_category = models.CharField(max_length=20, verbose_name="Categoria do Tipo Atual")
    created_at = models.DateTimeField(verbose_name="Criado em")
    
    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"


class SalesMaterials(models.Model):

    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material")
    amount = models.DecimalField(max_digits=20, decimal_places=6, default=0, verbose_name="Quantidade")
    material_class = models.CharField(max_length=256, verbose_name="Classe do Material")
    created_at = models.DateTimeField(verbose_name="Criado em")

    def __str__(self):
        return f"Sale: {self.id_sale}, Material: {self.id_material}"

    class Meta:
        verbose_name = "Sales Material"
        verbose_name_plural = "Sales Materials"
