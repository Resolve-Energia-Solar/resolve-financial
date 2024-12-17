from django.db import models
from simple_history.models import HistoricalRecords
from resolve_crm.models import Project


class EnergyCompany(models.Model):
    name = models.CharField("Nome", max_length=200)
    cnpj = models.CharField("CNPJ", max_length=20, null=False, blank=False)
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, verbose_name="Endereço", null=True, blank=True)
    phone = models.CharField("Telefone", max_length=20, null=True, blank=True)
    email = models.EmailField("E-mail", null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Distribuidora de Energia"
        verbose_name_plural = "Distribuidoras de Energia"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class ResquestType(models.Model):
    name = models.CharField("Nome", max_length=200)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Tipo de Solicitação"
        verbose_name_plural = "Tipos de Solicitação"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class RequestsEnergyCompany(models.Model):
    company = models.ForeignKey(EnergyCompany, on_delete=models.CASCADE, verbose_name="Distribuidora de Energia")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projeto", related_name="requests_energy_company")
    unit = models.ForeignKey("Units", on_delete=models.CASCADE, verbose_name="Unidade", null=True, blank=True)
    type = models.ForeignKey("ResquestType", on_delete=models.CASCADE, verbose_name="Tipo de Solicitação")
    situation = models.ManyToManyField("SituationEnergyCompany", verbose_name="Situação", blank=True)
    requested_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="Solicitado por", null=True, blank=True)
    request = models.ForeignKey("RequestsEnergyCompany", on_delete=models.CASCADE, verbose_name="Solicitação", null=True, blank=True)
    request_date = models.DateField("Data da Solicitação")
    status = models.CharField("Status", max_length=2, choices=[("S", "Solicitado"), ("D", "Deferido"), ("I", "Indeferido")])
    conclusion_date = models.DateField("Data da Conclusão", null=True, blank=True)
    interim_protocol = models.CharField("Protocolo Provisório", max_length=100, null=True, blank=True)
    final_protocol = models.CharField("Protocolo Definitivo", max_length=100, null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Solicitação da Concessionária de Energia"
        verbose_name_plural = "Solicitações da Concessionárias de Energia"
        ordering = ["-request_date"]
    
    def __str__(self):
        return self.company.name
    

class SituationEnergyCompany(models.Model):
    name = models.CharField("Nome", max_length=200)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Situação da Concessionária de Energia"
        verbose_name_plural = "Situações da Concessionária de Energia"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Units(models.Model):
    TYPE_CHOICES = [
        ("M", "Monofásico"),
        ("B", "Bifásico"),
        ("T", "Trifásico"),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projeto", null=True, blank=True, related_name="units")
    name = models.CharField("Nome", max_length=200, null=True, blank=True)
    supply_adquance = models.ManyToManyField("SupplyAdequance", verbose_name="Adequação de Fornecimento", blank=True)
    main_unit = models.BooleanField("Geradora", default=False)
    unit_percentage = models.DecimalField("Porcentagem de Rateio", max_digits=10, decimal_places=2, null=True, blank=True)
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, verbose_name="Endereço", null=True, blank=True)
    type = models.CharField("Tipo de Fornecimento", max_length=100, null=True, blank=True, choices=TYPE_CHOICES)
    unit_number = models.CharField("Conta contrato", max_length=100, null=True, blank=True)
    #Trocar nome para meter_number
    account_number = models.CharField("Número do medidor", max_length=100, null=True, blank=True)
    bill_file = models.FileField("Arquivo da Fatura", upload_to="units-biils/", null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    def save(self, *args, **kwargs):
        if self.main_unit:
            # Desmarcar outras unidades geradoras no mesmo projeto
            Units.objects.filter(project=self.project, main_unit=True).exclude(id=self.id).update(main_unit=False)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ["name"]
    
    def __str__(self):
        return self.name or "Unidade sem nome"


class SupplyAdequance(models.Model):
    name = models.CharField("Nome", max_length=200)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Adequação de Fornecimento"
        verbose_name_plural = "Adequações de Fornecimento"
        ordering = ["name"]
        
    def __str__(self):
        return self.name
