from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    DocumentType, DocumentSubType, Attachment, Comment, Board, Column, Task, TaskTemplates
)
from accounts.models import Address, User, Branch
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile


class BaseAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username='admin', email='user@email.com', password='admin123')
        self.client.force_authenticate(user=self.user)
        

class DocumentTypeViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.doc_type = DocumentType.objects.create(
            name="Contrato", 
            app_label="contracts", 
            reusable=True, 
            required=False
        )
        self.list_url = reverse('api:document-type-list')
        self.detail_url = reverse('api:document-type-detail', args=[self.doc_type.id])
        
    def test_list_document_types(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        
    def test_retrieve_document_type(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.doc_type.id)

    def test_create_document_type(self):
        data = {
            "name": "Ordem de Serviço",
            "app_label": "contracts",
            "reusable": False,
            "required": True
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_update_document_type(self):
        data = {
            "name": "Contrato Atualizado",
            "app_label": "contracts",
            "reusable": True,
            "required": False
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.doc_type.refresh_from_db()
        self.assertEqual(self.doc_type.name, "Contrato Atualizado")

    def test_delete_document_type(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DocumentType.objects.filter(id=self.doc_type.id).exists())
        

class DocumentSubTypeViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.doc_type = DocumentType.objects.create(
            name="Proposta", 
            app_label="contracts", 
            reusable=False, 
            required=True
        )
        self.subtype = DocumentSubType.objects.create(
            name="Proposta Inicial",
            document_type=self.doc_type
        )
        self.list_url = reverse('api:document-subtype-list')
        self.detail_url = reverse('api:document-subtype-detail', args=[self.subtype.id])
        
    def test_list_document_subtypes(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_document_subtype(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.subtype.id)


class ContentTypeViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criando um ContentType qualquer
        self.content_type = ContentType.objects.get_for_model(DocumentType)
        self.list_url = reverse('api:content-type-list')
        # Detail requer um ID, mas como content_types geralmente são criados pelo Django
        # vamos assumir que self.content_type existe
        self.detail_url = reverse('api:content-type-detail', args=[self.content_type.id])

    def test_list_content_types(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_retrieve_content_type(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.content_type.id)
        
    # Este endpoint está definido com http_method_names = ['get'], portanto não testaremos POST/PUT/DELETE.


class BoardViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )
        self.branch = Branch.objects.create(name='Filial Teste', address=self.address)
        self.board = Board.objects.create(
            title="Board de Teste",
            description="Descrição do Board",
            branch=self.branch,
            is_lead=False,
        )
        self.list_url = reverse('api:board-list')
        self.detail_url = reverse('api:board-detail', args=[self.board.id])

    def test_list_boards(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        
    def test_retrieve_board(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.board.id)

    def test_create_board(self):
        data = {
            "title": "Novo Board",
            "description": "Descrição do Novo Board",
            "branch_id": self.branch.id,
            "columns_ids": []
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_board(self):
        data = {
            "title": "Board Atualizado",
            "description": "Nova descrição",
            "branch_id": self.branch.id,
            "columns_ids": []
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Board Atualizado")

    def test_delete_board(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(id=self.board.id).exists())


class ColumnViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )
        self.branch = Branch.objects.create(name='Filial Coluna', address=self.address)
        self.board = Board.objects.create(
            title="Board para Colunas",
            description="Descrição do Board",
            branch=self.branch,
            is_lead=False,
        )
        self.column = Column.objects.create(
            name="Coluna Teste",
            position=1,
            board=self.board
        )
        self.list_url = reverse('api:column-list')
        self.detail_url = reverse('api:column-detail', args=[self.column.id])

    def test_list_columns(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_column(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.column.id)


class TaskTemplatesViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )
        self.branch = Branch.objects.create(name='Filial Template', address=self.address)
        self.board = Board.objects.create(
            title="Board para Templates",
            description="Descrição do Board",
            branch=self.branch,
            is_lead=False,
        )
        self.column = Column.objects.create(
            name="Coluna Template",
            position=1,
            board=self.board
        )
        self.template = TaskTemplates.objects.create(
            board=self.board,
            title="Template Teste",
            deadline=5,
            auto_create=False,
            column=self.column,
            description="Descrição do Template"
        )
        self.list_url = reverse('api:task-template-list')
        self.detail_url = reverse('api:task-template-detail', args=[self.template.id])

    def test_list_task_templates(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_task_template(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.template.id)


class TaskViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )
        self.user = User.objects.create_user(username='usuario_teste', password='123456')
        self.branch = Branch.objects.create(name='Filial Tarefa', address=self.address)
        self.board = Board.objects.create(
            title="Board para Tarefas",
            description="Descrição do Board",
            branch=self.branch,
            is_lead=False,
        )
        self.column = Column.objects.create(
            name="Coluna Tarefa",
            position=1,
            board=self.board
        )
        self.content_type = ContentType.objects.get_for_model(Board)
        self.task = Task.objects.create(
            project=None,
            title="Tarefa Teste",
            column=self.column,
            description="Descrição da Tarefa",
            owner=self.user,
            due_date="2100-01-01T00:00:00Z",
        )
        self.list_url = reverse('api:task-list')
        self.detail_url = reverse('api:task-detail', args=[self.task.id])

    def test_list_tasks(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_task(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.task.id)

    def test_create_task(self):
        data = {
            "title": "Nova Tarefa",
            "description": "Descrição da nova tarefa",
            "owner_id": self.user.id,
            "board_id": self.board.id,
            "content_type_id": self.content_type.id,
            "column_id": self.column.id,
            "due_date": "2100-02-01T00:00:00Z"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_task(self):
        data = {
            "title": "Tarefa Atualizada",
            "description": "Nova descrição",
            "owner_id": self.user.id,
            "board_id": self.board.id,
            "content_type_id": self.content_type.id,
            "lead_id": None,
            "column_id": self.column.id,
            "due_date": "2100-03-01T00:00:00Z"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Tarefa Atualizada")

    def test_delete_task(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())


class HistoryViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criando um Board e obtendo seu content_type para testar histórico
        self.address = Address.objects.create(
            zip_code='12345678',
            country='Brazil',
            state='PA',
            city='Belém',
            neighborhood='Barreiro',
            street='Passagem Boa Fé',
            number='123'
        )
        self.branch = Branch.objects.create(name='Filial História', address=self.address)
        self.board = Board.objects.create(
            title="Board Histórico",
            description="Descrição do Board",
            branch=self.branch,
            is_lead=False,
        )
        self.content_type = ContentType.objects.get_for_model(Board)
        self.history_url = reverse('api:history')
        
    def test_history_without_params(self):
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content_type e object_id são obrigatórios.', response.data['message'])

    def test_history_with_invalid_ids(self):
        # content_type existe, mas object_id não
        response = self.client.get(self.history_url, {'content_type': 999, 'object_id': 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_history_with_valid_params_no_changes(self):
        response = self.client.get(self.history_url, {'content_type': self.content_type.id, 'object_id': self.board.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('changes', response.data)
        self.assertEqual(len(response.data['changes']), 0)  # Sem histórico gerado, deve retornar vazio

        # Caso queira gerar histórico, você pode editar o objeto antes e chamar novamente a view.


class AttachmentViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Cria dependências para o Attachment
        self.user = User.objects.create_user(username='attachment_user', password='123456')
        self.doc_type = DocumentType.objects.create(
            name="Documento de Teste",
            app_label="contracts",
            reusable=False,
            required=False
        )
        self.content_type = ContentType.objects.get_for_model(DocumentType)

        # Cria um arquivo de teste
        self.test_file = SimpleUploadedFile("testfile.txt", b"file_content", content_type=self.content_type)

        self.attachment = Attachment.objects.create(
            object_id=1,
            content_type=self.content_type,
            file=self.test_file,
            status='pendente',
            document_type=self.doc_type,
            description='Anexo de teste'
        )

        self.list_url = reverse('api:attachment-list')
        self.detail_url = reverse('api:attachment-detail', args=[self.attachment.id])

    def test_list_attachments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_attachment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.attachment.id)

    def test_create_attachment(self):
        new_file = SimpleUploadedFile("novoteste.txt", b"novo_conteudo", content_type=self.content_type)
        data = {
            "object_id": 2,
            "content_type_id": self.content_type.id,
            "file": new_file,
            "document_type_id": self.doc_type.id,
            "description": "Novo anexo"
        }
        response = self.client.post(self.list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(Attachment.objects.filter(id=response.data['id']).exists())

    def test_update_attachment(self):
        new_file = SimpleUploadedFile("novoteste.txt", b"novo_conteudo", content_type=self.content_type)
        data = {
            "object_id": 1,
            "content_type_id": self.content_type.id,
            "description": "Anexo atualizado",
            "file": new_file
        }
        response = self.client.patch(self.detail_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.description, "Anexo atualizado")

    def test_delete_attachment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Attachment.objects.filter(id=self.attachment.id).exists())


class CommentViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Criando usuário autor do comentário
        self.author = User.objects.create_user(username='comentador', password='abc123')

        # Criando um ContentType para associar ao comentário
        # Aqui usamos DocumentType apenas como exemplo, pode ser qualquer modelo
        self.doc_type = DocumentType.objects.create(
            name="Documento Comentado",
            app_label="contracts",
            reusable=False,
            required=False
        )
        self.content_type = ContentType.objects.get_for_model(DocumentType)
        
        self.comment = Comment.objects.create(
            object_id=1,
            content_type=self.content_type,
            author=self.author,
            text="Comentário inicial"
        )

        self.list_url = reverse('api:comment-list')
        self.detail_url = reverse('api:comment-detail', args=[self.comment.id])

    def test_list_comments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_comment(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comment.id)

    def test_create_comment(self):
        data = {
            "object_id": 2,
            "content_type_id": self.content_type.id,
            "author_id": self.author.id,
            "text": "Novo comentário criado via teste"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(Comment.objects.filter(id=response.data['id']).exists())

    def test_update_comment(self):
        data = {
            "object_id": 1,
            "content_type_id": self.content_type.id,
            "author_id": self.author.id,
            "text": "Comentário atualizado"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, "Comentário atualizado")

    def test_delete_comment(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
