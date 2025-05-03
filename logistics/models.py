from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.functional import cached_property

class MaterialAttributes(models.Model):
    key = models.CharField("Chave", max_length=50, null=True, blank=True)
    value = models.CharField("Valor", max_length=50, null=True, blank=True)
    material = models.ForeignKey("logistics.Materials", on_delete=models.CASCADE, verbose_name="Material", related_name="attributes")
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    def __str__(self):
        return self.key + " - " + self.value

    class Meta:
        verbose_name = "Atributo do Material"
        verbose_name_plural = "Atributos dos Materiais"
        ordering = ["-created_at"]

#ITEM
class Materials(models.Model):
    name = models.CharField("Nome", max_length=100, null=False, blank=False)
    price = models.DecimalField("Preço", max_digits=20, decimal_places=3, default=0, null=False, blank=False)
    is_extra = models.BooleanField("Extra", default=False, null=True, blank=True)
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


class ProductMaterials(models.Model):
    product = models.ForeignKey("logistics.Product", on_delete=models.CASCADE, verbose_name="product de Energia Solar", null=True, blank=True, related_name="product_material")
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material", related_name="products", null=True, blank=True)
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    
    history = HistoricalRecords()


    def __str__(self):
        return f"product: {self.product}, Material: {self.material}"

    class Meta:
        verbose_name = "Material do Produto"
        verbose_name_plural = "Materiais dos Produtos"
        ordering = ["-created_at"]
        

#PRODUTO
class Product(models.Model):
    
    DEFAULT_CHOICES = [
        ("S", "Sim"),
        ("N", "Não")
    ]
    
    name = models.CharField("Nome", max_length=50, null=False, blank=False)
    description = models.CharField("Descrição", max_length=80, null=True, blank=True)
    product_value = models.DecimalField("Valor do Produto", max_digits=20, decimal_places=6, default=0, null=False, blank=False)
    reference_value = models.DecimalField("Valor de Referência", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    cost_value = models.DecimalField("Valor de Custo", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    branch = models.ManyToManyField("accounts.Branch", verbose_name="Filiais")
    materials = models.ManyToManyField(Materials, through="logistics.ProductMaterials", verbose_name="Materiais")
    roof_type = models.ForeignKey("field_services.RoofType", on_delete=models.CASCADE, verbose_name="Tipo de Telhado", null=True, blank=True)
    params = models.DecimalField("Parâmetros", max_digits=6, decimal_places=2, null=True, blank=True)
    default = models.CharField("Padrão", max_length=1, choices=DEFAULT_CHOICES, default="N", null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)

    # Logs
    history = HistoricalRecords()
    
    @cached_property
    def product_material(self):
        return self.__class__.objects.get(pk=self.pk).product_material.all()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["-created_at"]


class ProjectMaterials(models.Model):
    project = models.ForeignKey('resolve_crm.Project', on_delete=models.CASCADE, verbose_name="Projeto")
    material = models.ForeignKey(Materials, on_delete=models.CASCADE, verbose_name="Material")
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0)
    material_class = models.CharField("Classe do Material", max_length=2, choices=[("K", "Kit"), ("P", "Padrão")], null=True, blank=True)
    is_exit = models.BooleanField("Saída", default=False)
    serial_number = models.CharField("Número de Série", max_length=50, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)
    
    history = HistoricalRecords()


    def __str__(self):
        return f"Projeto: {self.project}, Material: {self.material}, Quantidade: {self.amount}"

    class Meta:
        verbose_name = "Material do Projeto"
        verbose_name_plural = "Materiais dos Projetos"
        ordering = ["-created_at"]


class SaleProduct(models.Model):
    sale = models.ForeignKey("resolve_crm.Sale", on_delete=models.CASCADE, verbose_name="Venda", null=True, blank=True, related_name="sale_products")
    commercial_proposal = models.ForeignKey("resolve_crm.ComercialProposal", on_delete=models.CASCADE,verbose_name="Proposta Comercial", null=True, blank=True, related_name="commercial_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto", related_name="sales", null=True, blank=True)
    amount = models.DecimalField("Quantidade", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    value = models.DecimalField("Valor do Produto", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    cost_value = models.DecimalField("Valor de Custo", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    reference_value = models.DecimalField("Valor de Referência", max_digits=20, decimal_places=6, default=1, null=True, blank=True)
    
    average_consumption = models.DecimalField("Consumo Médio", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    estimated_consumption = models.DecimalField("Consumo Estimado", max_digits=20, decimal_places=6, default=0, null=True, blank=True)
    
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Sale: {self.sale}, Product: {self.product}"

    class Meta:
        verbose_name = "Produto da Venda"
        verbose_name_plural = "Produtos das Vendas"
        ordering = ["-created_at"]



class Purchase(models.Model):
    project = models.ForeignKey('resolve_crm.Project', on_delete=models.CASCADE, verbose_name="Projeto")
    supplier = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name="Fornecedor")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produto")
    purchase_date = models.DateTimeField("Data do Pedido", auto_now_add=True)
    delivery_type = models.ForeignKey('logistics.DeliveryType', on_delete=models.CASCADE, verbose_name="Tipo de Entrega", null=True, blank=True)
    status = models.CharField("Status", max_length=50, null=True, blank=True)
    delivery_number = models.CharField("Número de Entrega", max_length=50, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    # Logs
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"Projeto: {self.project}, Produto: {self.product}, Fornecedor: {self.supplier}"

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-purchase_date"]
        

class DeliveryType(models.Model):
    name = models.CharField("Nome", max_length=50, null=False, blank=False)
    description = models.CharField("Descrição", max_length=80, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False, null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Entrega"
        verbose_name_plural = "Tipos de Entrega"
        ordering = ["-created_at"]