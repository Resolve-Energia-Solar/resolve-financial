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
    
    def __str__(self):
        return self.name


class RequestsEnergyCompany(models.Model):
    company = models.ForeignKey(EnergyCompany, on_delete=models.CASCADE, verbose_name="Distribuidora de Energia")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Projeto", null=True, blank=True)
    request_date = models.DateField("Data da Solicitação")
    #ANALISA OS STATUS
    status = models.CharField("Status", max_length=2, choices=[("EA", "Em andamento"), ("D", "Deferido"), ("I", "Indeferido")])
    reason = models.TextField("Motivo", null=True, blank=True)
    conclusion_date = models.DateField("Data da Conclusão", null=True, blank=True)
    #DATA EM QUE MUDOU DE DEFERIDO OU INDEFERIDO | deve ser date ou datetime? | deve aparecer pro usuário?
    conclusion_registred = models.DateField("Data do Registro da Conclusão", null=True, blank=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Solicitação de Distribuidora de Energia"
        verbose_name_plural = "Solicitações de Distribuidoras de Energia"
    
    def __str__(self):
        return self.company.name
      
      
class CircuitBreaker(models.Model):
    material = models.ForeignKey("logistics.Materials", on_delete=models.CASCADE, verbose_name="Material")
    pole = models.IntegerField("Pólos")
    current = models.DecimalField("Corrente", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    is_deleted = models.BooleanField("Deletado", default=False)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Disjuntor"
        verbose_name_plural = "Disjuntores"
    
    def __str__(self):
        return self.material.description
