from django.urls import reverse
from rest_framework import status
from accounts.models import User, Address
from core.tests import BaseAPITestCase
from resolve_crm.models import Project, Sale, Lead, Origin
from engineering.models import (
    EnergyCompany, RequestsEnergyCompany, Units, SupplyAdequance, SituationEnergyCompany, ResquestType
)
from logistics.models import Product
from accounts.models import Branch
from datetime import datetime, timedelta


class EnergyCompanyViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='11111-000',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Centro',
            street='Rua Teste',
            number='123'
        )
        self.company = EnergyCompany.objects.create(
            name="Companhia de Energia Teste",
            cnpj="1234567890001",
            address=self.address,
            phone="(11) 99999-9999",
            email="contato@companhia.com"
        )
        self.list_url = reverse('api:energycompany-list')
        self.detail_url = reverse('api:energycompany-detail', args=[self.company.id])

    def test_list_energy_companies(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_energy_company(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.company.id)

    def test_create_energy_company(self):
        data = {
            "name": "Companhia Nova",
            "cnpj": "9876543210001",
            "address_id": self.address.id
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_energy_company(self):
        data = {
            "name": "Companhia Atualizada",
            "cnpj": "1234567890001",
            "address_id": self.address.id
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "Companhia Atualizada")

    def test_delete_energy_company(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EnergyCompany.objects.filter(id=self.company.id).exists())


class SupplyAdequanceViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.supply = SupplyAdequance.objects.create(name="Adequação Teste")
        self.list_url = reverse('api:supply-adequance-list')
        self.detail_url = reverse('api:supply-adequance-detail', args=[self.supply.id])

    def test_list_supply_adequances(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_supply_adequance(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.supply.id)

    def test_create_supply_adequance(self):
        data = {
            "name": "Nova Adequação"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_supply_adequance(self):
        data = {
            "name": "Adequação Atualizada"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.supply.refresh_from_db()
        self.assertEqual(self.supply.name, "Adequação Atualizada")

    def test_delete_supply_adequance(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SupplyAdequance.objects.filter(id=self.supply.id).exists())


class SituationEnergyCompanyViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.situation = SituationEnergyCompany.objects.create(name="Situação Inicial")
        self.list_url = reverse('api:situation-energy-company-list')
        self.detail_url = reverse('api:situation-energy-company-detail', args=[self.situation.id])

    def test_list_situations(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_situation(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.situation.id)

    def test_create_situation(self):
        data = {
            "name": "Nova Situação"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_situation(self):
        data = {
            "name": "Situação Atualizada"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.situation.refresh_from_db()
        self.assertEqual(self.situation.name, "Situação Atualizada")

    def test_delete_situation(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SituationEnergyCompany.objects.filter(id=self.situation.id).exists())


class ResquestTypeViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.req_type = ResquestType.objects.create(name="Tipo de Solicitação Teste")
        self.list_url = reverse('api:resquest-type-list')
        self.detail_url = reverse('api:resquest-type-detail', args=[self.req_type.id])

    def test_list_request_types(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_request_type(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.req_type.id)

    def test_create_request_type(self):
        data = {
            "name": "Novo Tipo de Solicitação"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_request_type(self):
        data = {
            "name": "Tipo de Solicitação Atualizada"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.req_type.refresh_from_db()
        self.assertEqual(self.req_type.name, "Tipo de Solicitação Atualizada")

    def test_delete_request_type(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ResquestType.objects.filter(id=self.req_type.id).exists())


class UnitsViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criando dependências
        self.user_customer = User.objects.create_user(username='customer_units', password='123456', first_document='99999999999', email='customer_units@example.com')
        self.user_seller = User.objects.create_user(username='seller_units', password='123456', first_document='88888888888', email='seller_units@example.com')
        self.user_supervisor = User.objects.create_user(username='sup_units', password='123456', first_document='77777777777', email='sup_units@example.com')
        self.user_manager = User.objects.create_user(username='manager_units', password='123456', first_document='66666666666', email='manager_units@example.com')
        self.branch = Branch.objects.create(name='Filial Units', address=Address.objects.create(zip_code='33333333', country='Brazil', state='MG', city='BH', neighborhood='Centro', street='Rua X', number='99'))
        self.origin = Origin.objects.create(name="Origem Unidades", type="IB")
        self.lead = Lead.objects.create(name="Lead Units", phone="11999999999", origin=self.origin)
        self.sale = Sale.objects.create(
            customer=self.user_customer,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=1000.000,
        )
        self.project = Project.objects.create(sale=self.sale, status="P")
        self.address = Address.objects.create(
            zip_code='44444-000',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Bairro',
            street='Rua Y',
            number='10'
        )
        self.supply_adequance = SupplyAdequance.objects.create(name="Adequação Unit Test")
        self.unit = Units.objects.create(project=self.project, name="Unidade Teste", address=self.address, type='M')
        self.unit.supply_adquance.add(self.supply_adequance)

        self.list_url = reverse('api:unit-list')
        self.detail_url = reverse('api:unit-detail', args=[self.unit.id])

    def test_list_units(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_unit(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.unit.id)

    def test_create_unit(self):
        new_address = Address.objects.create(
            zip_code='55555-000',
            country='Brasil',
            state='RJ',
            city='Rio de Janeiro',
            neighborhood='Centro',
            street='Rua Z',
            number='100'
        )
        data = {
            "name": "Nova Unidade",
            "address_id": new_address.id,
            "project_id": self.project.id,
            "supply_adquance_ids": [self.supply_adequance.id],
            "type": "B"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_unit(self):
        data = {
            "name": "Unidade Atualizada",
            "address_id": self.address.id,
            "project_id": self.project.id,
            "supply_adquance_ids": [self.supply_adequance.id],
            "type": "T"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.name, "Unidade Atualizada")

    def test_delete_unit(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Units.objects.filter(id=self.unit.id).exists())


class RequestsEnergyCompanyViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Dependências
        self.address = Address.objects.create(
            zip_code='66666-000',
            country='Brasil',
            state='SP',
            city='São Paulo',
            neighborhood='Bairro',
            street='Rua W',
            number='11'
        )
        self.origin = Origin.objects.create(name="Origem ReqEnergy", type="IB")
        self.user_customer = User.objects.create_user(username='customer_req', password='123456', first_document='11111111111', email='customer_req@example.com')
        self.user_seller = User.objects.create_user(username='seller_req', password='123456', first_document='22222222222', email='seller_req@example.com')
        self.user_supervisor = User.objects.create_user(username='sup_req', password='123456', first_document='33333333333', email='sup_req@example.com')
        self.user_manager = User.objects.create_user(username='manager_req', password='123456', first_document='44444444444', email='manager_req@example.com')
        self.branch = Branch.objects.create(name='Filial ReqEnergy', address=self.address)
        
        self.lead = Lead.objects.create(name="Lead Req", phone="11988888888", origin=self.origin)
        self.sale = Sale.objects.create(
            customer=self.user_customer,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=2000.000,
        )
        self.project = Project.objects.create(sale=self.sale, status="P")
        self.supply_adequance = SupplyAdequance.objects.create(name="Adequação Req")
        self.unit = Units.objects.create(project=self.project, name="Unidade Req", address=self.address, type='M')
        self.unit.supply_adquance.add(self.supply_adequance)
        self.company = EnergyCompany.objects.create(
            name="Companhia Req",
            cnpj="1231231230001",
            address=self.address
        )
        self.req_type = ResquestType.objects.create(name="Tipo Req")
        self.situation = SituationEnergyCompany.objects.create(name="Situação Req")
        self.requested_by = self.user_seller

        self.req_energy = RequestsEnergyCompany.objects.create(
            company=self.company,
            project=self.project,
            unit=self.unit,
            type=self.req_type,
            request_date=datetime.now().date(),
            status="S",
            requested_by=self.requested_by
        )
        self.req_energy.situation.add(self.situation)

        self.list_url = reverse('api:requestsenergycompany-list')
        self.detail_url = reverse('api:requestsenergycompany-detail', args=[self.req_energy.id])

    def test_list_requests_energy_company(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_requests_energy_company(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.req_energy.id)

    def test_create_requests_energy_company(self):
        data = {
            "company_id": self.company.id,
            "project_id": self.project.id,
            "unit_id": self.unit.id,
            "type_id": self.req_type.id,
            "situation_ids": [self.situation.id],
            "requested_by_id": self.requested_by.id,
            "request_date": datetime.now().date().isoformat(),
            "status": "D"  # Deferido
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_requests_energy_company(self):
        data = {
            "company_id": self.company.id,
            "project_id": self.project.id,
            "unit_id": self.unit.id,
            "type_id": self.req_type.id,
            "situation_ids": [self.situation.id],
            "requested_by_id": self.requested_by.id,
            "request_date": self.req_energy.request_date.isoformat(),
            "status": "I"  # Indeferido
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.req_energy.refresh_from_db()
        self.assertEqual(self.req_energy.status, "I")

    def test_delete_requests_energy_company(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RequestsEnergyCompany.objects.filter(id=self.req_energy.id).exists())
