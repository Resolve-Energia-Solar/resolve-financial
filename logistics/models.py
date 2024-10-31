from django.db import models
from simple_history.models import HistoricalRecords


class MaterialTypes(models.Model):

    name = models.CharField(max_length=50, verbose_name="Nome", blank=True, null=True)
    description = models.CharField(max_length=255, verbose_name="Descrição")
    is_deleted = models.BooleanField(verbose_name="Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Materiais"
        ordering = ["-created_at"]


class Materials(models.Model):

    bar_code = models.CharField("Código de Barras", max_length=20, null=True, blank=True)
    image = models.ImageField("Imagem", max_length=100, null=True, blank=True)
    description = models.CharField("Descrição", max_length=80)
    technical_description = models.CharField("Descrição Técnica", max_length=50, null=True, blank=True)
    type = models.ForeignKey(MaterialTypes, on_delete=models.CASCADE, verbose_name="Tipo")
    measure_unit = models.CharField("Unidade de Medida", max_length=8)
    is_serialized = models.BooleanField(verbose_name="Serializado", default=False)
    current_type = models.CharField("Tipo Atual", max_length=8, null=True, blank=True)
    current_type_category = models.CharField("Categoria do Tipo Atual", max_length=20, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    
    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"
        ordering = ["-created_at"]


class SolarEnergyKit(models.Model):

    inversors_model = models.ForeignKey("logistics.Materials", on_delete=models.CASCADE, verbose_name="Modelo dos Inversores", related_name="inversors_kit_set")
    inversor_amount = models.PositiveSmallIntegerField("Quantidade de Inversores", default=0)
    modules_model = models.ForeignKey("logistics.Materials", on_delete=models.CASCADE, verbose_name="Modelo dos Módulos", related_name="modules_kit_set")
    modules_amount = models.PositiveSmallIntegerField("Quantidade de Módulos", default=0)
    kwp = models.DecimalField("kWp", max_digits=10, decimal_places=2, null=True, blank=True)
    branch = models.ForeignKey("accounts.Branch", on_delete=models.CASCADE, verbose_name="Filial")
    roof_type = models.ForeignKey("inspections.RoofType", on_delete=models.CASCADE, verbose_name="Tipo de Telhado")
    price = models.DecimalField("Preço", max_digits=20, decimal_places=6, default=0)
    is_default = models.BooleanField("Padrão", default=False)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.inversor_amount}x {self.inversors_model}, {self.modules_amount}x {self.modules_model} - {self.branch.name}, {self.roof_type.name}'

    class Meta:
        verbose_name = "Kit de Materiais de Energia Solar"
        verbose_name_plural = "Kits de Materiais de Energia Solar"
        ordering = ["-created_at"]


class SalesMaterials(models.Model):

    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material")
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0)
    material_class = models.CharField("Classe do Material", max_length=256)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    def __str__(self):
        return f"Sale: {self.id_sale}, Material: {self.id_material}"

    class Meta:
        verbose_name = "Material da Venda"
        verbose_name_plural = "Materiais das Vendas"
        ordering = ["-created_at"]


class ProjectMaterials(models.Model):

    project = models.ForeignKey("resolve_crm.Project", on_delete=models.CASCADE, verbose_name="Projeto", related_name="materials_set")
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material", related_name="projects_set")
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    def __str__(self):
        return f"Project: {self.project}, Material: {self.material}"

    class Meta:
        verbose_name = "Material do Projeto"
        verbose_name_plural = "Materiais dos Projetos"
        ordering = ["-created_at"]
