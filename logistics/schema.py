import graphene
from graphene_django.types import DjangoObjectType
from .models import MaterialTypes, Materials, SolarEnergyKit, SalesMaterials, ProjectMaterials

class MaterialTypesType(DjangoObjectType):
    class Meta:
        model = MaterialTypes
        fields = "__all__"

class MaterialsType(DjangoObjectType):
    class Meta:
        model = Materials
        fields = "__all__"

class SolarEnergyKitType(DjangoObjectType):
    class Meta:
        model = SolarEnergyKit
        fields = "__all__"

class SalesMaterialsType(DjangoObjectType):
    class Meta:
        model = SalesMaterials
        fields = "__all__"

class ProjectMaterialsType(DjangoObjectType):
    class Meta:
        model = ProjectMaterials
        fields = "__all__"

class Query(graphene.ObjectType):
    material_types = graphene.List(MaterialTypesType)
    materials = graphene.List(MaterialsType)
    solar_energy_kits = graphene.List(SolarEnergyKitType)
    sales_materials = graphene.List(SalesMaterialsType)
    project_materials = graphene.List(ProjectMaterialsType)

    def resolve_material_types(self, info, **kwargs):
        return MaterialTypes.objects.all()

    def resolve_materials(self, info, **kwargs):
        return Materials.objects.all()

    def resolve_solar_energy_kits(self, info, **kwargs):
        return SolarEnergyKit.objects.all()

    def resolve_sales_materials(self, info, **kwargs):
        return SalesMaterials.objects.all()

    def resolve_project_materials(self, info, **kwargs):
        return ProjectMaterials.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
