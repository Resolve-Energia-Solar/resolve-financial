from django.db import models


class RoofType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nome", blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Telhado"
        verbose_name_plural = "Tipos de Telhados"