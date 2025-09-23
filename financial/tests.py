from django.urls import reverse
from rest_framework import status
from accounts.models import Address, Branch, User
from core.tests import BaseAPITestCase
from resolve_crm.models import Sale
from financial.models import (
    FinancialRecord, Financier, Payment, PaymentInstallment, FranchiseInstallment
)
from unittest.mock import patch
from datetime import date, datetime, timedelta
from django.utils import timezone


class FinancierViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='12345-678',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.financier = Financier.objects.create(
            name="Financiadora Teste",
            cnpj="12345678901234",
            address=self.address,
            phone="(11) 99999-9999",
            email="teste@financiadora.com"
        )
        self.list_url = reverse('api:financier-list')
        self.detail_url = reverse('api:financier-detail', args=[self.financier.id])

    def test_list_financiers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_financier(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.financier.id)

    def test_create_financier(self):
        data = {
            "name": "Nova Financiadora",
            "cnpj": "98765432101234",
            "address_id": self.address.id,
            "phone": "(11) 88888-8888",
            "email": "nova@financiadora.com"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_financier(self):
        data = {
            "name": "Financiadora Atualizada",
            "cnpj": self.financier.cnpj,
            "address_id": self.address.id,
            "phone": "(11) 77777-7777",
            "email": self.financier.email
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.financier.refresh_from_db()
        self.assertEqual(self.financier.name, "Financiadora Atualizada")

    def test_delete_financier(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Financier.objects.filter(id=self.financier.id).exists())


class PaymentViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='customer', password='123456', first_document='12345678900', email='customer@example.com')
        self.seller = User.objects.create_user(username='seller', password='123456', email='seller@example.com')
        self.sales_supervisor = User.objects.create_user(username='supervisor', password='123456', email='supervisor@example.com')
        self.sales_manager = User.objects.create_user(username='manager', password='123456', email='manager@example.com')
        self.address = Address.objects.create(
            zip_code='12345-678',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.branch = Branch.objects.create(name='Branch Test', address=self.address)
        
        self.sale = Sale.objects.create(
            customer=self.user,
            seller=self.seller,
            sales_supervisor=self.sales_supervisor,
            sales_manager=self.sales_manager,
            total_value=1000,
            branch=self.branch,
            is_pre_sale=True,
            status='P'
        )
        self.financier = Financier.objects.create(
            name="Financiadora Teste",
            cnpj="12345678901234",
            address=Address.objects.create(zip_code='00000-111', country='Brasil', state='SP', city='São Paulo', neighborhood='Centro', street='Rua X', number='123'),
            phone="(11) 99999-9999",
            email="teste@financiadora.com"
        )
        self.payment = Payment.objects.create(
            borrower=self.user,
            sale=self.sale,
            value=1000,
            payment_type="C",
            financier=self.financier,
            due_date=timezone.now().date().isoformat()
        )
        self.list_url = reverse('api:payment-list')
        self.detail_url = reverse('api:payment-detail', args=[self.payment.id])

    def test_list_payments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_payment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.payment.id)

    def test_create_payment(self):
        data = {
            "borrower_id": self.user.id,
            "sale_id": self.sale.id,
            "value": 500,
            "payment_type": "D",
            "financier_id": self.financier.id,
            "due_date": timezone.now().date().isoformat()
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_payment(self):
        data = {
            "borrower_id": self.user.id,
            "sale_id": self.sale.id,
            "value": 800,
            "payment_type": self.payment.payment_type,
            "financier_id": self.financier.id,
            "due_date": self.payment.due_date
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.value, 800)

    def test_delete_payment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Payment.objects.filter(id=self.payment.id).exists())


class PaymentInstallmentViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='customer', password='123456', first_document='12345678900', email='customer@example.com')
        self.seller = User.objects.create_user(username='seller', password='123456', email='seller@example.com')
        self.sales_supervisor = User.objects.create_user(username='supervisor', password='123456', email='supervisor@example.com')
        self.sales_manager = User.objects.create_user(username='manager', password='123456', email='manager@example.com')
        self.address = Address.objects.create(
            zip_code='12345-678',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.branch = Branch.objects.create(name='Branch Test', address=self.address)
        self.sale = Sale.objects.create(
            customer=self.user,
            seller=self.seller,
            sales_supervisor=self.sales_supervisor,
            sales_manager=self.sales_manager,
            total_value=1000,
            branch=self.branch,
            is_pre_sale=True,
            status='P'
        )
        self.payment = Payment.objects.create(
            borrower=User.objects.create_user(username='customer2', password='123456', email='customer2@example.com'),
            sale=self.sale,
            value=1000,
            payment_type="C",
            due_date=datetime.now().date()
        )
        self.installment = PaymentInstallment.objects.create(
            payment=self.payment,
            installment_value=500,
            installment_number=1,
            due_date=datetime.now().date()
        )
        self.list_url = reverse('api:payment-installment-list')
        self.detail_url = reverse('api:payment-installment-detail', args=[self.installment.id])

    def test_list_installments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_installment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.installment.id)

    def test_create_installment(self):
        data = {
            "payment": self.payment.id,
            "installment_value": 300,
            "installment_number": 2,
            "due_date": (datetime.now() + timedelta(days=30)).date().isoformat()
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_installment(self):
        data = {
            "payment": self.payment.id,
            "installment_value": 600,
            "installment_number": self.installment.installment_number,
            "due_date": self.installment.due_date
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.installment.refresh_from_db()
        self.assertEqual(self.installment.installment_value, 600)

    def test_delete_installment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PaymentInstallment.objects.filter(id=self.installment.id).exists())


class FranchiseInstallmentViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='customer', password='123456', first_document='12345678900', email='customer@example.com')
        self.seller = User.objects.create_user(username='seller', password='123456', email='seller@example.com')
        self.sales_supervisor = User.objects.create_user(username='supervisor', password='123456', email='supervisor@example.com')
        self.sales_manager = User.objects.create_user(username='manager', password='123456', email='manager@example.com')
        self.address = Address.objects.create(
            zip_code='12345-678',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.branch = Branch.objects.create(name='Branch Test', address=self.address)
        
        self.sale = Sale.objects.create(
            customer=self.user,
            seller=self.seller,
            sales_supervisor=self.sales_supervisor,
            sales_manager=self.sales_manager,
            total_value=1000,
            branch=self.branch,
            is_pre_sale=True,
            status='P'
        )
        self.installment = FranchiseInstallment.objects.create(
            sale=self.sale,
            installment_value=500
        )
        self.list_url = reverse('api:franchise-installment-list')
        self.detail_url = reverse('api:franchise-installment-detail', args=[self.installment.id])

    def test_list_franchise_installments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_franchise_installment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.installment.id)

    def test_create_franchise_installment(self):
        data = {
            "sale_id": self.sale.id,
            "installment_value": 300,
            "is_paid": False
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_franchise_installment(self):
        data = {
            "sale_id": self.sale.id,
            "installment_value": 600,
            "is_paid": True,
            "status": "PG",
            "paid_at": timezone.now().isoformat()
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.installment.refresh_from_db()
        self.assertTrue(self.installment.is_paid)

    def test_delete_franchise_installment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FranchiseInstallment.objects.filter(id=self.installment.id).exists())


class PaymentRequestViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='customer', password='123456', first_document='12345678900', email='customer@example.com')


class FinancialRecordAPITestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('api:financial-record-list')
        self.user2 = User.objects.create_user(username='user2', password='pass123', email='user2@email.com')
        self.financial_record = FinancialRecord.objects.create(
            integration_code='INT123',
            protocol='PROTO001',
            is_receivable=True,
            status='P',
            value=1000.00,
            due_date=date.today(),
            department_code='DEP001',
            category_code='CAT001',
            client_supplier_code=123456789,
            requester=self.user,
            responsible=self.user2
        )

    def test_list_financial_records(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_financial_record(self):
        url = reverse('api:financial-record-detail', args=[self.financial_record.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.financial_record.pk)

    def test_create_financial_record(self):
        data = {
            "integration_code": "INT999",
            "is_receivable": False,
            "status": "S",
            "value": 1500.50,
            "due_date": str(date.today()),
            "department_code": "DEP999",
            "category_code": "CAT999",
            "client_supplier_code": 987654321,
            "requester_id": self.user.id,
            "responsible_id": self.user2.id
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_financial_record(self):
        url = reverse('api:financial-record-detail', args=[self.financial_record.pk])
        data = {"status": "E"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "E")

    def test_delete_financial_record(self):
        url = reverse('api:financial-record-detail', args=[self.financial_record.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FinancialRecord.objects.filter(pk=self.financial_record.pk).exists())

    @patch('simple_history.utils.get_history_user')
    def test_audit_status_tracking(self, mock_get_history_user):
        """Testa se os campos audit_by e audit_response_date são atualizados quando audit_status muda"""
        # Configura o mock para retornar o usuário autenticado
        mock_get_history_user.return_value = self.user
        
        # Cria um financial record com audit_status inicial
        financial_record = FinancialRecord.objects.create(
            integration_code='AUDIT_TEST',
            protocol='AUDIT001',
            is_receivable=True,
            status='S',
            audit_status='AA',  # Aguardando Aprovação
            value=500.00,
            due_date=date.today(),
            department_code='DEP001',
            category_code='CAT001',
            client_supplier_code=123456789,
            requester=self.user,
            responsible=self.user2
        )
        
        # Verifica que os campos de audit não estão preenchidos inicialmente
        self.assertIsNone(financial_record.audit_by)
        self.assertIsNone(financial_record.audit_response_date)
        
        # Atualiza o audit_status
        financial_record.audit_status = 'A'  # Aprovado
        financial_record.save()
        
        # Recarrega o objeto do banco de dados
        financial_record.refresh_from_db()
        
        # Verifica se os campos foram atualizados
        self.assertEqual(financial_record.audit_by, self.user)
        self.assertIsNotNone(financial_record.audit_response_date)
        self.assertAlmostEqual(
            financial_record.audit_response_date,
            timezone.now(),
            delta=timedelta(seconds=5)
        )

    def test_audit_status_tracking_without_user(self):
        """Testa se audit_response_date é atualizado mesmo sem usuário identificado"""
        # Cria um financial record com audit_status inicial
        financial_record = FinancialRecord.objects.create(
            integration_code='AUDIT_TEST2',
            protocol='AUDIT002',
            is_receivable=True,
            status='S',
            audit_status='AA',  # Aguardando Aprovação
            value=750.00,
            due_date=date.today(),
            department_code='DEP002',
            category_code='CAT002',
            client_supplier_code=123456788,
            requester=self.user,
            responsible=self.user2
        )
        
        # Verifica que os campos de audit não estão preenchidos inicialmente
        self.assertIsNone(financial_record.audit_by)
        self.assertIsNone(financial_record.audit_response_date)
        
        # Atualiza o audit_status
        financial_record.audit_status = 'R'  # Reprovado
        financial_record.save()
        
        # Recarrega o objeto do banco de dados
        financial_record.refresh_from_db()
        
        # Verifica se audit_response_date foi atualizado mesmo sem usuário
        self.assertIsNotNone(financial_record.audit_response_date)
        self.assertAlmostEqual(
            financial_record.audit_response_date,
            timezone.now(),
            delta=timedelta(seconds=5)
        )
