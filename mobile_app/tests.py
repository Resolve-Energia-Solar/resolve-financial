import io
from django.urls import reverse
from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from PIL import Image

from accounts.models import Address, Branch, User
from core.tests import BaseAPITestCase
from mobile_app.models import Discount
from resolve_crm.models import Sale, Project


class CustomerLoginViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            email="customer@example.com",
            password="password123",
            first_document="123456789",
            birth_date="2000-01-01",
            is_active=True,
            username="customer"
        )
        self.user_seller = User.objects.create_user(username='seller_user', password='123456', first_document='10987654321', email='seller@example.com')
        self.user_supervisor = User.objects.create_user(username='supervisor', password='123456', first_document='11111111111', email='supervisor@example.com')
        self.user_manager = User.objects.create_user(username='manager', password='123456', first_document='22222222222', email='manager@example.com')
        self.branch = Branch.objects.create(name='Filial Venda', address=Address.objects.create(zip_code='00000000', country='Brazil', state='RJ', city='Rio', neighborhood='Centro', street='Rua B', number='20'))
        self.sale = Sale.objects.create(
            customer=self.user,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=1000.000,
        )
        self.url = reverse('mobile_app:customer_login')

    def test_login_success(self):
        data = {"first_document": "123456789", "birth_date": "2000-01-01"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_invalid_credentials(self):
        data = {"first_document": "987654321", "birth_date": "1990-01-01"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        data = {"first_document": "123456789", "birth_date": "2000-01-01"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DiscountViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        image = Image.new('RGB', (100, 100), color='green')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        self.image = SimpleUploadedFile("banner.png", image_io.getvalue(), content_type='image/png')
        self.discount = Discount.objects.create(
            title="Promoção Teste",
            description="Descrição da promoção",
            link="http://example.com",
            banner=self.image
        )
        self.list_url = reverse('mobile_app:discount-list')
        self.detail_url = reverse('mobile_app:discount-detail', args=[self.discount.id])

    def test_list_discounts(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_discount(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Promoção Teste")

    def test_create_discount(self):
        image = Image.new('RGB', (100, 100), color='green')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        image_file = SimpleUploadedFile("banner.png", image_io.getvalue(), content_type='image/png')
        data = {
            "title": "Nova Promoção",
            "description": "Nova descrição",
            "link": "http://example.com/new",
            "banner": image_file
        }
        response = self.client.post(self.list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_discount(self):
        image = Image.new('RGB', (100, 100), color='green')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        image_file = SimpleUploadedFile("banner.png", image_io.read(), content_type='image/png')
        data = {"title": "Promoção Atualizada", "banner": image_file}
        response = self.client.patch(self.detail_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.discount.refresh_from_db()
        self.assertEqual(self.discount.title, "Promoção Atualizada")

    def test_delete_discount(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Discount.objects.filter(id=self.discount.id).exists())


class MonitoringListViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('mobile_app:monitoring-list')

    def test_monitoring_list(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class MonitoringDetailViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('mobile_app:monitoring-detail', args=[1])

    def test_monitoring_detail(self):
        response = self.client.get(self.url, {'month': '10', 'year': '2024'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class DocumentationViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user_customer = User.objects.create_user(username='customer', password='123456', first_document='12345678901', email='customer@example.com')
        self.user_seller = User.objects.create_user(username='seller_user', password='123456', first_document='10987654321', email='seller@example.com')
        self.user_supervisor = User.objects.create_user(username='supervisor', password='123456', first_document='11111111111', email='supervisor@example.com')
        self.user_manager = User.objects.create_user(username='manager', password='123456', first_document='22222222222', email='manager@example.com')
        self.branch = Branch.objects.create(name='Filial Venda', address=Address.objects.create(zip_code='00000000', country='Brazil', state='RJ', city='Rio', neighborhood='Centro', street='Rua B', number='20'))
        self.sale = Sale.objects.create(
            customer=self.user_customer,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=1000.000,
        )
        self.project = Project.objects.create(
            sale=self.sale,
            start_date=now(),
            project_number="P001"
        )
        self.project.create_deadlines()
        self.url = reverse('mobile_app:documentation', args=[self.project.id])

    def test_get_documentation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FinancialViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user_customer = User.objects.create_user(username='customer', password='123456', first_document='12345678901', email='customer@example.com')
        self.user_seller = User.objects.create_user(username='seller_user', password='123456', first_document='10987654321', email='seller@example.com')
        self.user_supervisor = User.objects.create_user(username='supervisor', password='123456', first_document='11111111111', email='supervisor@example.com')
        self.user_manager = User.objects.create_user(username='manager', password='123456', first_document='22222222222', email='manager@example.com')
        self.branch = Branch.objects.create(name='Filial Venda', address=Address.objects.create(zip_code='00000000', country='Brazil', state='RJ', city='Rio', neighborhood='Centro', street='Rua B', number='20'))
        self.sale = Sale.objects.create(
            customer=self.user_customer,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=1000.000
        )
        self.url = reverse('mobile_app:financial', args=[self.sale.id])

    def test_get_financial(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_paid'], 0)


class AttachDocumentViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('mobile_app:attach-document')

    def test_attach_document(self):
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        data = {
            "name": "Documento Teste",
            "file": file
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
