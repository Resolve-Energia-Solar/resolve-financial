import os
import time
import django
from datetime import date, datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resolve_erp.settings")

from django.conf import settings
settings.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}

django.setup()

from django.core.management import call_command
from django.db import transaction
from django.db.models.signals import post_save

from resolve_crm.signals import send_webhook_on_save

# Desconecta signal
post_save.disconnect(send_webhook_on_save)

call_command("migrate", interactive=False)

from resolve_crm.models import Project, Sale
from field_services.models import Category, Forms, Schedule, Service
from accounts.models import User, Branch, Address
from logistics.models import Product
from django.test import Client

def insert_bulk_data(model, objects, batch_size=5000):
    try:
        start_time = time.time()
        with transaction.atomic():
            model.objects.bulk_create(objects, batch_size=batch_size)
        elapsed_time = time.time() - start_time
        print(f"Inserção em {model.__name__} concluída em {elapsed_time:.2f} segundos.")
        return elapsed_time
    except Exception as e:
        print(f"Erro ao inserir dados em {model.__name__}: {e}")
        return None

def measure_get_request(url):
    client = Client()
    start_time = time.time()
    response = client.get(url)
    elapsed_time = time.time() - start_time
    print(f"GET {url} respondeu em {elapsed_time:.2f} segundos com status {response.status_code}.")
    return elapsed_time, response.status_code

def main():
    total_records = 150000
    form = Forms.objects.create(name="Formulário padrão")
    category = Category.objects.create(name="Categoria padrão")
    user = User.objects.create(username="testuser", password="senha123@", complete_name="Usuário Teste", email="teste@teste.com")
    branch = Branch.objects.create(name="Main Branch")
    product = Product.objects.create(name="Produto teste", product_value=1000.00)
    service = Service.objects.create(name="Serviço padrão", category=category, form=form)
    address = Address.objects.create(street="Rua Padrão", city="Cidade", state="Estado", zip_code="12345678")

    sale_data = [
        Sale(
            customer=user,
            seller=user,
            sales_supervisor=user,
            sales_manager=user,
            total_value=1000.00,
            branch=branch
        ) for _ in range(total_records)
    ]
    sale_time = insert_bulk_data(Sale, sale_data)

    sales = list(Sale.objects.all())

    schedule_data = [
        Schedule(
            schedule_creator=user,
            schedule_date=date.today(),
            schedule_start_time=datetime.now().time(),
            schedule_end_date=date.today(),
            schedule_end_time=datetime.now().time(),
            service=service,
            address=address
        ) for _ in range(total_records)
    ]
    schedule_time = insert_bulk_data(Schedule, schedule_data)

    project_data = [
        Project(
            sale=sales[i],
            product=product,
            designer_status="P",
            status="P"
        ) for i in range(total_records)
    ]
    project_time = insert_bulk_data(Project, project_data)

    print("\n=== Resultados de inserção ===")
    print(f"Tempo de inserção em Sale: {sale_time:.2f} segundos" if sale_time else "Erro em Sale")
    print(f"Tempo de inserção em Schedule: {schedule_time:.2f} segundos" if schedule_time else "Erro em Schedule")
    print(f"Tempo de inserção em Project: {project_time:.2f} segundos" if project_time else "Erro em Project")

    print("\n=== Métricas de Tempo das Requisições GET ===")
    urls = ['/sales/', '/schedules/', '/projects/']

    for url in urls:
        elapsed_time, status_code = measure_get_request(url)
        print(f"Tempo para GET {url}: {elapsed_time:.2f} segundos (status {status_code})")

if __name__ == "__main__":
    main()
