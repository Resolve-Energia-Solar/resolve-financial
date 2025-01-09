from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from simple_history.models import HistoricalRecords
from django.urls import reverse_lazy


class UserType(models.Model):
    name = models.CharField("Nome do Tipo de Usuário", max_length=50, unique=True)
    description = models.TextField("Descrição", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Usuário"
        verbose_name_plural = "Tipos de Usuário"
        ordering = ['name']
        

class CustomField(models.Model):
    key = models.CharField("Chave", max_length=50, unique=True)
    value = models.CharField("Valor", max_length=50)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, verbose_name="Usuário", related_name="custom_fields")
    history = HistoricalRecords()
    
    def __str__(self):
        return self.key + " - " + self.value + " - " + self.user.complete_name
    
    class Meta:
        verbose_name = "Campo Personalizado"
        verbose_name_plural = "Campos Personalizados"
        ordering = ['key']
        

class Employee(models.Model):
    user = models.OneToOneField("accounts.User", verbose_name="Usuário", on_delete=models.CASCADE, related_name="employee")
    contract_type = models.CharField("Tipo de Contrato", max_length=1, choices=(("C", "CLT"), ("P", "PJ")),blank=True, null=True)
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey("accounts.Department", verbose_name="Departamento", on_delete=models.CASCADE, blank=True, null=True)
    role = models.ForeignKey("accounts.Role", verbose_name="Cargo", on_delete=models.CASCADE, blank=True, null=True)
    #trocar para relacionar com o próprio funcionario
    user_manager = models.ForeignKey("accounts.User", verbose_name="Gerente", on_delete=models.CASCADE, related_name="this_user_manager", blank=True, null=True)
    hire_date = models.DateField("Data de Admissão", blank=True, null=True)
    resignation_date = models.DateField("Data de Demissão", blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.user.first_name if self.user.first_name else self.user.email

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['user__complete_name', 'user__first_name', 'user__email']


class User(AbstractUser):
    PERSON_TYPE_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    # Personal Info
    complete_name = models.CharField("Nome Completo", max_length=255)
    birth_date = models.DateField("Data de Nascimento", blank=True, null=True)
    gender = models.CharField("Gênero", max_length=1, choices=(("M", "Masculino"), ("F", "Feminino"), ("O", "Outro")), default="M")
    first_document = models.CharField("CPF/CNPJ", max_length=20, blank=True, null=True)
    second_document = models.CharField("RG/Inscrição Estadual", max_length=12, blank=True, null=True)
    profile_picture = models.ImageField("Foto de Perfil", upload_to="profiles", default="profiles/default.png")

    # Contact
    email = models.EmailField("E-mail", unique=True)

    # Address
    addresses = models.ManyToManyField("accounts.Address", verbose_name="Endereços", related_name="customer_addresses")

    # User Type Info
    user_types = models.ManyToManyField("accounts.UserType", verbose_name="Tipos de Usuário")

    person_type = models.CharField("Tipo de Pessoa", max_length=2, choices=PERSON_TYPE_CHOICES, blank=True, null=True)

    # Logs
    history = HistoricalRecords()

    def save(self, current_user=None, *args, **kwargs):
        if not self.first_name and not self.last_name and self.complete_name:
            name_parts = self.complete_name.split(" ")
            self.first_name = name_parts[0]
            self.last_name = name_parts[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.first_name if self.first_name else self.email

    def get_absolute_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"slug": self.username})
    
    REQUIRED_FIELDS = ['complete_name', 'username']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['complete_name', 'first_name', 'email']


class PhoneNumber(models.Model):
    country_code = models.PositiveSmallIntegerField("Código do País", default=55)
    area_code = models.PositiveSmallIntegerField("DDD", validators=[RegexValidator(r'^\d{2}$'), MaxValueValidator(99)])
    phone_number = models.CharField("Número de Telefone", max_length=11, validators=[RegexValidator(r'^\d+$')])
    is_main = models.BooleanField("Principal?", default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário", related_name="phone_numbers", blank=True, null=True)
    def __str__(self):
        return f'+{self.country_code} {self.phone_number}'
    
    def save(self, *args, **kwargs):
        super(PhoneNumber, self).save(*args, **kwargs)
        if self.is_main:
            PhoneNumber.objects.filter(user=self.user).exclude(id=self.id).update(is_main=False)
    
    class Meta:
        verbose_name = "Número de Telefone"
        verbose_name_plural = "Números de Telefone"
        ordering = ['-is_main', 'user__complete_name']


class Address(models.Model):
    zip_code = models.CharField("CEP", max_length=8, validators=[RegexValidator(r'^\d{1,8}$')])
    country = models.CharField("País", max_length=255)
    state = models.CharField("Estado", max_length=2, choices=(("AC", "AC"), ("AL", "AL"), ("AP", "AP"), ("AM", "AM"), ("BA", "BA"), ("CE", "CE"), ("DF", "DF"), ("ES", "ES"), ("GO", "GO"), ("MA", "MA"), ("MT", "MT"), ("MS", "MS"), ("MG", "MG"), ("PA", "PA"), ("PB", "PB"), ("PR", "PR"), ("PE", "PE"), ("PI", "PI"), ("RJ", "RJ"), ("RN", "RN"), ("RS", "RS"), ("RO", "RO"), ("RR", "RR"), ("SC", "SC"), ("SP", "SP"), ("SE", "SE"), ("TO", "TO")))
    city = models.CharField("Cidade", max_length=255)
    neighborhood = models.CharField("Bairro", max_length=255)
    street = models.CharField("Rua", max_length=255)
    number = models.CharField("Número", max_length=10)
    complement = models.CharField("Complemento", max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField("Deletado?", default=False)
    # Logs
    history = HistoricalRecords()

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        super().save(*args, **kwargs)

    def __str__(self):
        if self.complement:
            return f"{self.street} - {self.number}, {self.complement}, {self.city}/{self.state} - {self.zip_code}, {self.country}"
        else:
            return f"{self.street} - {self.number}, {self.city}/{self.state} - {self.zip_code}, {self.country}"
    
    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"
        ordering = ['city', 'state', 'street', 'number']


class Branch(models.Model):
    name = models.CharField("Nome", max_length=255)
    address = models.ForeignKey("accounts.Address", verbose_name="Endereço", on_delete=models.CASCADE, blank=True, null=True)
    owners = models.ManyToManyField("accounts.User", verbose_name="Proprietários", related_name='branch_owners', blank=True)
    picture = models.ImageField("Foto", upload_to="branches", blank=True, null=True)
    transfer_percentage = models.DecimalField(
        "Porcentagem de Repasse",
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    discount_allowed = models.DecimalField("Desconto Permitido", max_digits=5, decimal_places=4, blank=True, null=True, )
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField("Nome", max_length=255)
    email = models.EmailField("E-mail", blank=True, null=True)
    owner = models.ForeignKey("accounts.User", verbose_name="Gerente", on_delete=models.CASCADE, related_name='department_owner')
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['name']

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField("Nome", max_length=255)
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)


    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['name']

    def __str__(self):
        return self.name


class Squad(models.Model):
    name = models.CharField("Nome", max_length=255)
    boards = models.ManyToManyField("core.Board", verbose_name="Quadro",related_name='squads', blank=True)
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE)
    manager = models.ForeignKey("accounts.User", verbose_name="Supervisor", on_delete=models.CASCADE, related_name='squad_manager')
    members = models.ManyToManyField("accounts.User", verbose_name="Membros", related_name='squad_members')
    is_deleted = models.BooleanField("Deletado?", default=False)

    # Logs
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Squad"
        verbose_name_plural = "Squads"
        ordering = ['name']
    
    def get_absolute_url(self):
        return reverse_lazy('accounts:squad_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name
