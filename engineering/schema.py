import graphene
from graphene_django.types import DjangoObjectType
from .models import EnergyCompany, RequestsEnergyCompany, CircuitBreaker, Units

class EnergyCompanyType(DjangoObjectType):
    class Meta:
        model = EnergyCompany
        fields = "__all__"

class RequestsEnergyCompanyType(DjangoObjectType):
    class Meta:
        model = RequestsEnergyCompany
        fields = "__all__"

class CircuitBreakerType(DjangoObjectType):
    class Meta:
        model = CircuitBreaker
        fields = "__all__"

class UnitsType(DjangoObjectType):
    class Meta:
        model = Units
        fields = "__all__"

class Query(graphene.ObjectType):
    energy_companies = graphene.List(EnergyCompanyType)
    requests_energy_companies = graphene.List(RequestsEnergyCompanyType)
    circuit_breakers = graphene.List(CircuitBreakerType)
    units = graphene.List(UnitsType)

    def resolve_energy_companies(self, info, **kwargs):
        return EnergyCompany.objects.all()

    def resolve_requests_energy_companies(self, info, **kwargs):
        return RequestsEnergyCompany.objects.all()

    def resolve_circuit_breakers(self, info, **kwargs):
        return CircuitBreaker.objects.all()

    def resolve_units(self, info, **kwargs):
        return Units.objects.all()

# Crie o schema com a query definida
schema = graphene.Schema(query=Query)
