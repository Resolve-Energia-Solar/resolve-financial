# Adicione as importações necessárias
import graphene
from graphene_django import DjangoObjectType
from .models import DocumentType

class DocumentTypeType(DjangoObjectType):
    class Meta:
        model = DocumentType
        fields = "__all__"  # Inclui todos os campos do modelo

class Query(graphene.ObjectType):
    document_types = graphene.List(DocumentTypeType)

    def resolve_document_types(self, info, **kwargs):
        return DocumentType.objects.all()

schema = graphene.Schema(query=Query)
