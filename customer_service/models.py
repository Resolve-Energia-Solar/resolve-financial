from django.db import models


class CustomerService(models.Model):

    customer = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, verbose_name="Cliente", blank=True, null=True
    )
    protocol = models.BigIntegerField("Protocolo")
    user = models.CharField("Usuário", max_length=50)
    service = models.PositiveIntegerField("Atendimento")
    date = models.DateField("Data")

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"

    def __str__(self):
        return f"{self.protocol} - {self.customer.complete_name}"



class LostReason(models.Model):
    name = models.CharField("Motivo", max_length=50)
    is_deleted = models.BooleanField("Deletado", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Motivo de Perda"
        verbose_name_plural = "Motivos de Perda"

    def __str__(self):
        return self.name