from django.db import models
from simple_history.models import HistoricalRecords


class Materials(models.Model):

    image = models.ImageField(upload_to='logistics/materials/', null=True, blank=True)
    description = models.CharField(max_length=80)
    technical_description = models.CharField(max_length=50, null=True)
    type = models.CharField(max_length=50)
    measure_unit = models.CharField(max_length=8)
    is_serialized = models.BooleanField(default=False)
    
    # Logs
    created_at = models.DateTimeField()
    history = HistoricalRecords()

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"