from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Branch, UserType, Address
from core.tests import BaseAPITestCase
from resolve_crm.models import Origin, Lead, MarketingCampaign, ComercialProposal, Sale, Project, ContractSubmission
from logistics.models import Product
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta


class OriginViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.origin = Origin.objects.create(name="Campanha Digital", type="IB")
        self.list_url = reverse('api:origin-list')
        self.detail_url = reverse('api:origin-detail', args=[self.origin.id])

    def test_list_origin(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_origin(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.origin.id)

    def test_create_origin(self):
        data = {
            "name": "Origem TV",
            "type": "OB"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_origin(self):
        data = {
            "name": "Origem Atualizada",
            "type": "IB"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.origin.refresh_from_db()
        self.assertEqual(self.origin.name, "Origem Atualizada")

    def test_delete_origin(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Origin.objects.filter(id=self.origin.id).exists())


class LeadViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.origin = Origin.objects.create(name="Origem Lead", type="IB")
        self.user = User.objects.create_user(username='seller', password='123456')
        self.address = Address.objects.create(zip_code='12345-678', country='Brazil', state='SP', city='São Paulo', neighborhood='Centro', street='Rua A', number='10')
        self.lead = Lead.objects.create(
            name="Lead Teste",
            phone="11987654321",
            origin=self.origin,
        )
        self.lead.addresses.add(self.address)

        self.list_url = reverse('api:lead-list')
        self.detail_url = reverse('api:lead-detail', args=[self.lead.id])

    def test_list_leads(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_lead(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.lead.id)

    def test_create_lead(self):
        data = {
            "name": "Novo Lead",
            "phone": "11999999999",
            "origin_id": self.origin.id
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_lead(self):
        data = {
            "name": "Lead Atualizado",
            "phone": "11988888888",
            "origin_id": self.origin.id
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.name, "Lead Atualizado")

    def test_delete_lead(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(id=self.lead.id).exists())


import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

class MarketingCampaignViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criar uma imagem em memória
        image = Image.new('RGB', (100, 100), color='white')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        banner_file = SimpleUploadedFile("banner.png", image_io.read(), content_type='image/png')
        self.marketing_campaign = MarketingCampaign.objects.create(
            name="Campanha de Verão",
            start_datetime=datetime.now(),
            end_datetime=datetime.now() + timedelta(days=5),
            description="Promoção de verão",
            banner=banner_file
        )
        self.list_url = reverse('api:marketing-campaign-list')
        self.detail_url = reverse('api:marketing-campaign-detail', args=[self.marketing_campaign.id])

    def test_list_campaigns(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_campaign(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.marketing_campaign.id)

    def test_create_campaign(self):
        # Criar uma imagem em memória
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        banner_file = SimpleUploadedFile("banner2.png", image_io.read(), content_type='image/png')
        data = {
            "name": "Campanha de Inverno",
            "start_datetime": datetime.now().isoformat(),
            "end_datetime": (datetime.now() + timedelta(days=10)).isoformat(),
            "description": "Promoção de inverno",
            "banner": banner_file
        }
        response = self.client.post(self.list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_campaign(self):
        # Criar uma imagem em memória
        image = Image.new('RGB', (100, 100), color='green')
        image_io = io.BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)
        banner_file = SimpleUploadedFile("banner3.png", image_io.read(), content_type='image/png')
        data = {
            "name": "Campanha Atualizada",
            "start_datetime": self.marketing_campaign.start_datetime.isoformat(),
            "end_datetime": self.marketing_campaign.end_datetime.isoformat(),
            "description": "Atualizada",
            "banner": banner_file
        }
        response = self.client.put(self.detail_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.marketing_campaign.refresh_from_db()
        self.assertEqual(self.marketing_campaign.name, "Campanha Atualizada")

    def test_delete_campaign(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MarketingCampaign.objects.filter(id=self.marketing_campaign.id).exists())


class ComercialProposalViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.origin = Origin.objects.create(name="Origem Proposta", type="IB")
        self.lead = Lead.objects.create(name="Lead Proposta", phone="11911112222", origin=self.origin)
        self.user = User.objects.create_user(username='user_proposal', password='123456', email='user_proposal@email.com')
        self.proposal = ComercialProposal.objects.create(
            lead=self.lead,
            due_date=datetime.now().date() + timedelta(days=10),
            value=1000.00,
            status="P",
            created_by=self.user
        )
        self.list_url = reverse('api:marketing-campaign-list').replace('marketing-campaign', 'comercial-proposal')
        self.detail_url = reverse('api:comercial-proposal-detail', args=[self.proposal.id])

    def test_list_proposals(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_proposal(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.proposal.id)

    def test_create_proposal(self):
        data = {
            "lead_id": self.lead.id,
            "due_date": (datetime.now().date() + timedelta(days=5)).isoformat(),
            "value": "2000.00",
            "status": "P",
            "created_by_id": self.user.id
        }
        list_url = self.list_url  # renomear por clareza
        response = self.client.post(list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_proposal(self):
        data = {
            "lead_id": self.lead.id,
            "due_date": self.proposal.due_date.isoformat(),
            "value": "2500.00",
            "status": "A",
            "created_by_id": self.user.id
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.value, 2500.00)


    def test_delete_proposal(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ComercialProposal.objects.filter(id=self.proposal.id).exists())


class SaleViewSetTestCase(BaseAPITestCase):
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
        self.list_url = reverse('api:marketing-campaign-list').replace('marketing-campaign', 'sale')
        self.detail_url = reverse('api:sale-detail', args=[self.sale.id])

    def test_list_sales(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_sale(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.sale.id)

    def test_create_sale(self):
        data = {
            "customer_id": self.user_customer.id,
            "seller_id": self.user_seller.id,
            "sales_supervisor_id": self.user_supervisor.id,
            "sales_manager_id": self.user_manager.id,
            "branch_id": self.branch.id,
            "total_value": "2000.000",
        }
        response = self.client.post(self.list_url, data, format='json')
        # Dependendo da lógica interna do create, pode ser necessário ajustar dados.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_sale(self):
        data = {
            "customer_id": self.user_customer.id,
            "seller_id": self.user_seller.id,
            "sales_supervisor_id": self.user_supervisor.id,
            "sales_manager_id": self.user_manager.id,
            "branch_id": self.branch.id,
            "total_value": "3000.000",
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.total_value, 3000.000)

    def test_delete_sale(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Sale.objects.filter(id=self.sale.id).exists())


class ProjectViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user_customer = User.objects.create_user(username='cust_project', password='123456', first_document='33333333333', email='cust_project@example.com')
        self.user_seller = User.objects.create_user(username='seller_project', password='123456', first_document='44444444444', email='seller_project@example.com')
        self.user_supervisor = User.objects.create_user(username='sup_project', password='123456', first_document='55555555555', email='sup_project@example.com')
        self.user_manager = User.objects.create_user(username='manager_project', password='123456', first_document='66666666666', email='manager_project@example.com')
        self.branch = Branch.objects.create(name='Filial Project', address=Address.objects.create(zip_code='11111111', country='Brazil', state='MG', city='Belo Horizonte', neighborhood='Centro', street='Rua C', number='30'))
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
            status="P"
        )
        self.list_url = reverse('api:marketing-campaign-list').replace('marketing-campaign', 'project')
        self.detail_url = reverse('api:project-detail', args=[self.project.id])

    def test_list_projects(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_project(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.project.id)

    def test_create_project(self):
        data = {
            "sale_id": self.sale.id,
            "status": "P",
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_project(self):
        data = {
            "sale_id": self.sale.id,
            "status": "EA",
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "EA")

    def test_delete_project(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())


class ContractSubmissionViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user_customer = User.objects.create_user(username='cust_cont', password='123456', first_document='77777777777', email='cust_cont@example.com')
        self.user_seller = User.objects.create_user(username='seller_cont', password='123456', first_document='88888888888', email='seller_cont@example.com')
        self.user_supervisor = User.objects.create_user(username='sup_cont', password='123456', first_document='99999999999', email='sup_cont@example.com')
        self.user_manager = User.objects.create_user(username='manager_cont', password='123456', first_document='00000000000', email='manager_cont@example.com')
        self.branch = Branch.objects.create(name='Filial Contract', address=Address.objects.create(zip_code='22222222', country='Brazil', state='SP', city='Campinas', neighborhood='Bairro', street='Rua D', number='40'))
        self.sale = Sale.objects.create(
            customer=self.user_customer,
            seller=self.user_seller,
            sales_supervisor=self.user_supervisor,
            sales_manager=self.user_manager,
            branch=self.branch,
            total_value=1500.000,
        )
        self.contract_submission = ContractSubmission.objects.create(
            sale=self.sale,
            submit_datetime=datetime.now(),
            status="P",
            due_date=(datetime.now().date() + timedelta(days=5)),
            link="http://example.com/contract"
        )
        self.list_url = reverse('api:marketing-campaign-list').replace('marketing-campaign', 'contract-submission')
        self.detail_url = reverse('api:contract-submission-detail', args=[self.contract_submission.id])

    def test_list_contract_submissions(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_contract_submission(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.contract_submission.id)

    def test_create_contract_submission(self):
        data = {
            "sale_id": self.sale.id,
            "submit_datetime": datetime.now().isoformat(),
            "status": "P",
            "due_date": (datetime.now().date() + timedelta(days=3)).isoformat(),
            "link": "http://example.com/contract2"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_contract_submission(self):
        data = {
            "sale_id": self.sale.id,
            "submit_datetime": self.contract_submission.submit_datetime.isoformat(),
            "status": "A",
            "due_date": self.contract_submission.due_date.isoformat(),
            "link": "http://example.com/contract_updated"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contract_submission.refresh_from_db()
        self.assertEqual(self.contract_submission.status, "A")

    def test_delete_contract_submission(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ContractSubmission.objects.filter(id=self.contract_submission.id).exists())
