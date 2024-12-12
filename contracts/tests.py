from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import io
from .views import InformacaoFaturaAPIView


class InformacaoFaturaAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('api:invoice_information')

    def test_post_without_file(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Arquivo da fatura é obrigatório.')

    def test_post_with_invalid_file(self):
        invalid_file = io.BytesIO(b"invalid content")
        invalid_file.name = 'invalid.pdf'
        response = self.client.post(self.url, {'bill_file': invalid_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['message'], 'Erro ao processar a fatura.')

    """
    def test_post_with_valid_file(self):
        valid_file = io.BytesIO(b"%PDF-1.4 valid content")
        valid_file.name = 'valid.pdf'
        with self.settings(EXTRACT_DATA_FROM_PDF=lambda x: {'data': 'valid data'}):
            response = self.client.post(self.url, {'bill_file': valid_file}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {'data': 'valid data'})
    """