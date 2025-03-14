from django.db import models
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation


class SicoobRequest(models.Model):
    
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='Cliente', related_name='sicoob_requests')
    occupation = models.CharField('Profissão', max_length=100)
    monthly_income = models.DecimalField('Renda mensal', max_digits=10, decimal_places=2)
    managing_partner = models.ForeignKey('accounts.User', verbose_name='Sócio Administrador', on_delete=models.CASCADE, related_name='sicoob_requests_as_managing_partner', null=True, blank=True)
    status = models.CharField(max_length=2, default='P', choices=[('P', 'Pendente'), ('A', 'Aprovado'), ('R', 'Reprovado'), ('PA', 'Pré-Aprovado')])
    requested_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='Solicitado por', related_name='sicoob_requests_requested_by')
    attachments = GenericRelation("core.Attachment", related_query_name='sicoob_request_attachments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()

    def clean(self):
        if self.customer.person_type == 'PJ' and not self.managing_partner:
            raise ValidationError('Sócio administrador é obrigatório para solicitações cujo cliente é pessoa jurídica.')
        return super().clean()

    def __str__(self):
        return f'{self.customer.complete_name} - {self.get_status_display()}'
    
    class Meta:
        verbose_name = 'Solicitação Sicoob'
        verbose_name_plural = 'Solicitações Sicoob'
        ordering = ['customer__complete_name']


