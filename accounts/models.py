from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse_lazy


class User(AbstractUser):
    # Personal Info
    complete_name = models.CharField("Nome Completo", max_length=255)
    birth_date = models.DateField("Data de Nascimento", blank=True, null=True)
    gender = models.CharField("Gênero", max_length=1, choices=(("M", "Masculino"), ("F", "Feminino")))
    cpf = models.CharField("CPF", max_length=11, unique=True)
    profile_picture = models.ImageField("Foto de Perfil", upload_to="profiles", default="profiles/default.png", blank=True, null=True)
    # Contact
    phone = models.CharField("Telefone", max_length=11, validators=[RegexValidator(r'^\d{1,11}$')], unique=True, blank=True, null=True)
    email = models.EmailField("E-mail", unique=True)
    # Address
    address = models.ForeignKey("accounts.Address", verbose_name="Endereço", max_length=255, on_delete=models.CASCADE, blank=True, null=True)
    # Employee Info
    contract_type = models.CharField("Tipo de Contrato", max_length=1, choices=(("C", "CLT"), ("P", "PJ")))
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE)
    department = models.ForeignKey("accounts.Department", verbose_name="Departamento", on_delete=models.CASCADE)
    role = models.ForeignKey("accounts.Role", verbose_name="Cargo", on_delete=models.CASCADE)
    user_manager = models.ForeignKey("accounts.User", verbose_name="Gerente", on_delete=models.CASCADE, related_name="this_user_manager", blank=True, null=True)
    hire_date = models.DateField("Data de Admissão", blank=True, null=True)
    resignation_date = models.DateField("Data de Demissão", blank=True, null=True)
    # Logs
    created_by = models.ForeignKey("accounts.User", verbose_name="Criado por", on_delete=models.CASCADE, related_name="user_created_by", blank=True, null=True, editable=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, blank=True, null=True, editable=False)
    updated_by = models.ForeignKey("accounts.User", verbose_name="Atualizado por", on_delete=models.CASCADE, related_name="user_updated_by", blank=True, null=True, editable=False)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, blank=True, null=True, editable=False)

    def save(self, current_user=None, *args, **kwargs):
        if not self.id and current_user is not None:
            self.created_by = self.updated_by = current_user
        elif current_user is not None:
            self.updated_by = current_user
        if self.resignation_date is not None:
            self.is_active = False
        if not self.first_name and not self.last_name:
            name_parts = self.complete_name.split(" ")
            self.first_name = name_parts[0]
            self.last_name = name_parts[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_absolute_url(self):
        return reverse_lazy("accounts:user_detail", kwargs={"slug": self.username})
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
    

class Address(models.Model):
    zip_code = models.CharField("CEP", max_length=8, validators=[RegexValidator(r'^\d{1,8}$')])
    country = models.CharField("País", max_length=255)
    state = models.CharField("Estado", max_length=2, choices=(("AC", "AC"), ("AL", "AL"), ("AP", "AP"), ("AM", "AM"), ("BA", "BA"), ("CE", "CE"), ("DF", "DF"), ("ES", "ES"), ("GO", "GO"), ("MA", "MA"), ("MT", "MT"), ("MS", "MS"), ("MG", "MG"), ("PA", "PA"), ("PB", "PB"), ("PR", "PR"), ("PE", "PE"), ("PI", "PI"), ("RJ", "RJ"), ("RN", "RN"), ("RS", "RS"), ("RO", "RO"), ("RR", "RR"), ("SC", "SC"), ("SP", "SP"), ("SE", "SE"), ("TO", "TO")))
    city = models.CharField("Cidade", max_length=255)
    neighborhood = models.CharField("Bairro", max_length=255)
    street = models.CharField("Rua", max_length=255)
    number = models.CharField("Número", max_length=10)
    complement = models.CharField("Complemento", max_length=255, blank=True, null=True)
    # Logs
    created_by = models.ForeignKey("accounts.User", verbose_name="Criado por", on_delete=models.CASCADE, related_name="address_created_by", blank=True, null=True, editable=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True, blank=True, null=True, editable=False)
    updated_by = models.ForeignKey("accounts.User", verbose_name="Atualizado por", on_delete=models.CASCADE, related_name="address_updated_by", blank=True, null=True, editable=False)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True, blank=True, null=True, editable=False)

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
    owner = models.ForeignKey("accounts.User", verbose_name="Proprietário", on_delete=models.CASCADE, related_name='branches_owner', blank=True, null=True)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.name


class Squad(models.Model):
    name = models.CharField("Nome", max_length=255)
    branch = models.ForeignKey("accounts.Branch", verbose_name="Unidade", on_delete=models.CASCADE)
    manager = models.ForeignKey("accounts.User", verbose_name="Gerente", on_delete=models.CASCADE, related_name='squad_manager')
    members = models.ManyToManyField("accounts.User", verbose_name="Membros", related_name='squad_members')

    class Meta:
        verbose_name = "Squad"
        verbose_name_plural = "Squads"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField("Nome", max_length=255)
    email = models.EmailField("E-mail", unique=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField("Nome", max_length=255)

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.name
