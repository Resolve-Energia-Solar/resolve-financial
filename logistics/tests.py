from django.urls import reverse
from rest_framework import status
from accounts.models import Address, Branch
from core.tests import BaseAPITestCase
from field_services.models import RoofType
from logistics.models import Materials, Product, ProductMaterials


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
            branch=self.branch,
            roof_type=self.roof_type
        )
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
            "branch_id": self.branch.id,
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
            "branch_id": self.branch.id,
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
