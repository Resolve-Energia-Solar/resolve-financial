from core.models import Attachment
from engineering.models import CivilConstruction, RequestsEnergyCompany, ResquestType, Units
from field_services.models import Schedule
from django.contrib.contenttypes.models import ContentType
from django.db import models as django_models  # Adicione esta linha
from django.db.models import (
    Case,
    When,
    Value,
    CharField,
    Q,
    BooleanField,
    Exists,
    OuterRef,
    Subquery,
    Aggregate,
    DateField,
    ExpressionWrapper,
    F,
    Max,
    Sum,
    DecimalField,
    Count,
    IntegerField,
    DurationField,
    Func,
    Avg,
    DateTimeField,
    FilteredRelation,
    Prefetch,
    Min,
)
from django.db.models.functions import Cast, Coalesce
import operator
from functools import reduce
from django.utils import timezone
from datetime import timedelta

class TimestampDiff(Func):
    function = "TIMESTAMPDIFF"
    template = "%(function)s(DAY, %(expressions)s)"
    output_field = IntegerField()


class GroupConcat(Aggregate):
    function = "GROUP_CONCAT"
    template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR '%(separator)s')"
    allow_distinct = True

    def __init__(self, expression, distinct=False, separator=", ", **extra):
        super().__init__(
            expression,
            distinct="DISTINCT " if distinct else "",
            separator=separator,
            output_field=CharField(),
            **extra,
        )


class ProjectQuerySet(django_models.QuerySet):
    
    def with_journey_counter(self):
        return self.annotate(
            last_final=Subquery(
                RequestsEnergyCompany.objects.filter(
                    project=OuterRef('pk'),
                    type__name__icontains="Vistoria final",
                    status="D",
                    conclusion_date__isnull=False
                )
                .order_by('-conclusion_date')
                .values('conclusion_date')[:1],
                output_field=DateField()
            ),
            contract_dt=Cast(F("sale__signature_date"), DateField())
        ).annotate(
            journey_end=Coalesce(
                F("last_final"),
                Value(timezone.localdate()),
                output_field=DateField()
            )
        ).annotate(
            journey_counter=Func(
                F('journey_end'),  # Data final
                F('contract_dt'),  # Data inicial
                function='DATEDIFF',
                template='%(function)s(%(expressions)s)',
                output_field=IntegerField()
            )
        )

    def with_is_released_to_engineering(self):
        from resolve_crm import models as resolve_models
        sale_ct = ContentType.objects.get_for_model(resolve_models.Sale)

        has_contract = Exists(
            Attachment.objects.filter(
                content_type=sale_ct,
                object_id=OuterRef("sale_id"),
                status="A",
                document_type__name__icontains="Contrato",
            ).values("id")
        )

        # Subconsulta para verificar se há CNH ou RG do homologador
        has_cnh_or_rg_homologador = Exists(
            Attachment.objects.filter(
                content_type=sale_ct, object_id=OuterRef("sale_id"), status="A"
            )
            .filter(
                Q(document_type__name__icontains="CNH")
                | Q(document_type__name__icontains="RG"),
                document_type__name__icontains="homologador",
            )
            .values("id")
        )

        # Restante das subconsultas
        has_unit_with_bill_file = Exists(
            Units.objects.filter(
                project=OuterRef("pk"), bill_file__isnull=False
            ).values(
                "id"
            )  # Limita a subconsulta para retornar apenas 'id'
        )

        has_new_contract_uc = Exists(
            Units.objects.filter(
                project=OuterRef("pk"), new_contract_number=True
            ).values(
                "id"
            )  # Limita a subconsulta para retornar apenas 'id'
        )

        return self.annotate(
            is_released_to_engineering=Case(
                When(
                    Q(sale__payment_status__in=["L", "C", "CO"])
                    & Q(inspection__final_service_opinion__name__icontains="Aprovad")
                    & Q(sale__is_pre_sale=False)
                    & ~Q(status__in=["C", "D"])
                    & Q(sale__status__in=["EA", "F"])
                    & has_contract
                    & has_cnh_or_rg_homologador
                    & (has_unit_with_bill_file | has_new_contract_uc),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        )


    def with_trt_status(self):
        from core.models import Attachment
        from django.contrib.contenttypes.models import ContentType
        from resolve_crm import models as resolve_models

        project_content_type = ContentType.objects.get_for_model(resolve_models.Project)

        return self.annotate(
            trt_status=Subquery(
                Attachment.objects.filter(
                    object_id=OuterRef("pk"),
                    content_type=project_content_type,
                    document_type__name="ART/TRT",
                )
                .order_by("-created_at")
                .values("status")[:1],
                output_field=CharField(),
            )
        ).distinct()


    def with_pending_material_list(self):
        return (
            self.with_is_released_to_engineering()
            .annotate(
                pending_material_list=Case(
                    When(
                        Q(is_released_to_engineering=True)
                        & Q(material_list_is_completed=False),
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        )


    def with_access_opnion(self):
        return (
            self.with_trt_status()
            .with_is_released_to_engineering()
            .annotate(
                access_opnion=Case(
                    When(
                        Q(trt_status="A")
                        & Q(units__new_contract_number=False)
                        & Q(is_released_to_engineering=True),
                        then=Value("Liberado"),
                    ),
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                )
            )
        ).distinct()


    def with_trt_pending(self):
        return (
            self.with_is_released_to_engineering()
            .with_trt_status()
            .annotate(
                trt_pending=Case(
                    When(Q(is_released_to_engineering=False), then=Value("Bloqueado")),
                    When(
                        Q(trt_status="R") & ~Q(trt_status="A"), then=Value("Reprovada")
                    ),
                    When(
                        Q(trt_status="EA") & ~Q(trt_status="A"),
                        then=Value("Em Andamento"),
                    ),
                    When(Q(trt_status="A"), then=Value("Concluída")),
                    default=Value("Pendente"),
                    output_field=CharField(),
                )
            )
        )


    def with_request_requested(self):
        return self.annotate(
            request_requested=Case(
                When(Q(requests_energy_company__isnull=False), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )


    def with_last_installation_final_service_opinion(self):
        return self.annotate(
            last_installation_final_service_opinion=Subquery(
                Schedule.objects.filter(
                    project=OuterRef("pk"),
                    service__category__name__icontains="Instalação",
                )
                .order_by("-created_at")
                .values("final_service_opinion__name")[:1],
                output_field=CharField(),
            )
        )


    def with_request_days_since_requested(self, type_name: str, annotation_name: str):
        base_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"), type__name__icontains=type_name
        ).order_by("-request_date")

        request_date_subquery = base_qs.values("request_date")[:1]
        conclusion_date_subquery = base_qs.values("conclusion_date")[:1]

        return self.annotate(
            **{
                f"{annotation_name}_int": TimestampDiff(
                    Subquery(request_date_subquery),
                    Coalesce(Subquery(conclusion_date_subquery), Func(function="NOW")),
                )
            }
        ).distinct()


    def with_supply_adquance_names(self):
        subquery = Units.objects.filter(
            project=OuterRef("pk"), main_unit=True, supply_adquance__isnull=False
        ).values_list("supply_adquance__name", flat=True)

        return self.annotate(
            supply_adquance_names=Coalesce(
                Subquery(
                    Units.objects.filter(
                        project=OuterRef("pk"),
                        main_unit=True,
                        supply_adquance__isnull=False,
                    )
                    .order_by()
                    .annotate(names_concat=GroupConcat("supply_adquance__name"))
                    .values("names_concat")[:1]
                ),
                Value(""),
            )
        ).distinct()


    def with_homologation_status(self):
        # 1) busca os RequestType relevantes e agrupa seus IDs por categoria
        request_types = ResquestType.objects.filter(
            Q(name__icontains="Parecer de Acesso") |
            Q(name__icontains="Aumento de Carga") |
            Q(name__icontains="Ajuste de Ramal") |
            Q(name__icontains="Nova UC") |
            Q(name__icontains="Vistoria Final")
        )
        type_ids = {
            "Parecer de Acesso": [],
            "Aumento de Carga": [],
            "Ajuste de Ramal": [],
            "Nova UC": [],
            "Vistoria Final": []
        }
        for rt in request_types:
            lower = rt.name.lower()
            if "parecer de acesso" in lower:
                type_ids["Parecer de Acesso"].append(rt.id)
            if "aumento de carga" in lower:
                type_ids["Aumento de Carga"].append(rt.id)
            if "ajuste de ramal" in lower:
                type_ids["Ajuste de Ramal"].append(rt.id)
            if "nova uc" in lower:
                type_ids["Nova UC"].append(rt.id)
            if "vistoria final" in lower:
                type_ids["Vistoria Final"].append(rt.id)

        # 2) subquery para detectar se há Unidade principal com novo contrato
        main_unit_has_new_contract = Units.objects.filter(
            project=OuterRef("pk"),
            main_unit=True,
            new_contract_number=True
        )

        # 3) para cada categoria de pedido, crio um Subquery que retorna o status
        #    e um Exists() que apenas verifica existência
        access_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Parecer de Acesso"]
        ).order_by().values("status")[:1]
        access_exists = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Parecer de Acesso"]
        )

        load_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Aumento de Carga"]
        ).order_by().values("status")[:1]
        load_exists = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Aumento de Carga"]
        )

        branch_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Ajuste de Ramal"]
        ).order_by().values("status")[:1]
        branch_exists = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Ajuste de Ramal"]
        )

        newuc_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Nova UC"]
        ).order_by().values("status")[:1]
        newuc_exists = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Nova UC"]
        )

        final_qs = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Vistoria Final"]
        ).order_by().values("status")[:1]
        final_exists = RequestsEnergyCompany.objects.filter(
            project=OuterRef("pk"),
            type_id__in=type_ids["Vistoria Final"]
        )

        return (
            self
            .with_is_released_to_engineering()
            .with_last_installation_final_service_opinion()
            .with_supply_adquance_names()
            .with_request_days_since_requested("Parecer de Acesso", "access_opnion_days")
            .with_request_days_since_requested("Aumento de Carga", "load_increase_days")
            .with_request_days_since_requested("Ajuste de Ramal", "branch_adjustment_days")
            .with_request_days_since_requested("Nova UC", "new_contact_number_days")
            .with_request_days_since_requested("Vistoria Final", "final_inspection_days")
            .annotate(
                access_req_status=Subquery(access_qs, output_field=CharField()),
                access_req_exists=Exists(access_exists),

                load_req_status=Subquery(load_qs, output_field=CharField()),
                load_req_exists=Exists(load_exists),

                branch_req_status=Subquery(branch_qs, output_field=CharField()),
                branch_req_exists=Exists(branch_exists),

                newuc_req_status=Subquery(newuc_qs, output_field=CharField()),
                newuc_req_exists=Exists(newuc_exists),

                final_req_status=Subquery(final_qs, output_field=CharField()),
                final_req_exists=Exists(final_exists),

                has_main_unit_new_contract=Exists(main_unit_has_new_contract),
            )
            .annotate(
                all_pre_reqs_deferred_or_not_applicable=Case(
                    When(
                        (
                            (
                                Q(has_main_unit_new_contract=True)
                                & Q(newuc_req_status="D")
                            )
                            | Q(has_main_unit_new_contract=False)
                        )
                        &
                        (
                            ~Q(supply_adquance_names__icontains="Aumento de Carga")
                            | Q(load_req_status="D")
                        )
                        &
                        (
                            ~Q(supply_adquance_names__icontains="Ajuste de Ramal")
                            | Q(branch_req_status="D")
                        )
                        &
                        Q(access_req_status="D")
                        &
                        Q(last_installation_final_service_opinion__icontains="Concluído"),
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                ),

                access_opnion_status=Case(
                    When(is_released_to_engineering=False, then=Value("Bloqueado")),
                    When(access_req_exists=False, then=Value("Pendente")),
                    When(access_req_status="S",    then=Value("Solicitado")),
                    When(access_req_status="D",    then=Value("Deferido")),
                    When(access_req_status="I",    then=Value("Indeferida")),
                    When(access_req_status="ID",   then=Value("Indeferida Debito")),
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                ),

                load_increase_status=Case(
                    When(~Q(supply_adquance_names__icontains="Aumento de Carga"), then=Value("Não se aplica")),
                    When(load_req_exists=False, last_installation_final_service_opinion__icontains="Concluído", then=Value("Pendente")),
                    When(load_req_status="S", then=Value("Solicitado")),
                    When(load_req_status="D", then=Value("Deferido")),
                    When(load_req_status="I", then=Value("Indeferida")),
                    When(load_req_status="ID", then=Value("Indeferida Debito")),
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                ),

                branch_adjustment_status=Case(
                    When(~Q(supply_adquance_names__icontains="Ajuste de Ramal"), then=Value("Não se aplica")),
                    When(branch_req_exists=False, last_installation_final_service_opinion__icontains="Concluído", then=Value("Pendente")),
                    When(branch_req_status="S", then=Value("Solicitado")),
                    When(branch_req_status="D", then=Value("Deferido")),
                    When(branch_req_status="I", then=Value("Indeferida")),
                    When(branch_req_status="ID", then=Value("Indeferida Debito")),
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                ),

                new_contact_number_status=Case(
                    When(has_main_unit_new_contract=False, then=Value("Não se aplica")),
                    When(
                        has_main_unit_new_contract=True,
                        then=Case(
                            When(is_released_to_engineering=False, then=Value("Bloqueado")),
                            When(~Q(designer_status="CO"), then=Value("Bloqueado")),
                            When(newuc_req_exists=False, then=Value("Pendente")),
                            When(newuc_req_status="S", then=Value("Solicitado")),
                            When(newuc_req_status="D", then=Value("Deferido")),
                            When(newuc_req_status="I", then=Value("Indeferida")),
                            When(newuc_req_status="ID", then=Value("Indeferida Debito")),
                            default=Value("Bloqueado"),
                        )
                    ),
                    output_field=CharField(),
                ),

                final_inspection_status=Case(
                    When(is_released_to_engineering=False, then=Value("Bloqueado")),

                    When(all_pre_reqs_deferred_or_not_applicable=False, then=Value("Bloqueado")),

                    When(final_req_exists=False, last_installation_final_service_opinion__icontains="Concluído", then=Value("Pendente")),
                    When(final_req_status="S",    then=Value("Solicitado")),
                    When(final_req_status="D",    then=Value("Deferido")),
                    When(final_req_status="I",    then=Value("Indeferida")),
                    When(final_req_status="ID",   then=Value("Indeferida Debito")),

                    default=Value("Bloqueado"),
                    output_field=CharField(),
                ),
            )
        )




    def with_final_inspection_status(self):
        # Mover para constante global (definida no topo do arquivo)
        VISTORIA_FINAL_IDS = ResquestType.objects.filter(
            name__icontains="Vistoria Final"
        ).values_list('id', flat=True)
        return self.with_is_released_to_engineering().with_last_installation_final_service_opinion().annotate(
        
            final_req_exists=Exists(
                RequestsEnergyCompany.objects.filter(
                    project=OuterRef('pk'),
                    type_id__in=VISTORIA_FINAL_IDS
                )
            ),
            final_req_status=Subquery(
                RequestsEnergyCompany.objects.filter(
                    project=OuterRef('pk'),
                    type_id__in=VISTORIA_FINAL_IDS
                ).order_by('-id')[:1].values('status')
            )
        ).annotate(
            
            final_inspection_status=Case(
                When(
                    Q(is_released_to_engineering=False), then=Value("Bloqueado")
                ),
                When(
                    Q(final_req_exists=False) &
                    Q(last_installation_final_service_opinion__icontains='Concluído'),
                    then=Value("Pendente")
                ),
                When(final_req_status="S", then=Value("Solicitado")),
                When(final_req_status="D", then=Value("Deferido")),
                When(final_req_status="I", then=Value("Indeferida")),
                When(final_req_status="ID", then=Value("Indeferida Debito")),
                default=Value("Bloqueado"),
                output_field=CharField(),
            )
        )
    
    
    def with_purchase_status(self):
        return (
            self.with_is_released_to_engineering()
            .annotate(
                purchase_status=Case(
                    When(Q(is_released_to_engineering=False), then=Value("Bloqueado")),
                    When(Q(purchases__isnull=True), then=Value("Liberado")),
                    When(Q(purchases__status="P"), then=Value("Pendente")),
                    When(Q(purchases__status="R"), then=Value("Compra Realizada")),
                    When(Q(purchases__status="C"), then=Value("Cancelado")),
                    When(Q(purchases__status="D"), then=Value("Distrato")),
                    When(
                        Q(purchases__status="F"),
                        then=Value("Aguardando Previsão de Entrega"),
                    ),
                    When(Q(purchases__status="A"), then=Value("Aguardando Pagamento")),
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                )
            )
        )


    def with_expected_delivery_date(self):
        return self.annotate(
            expected_delivery_date=Case(
                When(
                    sale__signature_date__isnull=False,
                    then=Cast(
                        ExpressionWrapper(
                            F("sale__signature_date") + timedelta(days=20),
                            output_field=DateField(),
                        ),
                        output_field=DateField(),
                    ),
                ),
                default=None,
                output_field=DateField(),
            ),
            expected_delivery_status=Case(
                When(sale__signature_date__isnull=True, then=Value("Sem contrato")),
                default=Value("Com contrato"),
                output_field=CharField(),
            ),
        )


    def with_delivery_status(self):
        from django.db.models import Exists, OuterRef, Subquery
        
        # Subquery para o último parecer de entrega
        delivery_schedules = Schedule.objects.filter(
            service__name__icontains="Entrega"
        ).filter(project=OuterRef('pk'))
        
        return (
            self.with_is_released_to_engineering().annotate(
            has_delivery=Exists(delivery_schedules),
            last_delivery_opinion_name=Subquery(
                delivery_schedules.order_by('-created_at')
                .values('final_service_opinion__name')[:1]
                ),
                delivery_status=Case(
                    # Condições de Bloqueado
                    When(Q(is_released_to_engineering=False), then=Value("Bloqueado")),
                    When(Q(purchases__isnull=True), then=Value("Bloqueado")),
                    When(
                        Q(purchases__isnull=False) &
                        Q(delivery_type="D") & 
                        ~Q(purchases__status="R"),
                        then=Value("Bloqueado")
                    ),
                    When(
                        Q(purchases__isnull=False) &
                        Q(delivery_type="C") & 
                        Q(purchases__status="R") &
                        ~Q(designer_status__in=["CO"]) &
                        ~Q(material_list_is_completed=True),
                        then=Value("Bloqueado")
                    ),
                    # Condições de Liberado
                    When(
                        Q(purchases__isnull=False) &
                        Q(delivery_type="D") & 
                        Q(purchases__status="R") &
                        ~Q(has_delivery=True),  # Usando a annotation has_delivery
                        then=Value("Liberado")
                    ),
                    When(
                        Q(purchases__isnull=False) &
                        Q(delivery_type="C") & 
                        Q(purchases__status="R") &
                        Q(designer_status__in=["CO"]) &
                        Q(material_list_is_completed=True) &
                        ~Q(has_delivery=True),  # Usando a annotation has_delivery
                        then=Value("Liberado")
                    ),
                    # Outros status
                    When(
                        Q(has_delivery=True) &  # Usando a annotation has_delivery
                        Q(last_delivery_opinion_name__isnull=True),
                        then=Value("Agendado")
                    ),
                    When(
                        Q(last_delivery_opinion_name__icontains="Entregue"),
                        then=Value("Entregue")
                    ),
                    When(
                        Q(last_delivery_opinion_name__icontains="Cancelado"),
                        then=Value("Cancelado")
                    ),
                    # Caso padrão
                    default=Value("Bloqueado"),
                    output_field=CharField(),
                )
            )
        )

        
    def with_is_released_to_installation(self):
        """Annotates whether the project is released for installation based on:
        - Engineering release status
        - Delivery status
        - Construction needs (inspection approval)
        - Construction completion status
        """
        # Constants for service categories and opinions
        INSPECTION_CATEGORY = "Vistoria"
        APPROVED_OPINION = "Aprovad"
        CONSTRUCTION_OPINIONS = ["Obra", "Sombreamento"]
        FINISHED_CONSTRUCTION_STATUS = "F"

        return (
            self.with_is_released_to_engineering()
            .with_delivery_status()
            .annotate(
                # Check if there's an approved inspection requiring construction
                has_construction_need=Exists(
                    Schedule.objects.filter(
                        project=OuterRef("pk"),
                        service__category__name__icontains=INSPECTION_CATEGORY,
                        final_service_opinion__name__icontains=APPROVED_OPINION,
                    ).filter(
                        reduce(
                            operator.or_,
                            [
                                Q(final_service_opinion__name__icontains=opinion)
                                for opinion in CONSTRUCTION_OPINIONS
                            ]
                        )
                    ).values("id")
                ),
                # Check if there's a finished construction
                has_finished_construction=Exists(
                    CivilConstruction.objects.filter(
                        project=OuterRef("pk"), 
                        status=FINISHED_CONSTRUCTION_STATUS
                    ).values("id")
                )
            )
            .annotate(
                is_released_to_installation=Case(
                    When(
                        Q(is_released_to_engineering=True) &
                        Q(delivery_status="Entregue") &
                        (
                            ~Q(has_construction_need=True) |
                            (Q(has_construction_need=True) & Q(has_finished_construction=True))
                        ),
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        )


    def _annotate_installation_related_fields(self, queryset):
        INSTALLATION_CATEGORY = "Instalação"
        INSPECTION_CATEGORY = "Vistoria"

        installation_schedules = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__category__name__icontains=INSTALLATION_CATEGORY
        )

        inspection_schedules = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__category__name__icontains=INSPECTION_CATEGORY,
            final_service_opinion__name__icontains="Aprovad"
        ).filter(
            Q(final_service_opinion__name__icontains="Obra") |
            Q(final_service_opinion__name__icontains="Sombreamento")
        )

        return queryset.annotate(
            latest_installation_opinion_name=Subquery(
                installation_schedules.order_by("-created_at")
                .values("final_service_opinion__name")[:1]
            ),
            has_installation=Exists(installation_schedules),
            has_construction_schedule=Exists(inspection_schedules),
            latest_construction_status=Coalesce(
                Subquery(
                    CivilConstruction.objects.filter(project=OuterRef("pk"))
                    .order_by("-id")
                    .values("status")[:1]
                ),
                Value("P")
            )
        )


    def with_installation_status(self):
        """Determines the installation status of projects based on multiple criteria"""
        # Status constants
        STATUS_PRE_SALE = "Pré-Venda"
        STATUS_CANCELED_SALE = "Venda Cancelada ou Distrato"
        STATUS_INSTALLED = "Instalado"
        STATUS_CANCELED = "Cancelado"
        STATUS_SCHEDULED = "Agendado"
        STATUS_UNDER_CONSTRUCTION = "Em obra"
        STATUS_BLOCKED = "Bloqueado"
        STATUS_RELEASED = "Liberado"

        # First get all necessary annotations
        queryset = self.with_is_released_to_installation()
        queryset = self._annotate_installation_related_fields(queryset)

        return queryset.annotate(
            installation_status=Case(
                # 0) Check pre-sale and canceled sale status first
                When(Q(sale__is_pre_sale=True), then=Value(STATUS_PRE_SALE)),
                When(
                    Q(sale__status__in=["C", "D"]),
                    then=Value(STATUS_CANCELED_SALE),
                ),
                # 1) Installed or canceled
                When(
                    Q(latest_installation_opinion_name__icontains="Concluído"),
                    then=Value(STATUS_INSTALLED),
                ),
                When(
                    Q(latest_installation_opinion_name__icontains="Cancelada"),
                    then=Value(STATUS_CANCELED),
                ),
                # 2) Scheduled: has installation but no final opinion yet
                When(
                    Q(has_installation=True) & Q(latest_installation_opinion_name__isnull=True),
                    then=Value(STATUS_SCHEDULED),
                ),
                # 3) Under construction: needs construction and not finished
                When(
                    Q(has_construction_schedule=True) & ~Q(latest_construction_status="F"),
                    then=Value(STATUS_UNDER_CONSTRUCTION),
                ),
                # 4) Not released for installation → blocked
                When(Q(is_released_to_installation=False), then=Value(STATUS_BLOCKED)),
                # 5) Released: ready for installation
                When(Q(is_released_to_installation=True), then=Value(STATUS_RELEASED)),
                default=Value(STATUS_BLOCKED),
                output_field=CharField(),
            )
        )


    def with_latest_installation(self):
        return self.annotate(
            latest_installation=Subquery(
                Schedule.objects.filter(
                    project=OuterRef("pk"),
                    service__category__name__icontains="Instalação",
                )
                .order_by("-created_at")
                .values("id")[:1]
            )
        )


    def with_installments_indicators(self):
        now = timezone.now()

        return self.annotate(
            overdue_installments_count=Count(
                "sale__payments__installments",
                filter=Q(
                    sale__payments__installments__is_paid=False,
                    sale__payments__installments__due_date__lte=now,
                ),
                distinct=True,
            ),
            overdue_installments_value=Coalesce(
                Sum(
                    "sale__payments__installments__installment_value",
                    filter=Q(
                        sale__payments__installments__is_paid=False,
                        sale__payments__installments__due_date__lte=now,
                    ),
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
            on_time_installments_count=Count(
                "sale__payments__installments",
                filter=Q(
                    sale__payments__installments__is_paid=False,
                    sale__payments__installments__due_date__gt=now,
                ),
                distinct=True,
            ),
            on_time_installments_value=Coalesce(
                Sum(
                    "sale__payments__installments__installment_value",
                    filter=Q(
                        sale__payments__installments__is_paid=False,
                        sale__payments__installments__due_date__gt=now,
                    ),
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
            paid_installments_count=Count(
                "sale__payments__installments",
                filter=Q(sale__payments__installments__is_paid=True),
                distinct=True,
            ),
            paid_installments_value=Coalesce(
                Sum(
                    "sale__payments__installments__installment_value",
                    filter=Q(sale__payments__installments__is_paid=True),
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
            total_installments=Count("sale__payments__installments", distinct=True),
            total_installments_value=Coalesce(
                Sum(
                    "sale__payments__installments__installment_value",
                    output_field=DecimalField(),
                ),
                Value(0),
            ),
        )


    def with_construction_status(self):
        return self.annotate(
            # Determine if the project needs construction
            # (if there's a schedule with an approved inspection that mentions construction or shading)
            needs_construction=Exists(
                Schedule.objects.filter(
                    project=OuterRef("pk"),
                    service__category__name__icontains="Vistoria",
                    final_service_opinion__name__icontains="Aprovad",
                )
                .filter(
                    Q(final_service_opinion__name__icontains="Obra")
                    | Q(final_service_opinion__name__icontains="Sombreamento")
                )
                .values("id")
            ),
            # Check if there's any civil construction associated with the project
            has_construction=Exists(
                CivilConstruction.objects.filter(project=OuterRef("pk"))
            ),
            # Return the status based on the conditions:
            # - If has construction, return the status of the latest construction
            # - If needs construction but has no construction, return empty string
            # - If doesn't need construction, return "Não se aplica"
            construction_status=Case(
                When(
                    Q(has_construction=True),
                    then=Subquery(
                        CivilConstruction.objects.filter(project=OuterRef("pk"))
                        .order_by("-id")
                        .values("status")[:1]
                    ),
                ),
                When(
                    Q(needs_construction=True) & Q(has_construction=False),
                    then=Value("S"),
                ),
                default=Value("NA"),
                output_field=CharField(),
            ),
        ).distinct()

    
    def with_ticket_stats(self):
        return self.annotate(
            total_tickets=Count(
                "project_tickets",
                distinct=True
            ),
            total_tickets_abertos=Count(
                "project_tickets",
                filter=~Q(project_tickets__status__in=["R", "F"]),
                distinct=True
            ),
            avg_tempo_resolucao=Avg(
                ExpressionWrapper(
                    F("project_tickets__conclusion_date") - F("project_tickets__created_at"),
                    output_field=DurationField(),
                ),
                filter=Q(project_tickets__status__in=["R", "F"])
            ),
            ticket_aberto_mais_antigo=Min(
                "project_tickets__created_at",
                filter=~Q(project_tickets__status__in=["R", "F"])
            ),
        )
    

    def with_status_annotations(self):
        return (
            self
            # default
            .with_is_released_to_engineering()
            .with_pending_material_list()
            # Homologation
            .with_access_opnion()
            .with_request_requested()
            .with_last_installation_final_service_opinion()
            .with_supply_adquance_names()
            .with_trt_pending()
            # Logistics
            .with_delivery_status()
            .with_purchase_status()
            .with_expected_delivery_date()
            # Installation
            .with_is_released_to_installation()
            .with_installation_status()
            # Construction
            .with_construction_status()
            .with_in_construction()
        )


    def with_avg_time_installation(self):
        entrega_finished_at_subquery = (
            Schedule.objects.filter(
                project=OuterRef("pk"),
                service__name__icontains="entrega",
                execution_finished_at__isnull=False,
            )
            .order_by("-execution_finished_at")
            .values("execution_finished_at")[:1]
        )

        installation_schedules = (
            Schedule.objects.filter(
                project=OuterRef("pk"),
                service__name__icontains="instalação",
                execution_started_at__isnull=False,
                execution_finished_at__isnull=False,
            )
            .annotate(
                entrega_finished_at=Subquery(
                    entrega_finished_at_subquery, output_field=DateTimeField()
                )
            )
            .annotate(
                duration=ExpressionWrapper(
                    F("execution_finished_at") - F("entrega_finished_at"),
                    output_field=DurationField(),
                )
            )
            .values("project")
            .annotate(avg_duration=Avg("duration"))
            .values("avg_duration")[:1]
        )

        return self.annotate(
            avg_time_installation=Subquery(
                installation_schedules, output_field=DurationField()
            )
        )


    def with_customer_released_flag(self):
        inspection_done = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__name__icontains="vistoria",
            agent_status="C",
        )

        delivery_done = Schedule.objects.filter(
            project=OuterRef("pk"),
            service__name__icontains="entrega",
            agent_status="C",
        )

        return self.annotate(
            customer_released=Exists(inspection_done) & Exists(delivery_done)
        )


    def with_number_of_installations(self):
        return self.annotate(
            number_of_installations=Count(
                "field_services",
                filter=Q(
                    field_services__service__name__icontains="instalação",
                    field_services__execution_finished_at__isnull=False,
                    field_services__schedule_date__isnull=False,
                ),
                distinct=True,
            )
        )


    def with_in_construction(self):
        return self.annotate(
            in_construction=Exists(
                Schedule.objects.filter(
                    project=OuterRef("pk"),
                    service__category__name__icontains="Vistoria",
                )
                .filter(
                    Q(final_service_opinion__name__icontains="Aprovad")
                    & (
                        Q(final_service_opinion__name__icontains="Obra")
                        | Q(final_service_opinion__name__icontains="Sombreamento")
                    )
                )
                .values("id")
            )
        )

