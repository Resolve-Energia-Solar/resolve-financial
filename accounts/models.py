from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
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


class User(AbstractUser):
    # Personal Info
    complete_name = models.CharField("Nome Completo", max_length=255, blank=True, null=True)
    birth_date = models.DateField("Data de Nascimento", blank=True, null=True)
    gender = models.CharField("Gênero", max_length=1, choices=(("M", "Masculino"), ("F", "Feminino"), ("O", "Outro")), default="M")
    first_document = models.CharField("CPF/CNPJ", max_length=20, unique=True, blank=True, null=True)
    profile_picture = models.ImageField("Foto de Perfil", upload_to="profiles", default="profiles/default.png")

    # Contact
    phone = models.ForeignKey("accounts.PhoneNumber", verbose_name="Telefone", on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField("E-mail", unique=True)

    # Address
    addresses = models.ManyToManyField("accounts.Address", verbose_name="Endereços", related_name="customer_addresses")

    # Employee Info
    contract_type = models.CharField("Tipo de Contrato", max_length=1, choices=(("C", "CLT"), ("P", "PJ")), default="C")
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE, blank=True, null=True)
    department = models.ForeignKey("accounts.Department", verbose_name="Departamento", on_delete=models.CASCADE, blank=True, null=True)
    role = models.ForeignKey("accounts.Role", verbose_name="Cargo", on_delete=models.CASCADE, blank=True, null=True)
    user_manager = models.ForeignKey("accounts.User", verbose_name="Gerente", on_delete=models.CASCADE, related_name="this_user_manager", blank=True, null=True)
    hire_date = models.DateField("Data de Admissão", blank=True, null=True)
    resignation_date = models.DateField("Data de Demissão", blank=True, null=True)

    # User Type Info
    user_types = models.ManyToManyField("accounts.UserType", verbose_name="Tipos de Usuário")

    PERSON_TYPE_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    person_type = models.CharField("Tipo de Pessoa", max_length=2, choices=PERSON_TYPE_CHOICES, blank=True, null=True)
    second_document = models.CharField("RG/Inscrição Estadual", max_length=12, blank=True, null=True)

    # Logs
    history = HistoricalRecords()

    def save(self, current_user=None, *args, **kwargs):
        if self.resignation_date is not None:
            self.is_active = False
        if not self.first_name and not self.last_name and self.complete_name:
            name_parts = self.complete_name.split(" ")
            self.first_name = name_parts[0]
            self.last_name = name_parts[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name()

    def get_absolute_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"slug": self.username})
    
    REQUIRED_FIELDS = ['complete_name', 'username']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"


class PhoneNumber(models.Model):
    phone_number = models.CharField("Número de Telefone", max_length=20, validators=[RegexValidator(r'^\d{1,11}$')], unique=True)
    is_main = models.BooleanField("Principal?", default=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Cliente")
    
    def __str__(self):
        return self.phone_number
    
    def save(self):
        if self.is_main:
            PhoneNumber.objects.filter(customer=self.customer).update(is_main=False)
        super(PhoneNumber, self).save()
    
    class Meta:
        verbose_name = "Número de Telefone"
        verbose_name_plural = "Números de Telefone"
    

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


class Branch(models.Model):
    name = models.CharField("Nome", max_length=255)
    address = models.ForeignKey("accounts.Address", verbose_name="Endereço", on_delete=models.CASCADE)
    owners = models.ManyToManyField("accounts.User", verbose_name="Proprietários", related_name='branch_owners', blank=True)
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField("Nome", max_length=255)
    email = models.EmailField("E-mail", unique=True)
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField("Nome", max_length=255)
    history = HistoricalRecords()
    is_deleted = models.BooleanField("Deletado?", default=False)


    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.name


class Squad(models.Model):
    name = models.CharField("Nome", max_length=255)
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE)
    manager = models.ForeignKey("accounts.User", verbose_name="Supervisor", on_delete=models.CASCADE, related_name='squad_manager')
    members = models.ManyToManyField("accounts.User", verbose_name="Membros", related_name='squad_members')
    boards = models.ManyToManyField("core.Board", verbose_name="Quadros", related_name='squad_boards', blank=True)
    is_deleted = models.BooleanField("Deletado?", default=False)

    # Logs
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Squad"
        verbose_name_plural = "Squads"
    
    def get_absolute_url(self):
        return reverse_lazy('accounts:squad_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name
