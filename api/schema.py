import graphene


from accounts.schema import Query as QueryAccounts
from contracts.schema import Query as QueryContracts
from core.schema import Query as QueryCore
from engineering.schema import Query as QueryEngineering
from financial.schema import Query as QueryFinancial
from inspections.schema import Query as QueryInspections
from logistics.schema import Query as QueryLogistics
from resolve_crm.schema import Query as QueryCrm


class Query(QueryAccounts, QueryContracts, QueryCore, QueryEngineering, QueryFinancial, QueryInspections, QueryLogistics, QueryCrm, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)