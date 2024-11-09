from django.db import models
from simple_history.models import HistoricalRecords


class MaterialAttributes(models.Model):
    key = models.CharField("Chave", max_length=50, null=True, blank=True)
    value = models.CharField("Valor", max_length=50, null=True, blank=True)
    material = models.ForeignKey("logistics.Materials", on_delete=models.CASCADE, verbose_name="Material", related_name="attributes")
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Atributo do Material"
        verbose_name_plural = "Atributos dos Materiais"
        ordering = ["-created_at"]

#ITEM
class Materials(models.Model):
    name = models.CharField("Nome", max_length=50, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    
    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"
        ordering = ["-created_at"]


class SolarKitMaterials(models.Model):
    solar_kit = models.ForeignKey("logistics.SolarEnergyKit", on_delete=models.CASCADE, verbose_name="Kit de Energia Solar", related_name="materials", null=True, blank=True)
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material", related_name="solar_kits", null=True, blank=True)
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Kit: {self.solar_kit}, Material: {self.material}"

    class Meta:
        verbose_name = "Material do Kit de Energia Solar"
        verbose_name_plural = "Materiais dos Kits de Energia Solar"
        ordering = ["-created_at"]
        

#PRODUTO
class SolarEnergyKit(models.Model):
    name = models.CharField("Nome", max_length=50, null=True, blank=True)
    description = models.CharField("Descrição", max_length=80, null=True, blank=True)
    product_value = models.DecimalField("Valor do Produto", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    reference_value = models.DecimalField("Valor de Referência", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    cost_value = models.DecimalField("Valor de Custo", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    branch = models.ForeignKey("accounts.Branch", on_delete=models.CASCADE, verbose_name="Filial", null=True, blank=True)
    roof_type = models.ForeignKey("inspections.RoofType", on_delete=models.CASCADE, verbose_name="Tipo de Telhado", null=True, blank=True)
    price = models.DecimalField("Preço", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    is_default = models.BooleanField("Padrão", default=False, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)

    # Logs
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kit de Materiais de Energia Solar"
        verbose_name_plural = "Kits de Materiais de Energia Solar"
        ordering = ["-created_at"]


class ProjectMaterials(models.Model):
    project = models.ForeignKey("resolve_crm.Project", on_delete=models.CASCADE, verbose_name="Projeto", related_name="materials_set", null=True, blank=True)
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material", related_name="projects_set", null=True, blank=True)
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    is_exit = models.BooleanField("Saída", default=False, null=True, blank=True)
    serial_number = models.CharField("Número de Série", max_length=50, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Project: {self.project}, Material: {self.material}"

    class Meta:
        verbose_name = "Material do Projeto"
        verbose_name_plural = "Materiais dos Projetos"
        ordering = ["-created_at"]


class SaleSolarKits(models.Model):
    sale = models.ForeignKey("resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", related_name="solar_kits", null=True, blank=True)
    commercial_proposal = models.ForeignKey("resolve_crm.ComercialProposal", on_delete=models.CASCADE, verbose_name="Proposta Comercial", related_name="solar_kits", null=True, blank=True)
    solar_kit = models.ForeignKey(SolarEnergyKit, on_delete=models.CASCADE, verbose_name="Kit de Energia Solar", related_name="sales", null=True, blank=True)
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    value = models.DecimalField("Valor do Produto", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    reference_value = models.DecimalField("Valor de Referência", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    cost_value = models.DecimalField("Valor de Custo", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Sale: {self.sale}, Solar Kit: {self.solar_kit}"

    class Meta:
        verbose_name = "Venda de Kit de Energia Solar"
        verbose_name_plural = "Vendas de Kits de Energia Solar"
        ordering = ["-created_at"]
