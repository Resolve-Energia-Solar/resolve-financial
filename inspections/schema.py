import graphene
from graphene_django.types import DjangoObjectType
from .models import RoofType

class RoofTypeType(DjangoObjectType):
    class Meta:
        model = RoofType
        fields = "__all__"

class Query(graphene.ObjectType):
    roof_types = graphene.List(RoofTypeType)

    def resolve_roof_types(self, info, **kwargs):
        return RoofType.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
