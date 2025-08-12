from django.urls import reverse
from rest_framework import status
from accounts.models import Address, Branch, User
from core.tests import BaseAPITestCase
from field_services.models import RoofType
from logistics.models import Materials, Product, ProductMaterials, Purchase
from resolve_crm.models import Sale, Project
from datetime import date


class MaterialsViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.material = Materials.objects.create(name="Material Teste", price=100)
        self.list_url = reverse('api:material-list')
        self.detail_url = reverse('api:material-detail', args=[self.material.id])

    def test_list_materials(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_material(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.material.id)

    def test_create_material(self):
        data = {"name": "Novo Material", "price": 150}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_material(self):
        data = {"name": "Material Atualizado", "price": 200}
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.material.refresh_from_db()
        self.assertEqual(self.material.name, "Material Atualizado")

    def test_delete_material(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Materials.objects.filter(id=self.material.id).exists())


class ProductViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(zip_code='12345', country='Country', state='State', city='City', neighborhood='Downtown', street='Street', number='100')
        self.branch = Branch.objects.create(name='Filial teste', address=self.address)
        self.roof_type = RoofType.objects.create(name="Tipo de Telhado")
        self.material = Materials.objects.create(name="Material para Produto", price=50)
        self.product = Product.objects.create(
            name="Produto Teste",
            description="Descrição do produto",
            product_value=1000,
            reference_value=900,
            cost_value=700,
            roof_type=self.roof_type
        )
        self.product.branch.add(self.branch)
        self.product_material = ProductMaterials.objects.create(product=self.product, material=self.material, amount=10)
        self.list_url = reverse('api:product-list')
        self.detail_url = reverse('api:product-detail', args=[self.product.id])

    def test_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_product(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)

    def test_create_product_with_materials(self):
        data = {
            "name": "Produto Novo",
            "description": "Descrição do produto novo",
            "product_value": 1500,
            "reference_value": 1200,
            "cost_value": 1000,
            "branch_ids": [self.branch.id],
            "roof_type_id": self.roof_type.id,
            "materials_ids": [{"material_id": self.material.id, "amount": 5}]
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.get(name="Produto Novo").name, "Produto Novo")

    def test_update_product_with_materials(self):
        data = {
            "name": "Produto Atualizado",
            "description": "Descrição atualizada",
            "product_value": 2000,
            "reference_value": 1800,
            "cost_value": 1500,
            "branch_ids": [self.branch.id],
            "roof_type_id": self.roof_type.id,
            "materials_ids": [{"material_id": self.material.id, "amount": 20}]
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Produto Atualizado")
        self.assertEqual(self.product.materials.first().amount, 20)

    def test_delete_product(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())


class PurchaseViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criar usuários
        self.customer = User.objects.create_user(
            username='customer_test',
            password='123456',
            first_document='12345678901',
            email='customer@test.com',
            complete_name='João Silva'
        )
        self.seller = User.objects.create_user(
            username='seller_test',
            password='123456',
            first_document='98765432109',
            email='seller@test.com',
            complete_name='Maria Santos'
        )
        self.supervisor = User.objects.create_user(
            username='supervisor_test',
            password='123456',
            first_document='11111111111',
            email='supervisor@test.com',
            complete_name='Pedro Costa'
        )
        self.manager = User.objects.create_user(
            username='manager_test',
            password='123456',
            first_document='22222222222',
            email='manager@test.com',
            complete_name='Ana Oliveira'
        )
        self.supplier = User.objects.create_user(
            username='supplier_test',
            password='123456',
            first_document='33333333333',
            email='supplier@test.com',
            complete_name='Fornecedor ABC'
        )
        
        # Criar endereço e filial
        self.address = Address.objects.create(
            zip_code='12345-678',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.branch = Branch.objects.create(name='Filial Teste', address=self.address)
        
        # Criar venda
        self.sale = Sale.objects.create(
            customer=self.customer,
            seller=self.seller,
            sales_supervisor=self.supervisor,
            sales_manager=self.manager,
            total_value=1000.00,
            branch=self.branch,
            is_pre_sale=True,
            status='P'
        )
        
        # Criar projeto
        self.project = Project.objects.create(
            sale=self.sale,
            status='P',
            project_number='PROJ-2024-001'
        )
        
        # Criar compra
        self.purchase = Purchase.objects.create(
            project=self.project,
            supplier=self.supplier,
            purchase_date=date(2024, 1, 15),
            status='P',
            purchase_value=500.00,
            delivery_forecast=date(2024, 2, 15),
            delivery_number='ENT-001'
        )
        
        self.list_url = reverse('api:purchase-list')
        self.detail_url = reverse('api:purchase-detail', args=[self.purchase.id])

    def test_list_purchases(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_purchase(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.purchase.id)

    def test_create_purchase(self):
        data = {
            "project_id": self.project.id,
            "supplier_id": self.supplier.id,
            "purchase_date": "2024-01-20",
            "status": "P",
            "purchase_value": "750.00",
            "delivery_forecast": "2024-02-20",
            "delivery_number": "ENT-002"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_purchase(self):
        data = {
            "project_id": self.project.id,
            "supplier_id": self.supplier.id,
            "purchase_date": "2024-01-25",
            "status": "R",
            "purchase_value": "600.00",
            "delivery_forecast": "2024-02-25",
            "delivery_number": "ENT-001-ATUALIZADO"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.status, "R")

    def test_delete_purchase(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Purchase.objects.filter(id=self.purchase.id).exists())

    def test_filter_by_customer_id(self):
        response = self.client.get(f"{self.list_url}?customer={self.customer.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_customer_name(self):
        response = self.client.get(f"{self.list_url}?customer_name=João")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_customer_document(self):
        response = self.client.get(f"{self.list_url}?customer_document=12345678901")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_customer_email(self):
        response = self.client.get(f"{self.list_url}?customer_email=customer@test.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_supplier_name(self):
        response = self.client.get(f"{self.list_url}?supplier_name=Fornecedor")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_project_number(self):
        response = self.client.get(f"{self.list_url}?project_number=PROJ-2024-001")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_status(self):
        response = self.client.get(f"{self.list_url}?status=P")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_purchase_date_range(self):
        response = self.client.get(f"{self.list_url}?purchase_date__gte=2024-01-01&purchase_date__lte=2024-01-31")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_purchase_value(self):
        response = self.client.get(f"{self.list_url}?purchase_value__gte=400&purchase_value__lte=600")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_general_search(self):
        response = self.client.get(f"{self.list_url}?q=João Silva")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_combined_filters(self):
        response = self.client.get(
            f"{self.list_url}?customer={self.customer.id}&status=P&purchase_value__gte=400"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.purchase.id)

    def test_filter_by_multiple_customers(self):
        # Criar outro cliente e compra
        customer2 = User.objects.create_user(
            username='customer2_test',
            password='123456',
            first_document='44444444444',
            email='customer2@test.com',
            complete_name='Carlos Lima'
        )
        sale2 = Sale.objects.create(
            customer=customer2,
            seller=self.seller,
            sales_supervisor=self.supervisor,
            sales_manager=self.manager,
            total_value=2000.00,
            branch=self.branch,
            is_pre_sale=True,
            status='P'
        )
        project2 = Project.objects.create(sale=sale2, status='P')
        purchase2 = Purchase.objects.create(
            project=project2,
            supplier=self.supplier,
            purchase_date=date(2024, 1, 20),
            status='P',
            purchase_value=1000.00
        )
        
        response = self.client.get(f"{self.list_url}?customer__in={self.customer.id},{customer2.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
