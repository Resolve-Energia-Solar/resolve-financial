from django.db import models


class PaymentRequest(models.Model):
    
    PAYMENT_METHOD_CHOICES = (
        ('PIX', 'PIX'),
        ('TED', 'TED'),
        ('DOC', 'DOC'),
        ('Boleto', 'Boleto'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('Dinheiro', 'Dinheiro'),
        ('Cheque', 'Cheque'),
        ('Transferência Bancária', 'Transferência Bancária'),
        ('Depósito Bancário', 'Depósito Bancário'),
        ('Outros', 'Outros'),
    )
    
    id = models.CharField(
        primary_key=True,
        max_length=8,
        verbose_name='ID',
        help_text='Identificador único da solicitação de pagamento'
    )
    protocol = models.CharField(
        max_length=14,
        verbose_name='Protocolo',
        help_text='Protocolo da solicitação'
    )
    requester = models.ForeignKey(
        "financial.AppsheetUser",
        on_delete=models.CASCADE,
        verbose_name='Usuário Solicitante',
        help_text='Usuário que realizou a solicitação',
        db_column='id_user',
        related_name='requested_payments'
    )
    manager = models.ForeignKey(
        "financial.AppsheetUser",
        on_delete=models.CASCADE,
        verbose_name='ID do Gerente',
        help_text='Identificador do gerente responsável',
        db_column='id_user_manager',
        related_name='managed_payments'
    )
    department = models.ForeignKey(
        'financial.UserDepartment',
        verbose_name='ID do Departamento do Usuário',
        help_text='Identificador do departamento do usuário',
        on_delete=models.CASCADE,
        db_column='id_user_deparment'
    )
    supplier = models.CharField(
        max_length=256,
        verbose_name='ID do Fornecedor da Solicitação de Pagamento',
        help_text='Identificador do fornecedor associado à solicitação de pagamento',
        db_column='id_payment_request_supplier'
    )
    sale = models.ForeignKey(
        "financial.SaleResume",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Venda',
        help_text='Venda associada (se aplicável)',
        db_column='id_sale'
    )
    description = models.TextField(
        verbose_name='Descrição',
        help_text='Descrição detalhada da solicitação de pagamento'
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        verbose_name='Valor',
        help_text='Valor total da solicitação de pagamento'
    )
    service_date = models.DateField(
        verbose_name='Data do Serviço',
        help_text='Data em que o serviço foi realizado'
    )
    due_date = models.DateField(
        verbose_name='Data de Vencimento',
        help_text='Data de vencimento da solicitação de pagamento'
    )
    category = models.CharField(
        max_length=50,
        verbose_name='Categoria',
        help_text='Categoria da solicitação de pagamento'
    )
    causative_department = models.ForeignKey(
        "financial.UserDepartment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='Departamento Causador',
        help_text='Departamento que causou a solicitação (se aplicável)',
        db_column='id_causative_department',
        related_name='causative_department_payments'
    )
    payment_method = models.CharField(
        max_length=50,
        verbose_name='Forma de Pagamento',
        db_column='id_payment_detail',
        choices=PAYMENT_METHOD_CHOICES
    )
    bank_account = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        verbose_name='ID da Conta Bancária',
        help_text='Identificador da conta bancária para o pagamento (se aplicável)',
        db_column='id_bank_account'
    )
    requesting_status = models.CharField(
        max_length=50,
        verbose_name='Status da Solicitação',
        help_text='Status atual da solicitação de pagamento'
    )
    manager_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Status do Gerente',
        help_text='Status atualizado pelo gerente (se aplicável)'
    )
    manager_status_completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão do Status do Gerente',
        help_text='Data e hora em que o gerente concluiu o status'
    )
    financial_status = models.CharField(
        max_length=50,
        verbose_name='Status Financeiro',
        help_text='Status financeiro da solicitação de pagamento'
    )
    financial_status_completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão do Status Financeiro',
        help_text='Data e hora em que o status financeiro foi concluído'
    )
    action_date = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Data da Ação',
        help_text='Data da ação relacionada à solicitação (se aplicável)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação',
        help_text='Data e hora em que a solicitação foi criada'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Data de Atualização',
        help_text='Data e hora da última atualização da solicitação'
    )
    invoice_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Número da Nota Fiscal',
        help_text='Número da nota fiscal associada (se aplicável)'
    )
    id_omie = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='ID Omie',
        help_text='Identificador no sistema Omie (se aplicável)'
    )

    class Meta:
        db_table = 'payment_requests'
        verbose_name = 'Solicitação de Pagamento'
        verbose_name_plural = 'Solicitações de Pagamento'
        ordering = ['-created_at']

    def __str__(self):
        return f"Solicitação {self.id} - {self.description[:50]}..."


"""
class PaymentRequest(models.Model):
    
    PAYMENT_METHOD_CHOICES = (
        ('PIX', 'PIX'),
        ('TED', 'TED'),
        ('DOC', 'DOC'),
        ('Boleto', 'Boleto'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('Dinheiro', 'Dinheiro'),
        ('Cheque', 'Cheque'),
        ('Transferência Bancária', 'Transferência Bancária'),
        ('Depósito Bancário', 'Depósito Bancário'),
        ('Outros', 'Outros'),
    )
    
    protocol = models.CharField("Protocolo", max_length=14, unique=True)
    id_omie = models.CharField("ID Omie", max_length=50, null=True, blank=True)
    requester = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, verbose_name="Requisitante", related_name='requested_payments'
    )
    manager = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, verbose_name="Gestor", related_name='managed_payments'
    )
    department = models.ForeignKey(
        'financial.UserDepartment', on_delete=models.CASCADE, verbose_name="Setor", related_name='department_payments'
    )
    supplier_name = models.CharField("Fornecedor", max_length=60, blank=True, null=True)
    supplier = models.IntegerField("ID do Fornecedor no Omie")
    category_name = models.CharField("Categoria", max_length=60, blank=True, null=True)
    category = models.CharField("ID da Categoria no Omie", max_length=20)
    id_sale = models.ForeignKey(
        'financial.SaleResume', on_delete=models.CASCADE, verbose_name="Venda", null=True, blank=True
    )
    description = models.TextField("Descrição")
    amount = models.DecimalField("Valor", max_digits=20, decimal_places=2)
    service_date = models.DateField("Data de Serviço")
    due_date = models.DateField("Data de Vencimento")
    category = models.CharField("Categoria", max_length=20)
    causative_department = models.ForeignKey(
        'financial.UserDepartment', on_delete=models.CASCADE, verbose_name="Setor", related_name='causative_department_payments'
    )
    payment_method = models.CharField("Forma de Pagamento", max_length=50, choices=PAYMENT_METHOD_CHOICES)
    # id_bank_account = models.ForeignKey("financial.BankAccount", on_delete=models.CASCADE, verbose_name="Conta Bancária")
    requesting_status = models.CharField("Status da Requisição", max_length=50)
    manager_status = models.CharField("Status do Gestor", max_length=50, null=True, blank=True)
    manager_status_completion_date = models.DateTimeField("Data de Conclusão do Status do Gestor", null=True, blank=True)
    financial_status = models.CharField("Status Financeiro", max_length=50)
    financial_status_completion_date = models.DateTimeField("Data de Conclusão do Status Financeiro", null=True, blank=True)
    invoice_number = models.CharField("Número da NF", max_length=255, null=True, blank=True)
    
    # Logs
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.protocol

    class Meta:
        verbose_name = 'Requisição de Pagamento'
        verbose_name_plural = 'Requisições de Pagamento'
        ordering = ['-created_at']
        db_table = 'payment_requests'
"""


class SaleResume(models.Model): 
    id = models.CharField(primary_key=True, max_length=8)
    name = models.CharField(max_length=255)
    contract_number = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.contract_number} - {self.name}'

    class Meta:
        managed = False
        db_table = 'saleid_customername_view'
        verbose_name_plural = 'Vendas'
        ordering = ['contract_number']

    def save(self, *args, **kwargs):
        raise NotImplementedError("Este modelo é somente leitura e não pode ser salvo.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Este modelo é somente leitura e não pode ser deletado.")


class UserDepartment(models.Model):
    id = models.CharField(primary_key=True, max_length=8)
    id_omie = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, null=True, blank=True)
    teams_bot = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=50)
    updated_at = models.DateTimeField()
    updated_by = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'user_departments'
        verbose_name = 'Departamento de Usuário'
        verbose_name_plural = 'Departamentos de Usuários'
        ordering = ['name']


"""
class BankAccount(models.Model):
    TRANSFER_TYPE_CHOICES = [
        ('PIX', 'PIX'),
        ('TED', 'TED'),
        ('DOC', 'DOC'),
    ]
    
    PIX_KEY_TYPE_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
        ('E-mail', 'E-mail'),
        ('Telefone', 'Telefone'),
        ('Aleatória', 'Aleatória'),
    ]

    id = models.CharField(max_length=8, primary_key=True)
    id_sale = models.CharField(max_length=8, null=True, blank=True)
    id_payment_request_supplier = models.CharField(max_length=8)
    transfer_type = models.CharField(max_length=3, choices=TRANSFER_TYPE_CHOICES, default='PIX')
    account_holder_name = models.CharField(max_length=256)
    bank_name = models.CharField(max_length=256, null=True, blank=True)
    pix_key_type = models.CharField(max_length=10, choices=PIX_KEY_TYPE_CHOICES, default='CPF')
    pix_key = models.CharField(max_length=256, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    account_digit = models.CharField(max_length=2, null=True, blank=True)
    agency_number = models.CharField(max_length=20, null=True, blank=True)
    agency_digit = models.CharField(max_length=2, null=True, blank=True)
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=50)
    updated_at = models.DateTimeField()
    updated_by = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.account_holder_name} - {self.bank_name}'

    class Meta:
        db_table = 'bank_accounts'
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['account_holder_name']
"""


class AppsheetUser(models.Model):
    id = models.CharField(primary_key=True, max_length=8)
    register = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)
    preferred_name = models.CharField(max_length=50)
    profile_image = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1)
    document = models.CharField(max_length=11, unique=True)
    contact_number = models.CharField(max_length=18)
    email = models.CharField(max_length=50)
    password = models.CharField(max_length=256, null=True, blank=True)
    password_reset_token = models.TextField(null=True, blank=True)
    password_reset_token_expiration_time = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    # user_role = models.ForeignKey('UserRole', on_delete=models.CASCADE, db_column='id_user_roles')
    # contract_type = models.ForeignKey('ContractType', on_delete=models.CASCADE, db_column='id_contract_types')
    user_department = models.ForeignKey('UserDepartment', on_delete=models.CASCADE, db_column='id_user_departments')
    # unit = models.ForeignKey('Unit', on_delete=models.CASCADE, db_column='id_units')
    user_manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, db_column='id_user_manager')
    is_gps_location_allowed = models.BooleanField(default=False)
    termination_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    global_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
