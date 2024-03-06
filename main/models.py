from django.db import models


class Lead(models.Model):

    # Personal Information
    name = models.CharField(max_length=200, verbose_name="Nome")
    type = models.CharField(max_length=200, verbose_name="Tipo", help_text="Pessoa Física ou Jurídica?", choices=[("PF", "Pessoa Física"), ("PJ", "Pessoa Jurídica")])
    picture = models.ImageField(verbose_name="Foto", upload_to="leads", blank=True, null=True)
    
    # Lead
    contact_email = models.EmailField(verbose_name="E-mail")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    address = models.TextField(verbose_name="Endereço", blank=True, null=True)
    
    # CRM Information
    
    origin = models.CharField(max_length=200, verbose_name="Origem")
    responsible = models.CharField(max_length=200, verbose_name="Responsável")
    preseller = models.CharField(max_length=200, verbose_name="Pré-vendedor", blank=True, null=True)
    branch = models.CharField(max_length=200, verbose_name="Filial")

    # Meta Information

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"


class Opportunity(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    stage = models.CharField(max_length=200, verbose_name="Estágio")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    expected_close_date = models.DateField(verbose_name="Data de Fechamento Esperada")

    class Meta:
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"


class Activity(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    activity_type = models.CharField(max_length=200, verbose_name="Tipo de Atividade")
    date = models.DateField(verbose_name="Data")
    notes = models.TextField(verbose_name="Notas")

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"


class Email(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    subject = models.CharField(max_length=200, verbose_name="Assunto")
    body = models.TextField(verbose_name="Corpo")
    sent_at = models.DateTimeField(verbose_name="Enviado em")

    class Meta:
        verbose_name = "E-mail"
        verbose_name_plural = "E-mails"


class MarketingCampaign(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Término")
    effectiveness = models.TextField(verbose_name="Eficácia")

    class Meta:
        verbose_name = "Campanha de Marketing"
        verbose_name_plural = "Campanhas de Marketing"


class CustomerLifeCycle(models.Model):
    Lead = models.ForeignKey(Lead, on_delete=models.CASCADE, verbose_name="Contato")
    stage = models.CharField(max_length=200, verbose_name="Estágio")
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Término")

    class Meta:
        verbose_name = "Ciclo de Vida do Cliente"
        verbose_name_plural = "Ciclos de Vida dos Clientes"
