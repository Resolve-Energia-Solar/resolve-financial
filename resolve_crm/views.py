import re
import logging
from datetime import datetime
from django.shortcuts import redirect
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import formats
from rest_framework import status
from rest_framework.views import APIView
from weasyprint import HTML
from rest_framework.pagination import PageNumberPagination
from accounts.models import User, UserType
from accounts.serializers import PhoneNumberSerializer, UserSerializer
from api.views import BaseModelViewSet
from engineering.models import Units
from financial.models import PaymentInstallment
from logistics.models import Product, ProductMaterials, SaleProduct
from logistics.serializers import ProductSerializer
from resolve_crm.task import save_all_sales
from .models import *
from .serializers import *
from django.db.models import Count, Q, Sum, Prefetch
from django.db.models import Exists, OuterRef, Q, F, DecimalField
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from hashlib import md5
from rest_framework.decorators import api_view
from django.contrib.contenttypes.models import ContentType
from core.task import create_process_async
from core.models import ProcessBase, Process
from .serializers import *
from .models import *
from django.utils import timezone


logger = logging.getLogger(__name__)

sale_content_type = ContentType.objects.get_for_model(Sale)
project_content_type = ContentType.objects.get_for_model(Project)


class OriginViewSet(BaseModelViewSet):
    queryset = Origin.objects.all()
    serializer_class = OriginSerializer


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_fields = '__all__'


class LeadTaskViewSet(BaseModelViewSet): 
    queryset = Task.objects.all()
    serializer_class = LeadTaskSerializer


class MarketingCampaignViewSet(BaseModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer


class ComercialProposalViewSet(BaseModelViewSet):
    queryset = ComercialProposal.objects.all()
    serializer_class = ComercialProposalSerializer


class SaleViewSet(BaseModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def get_queryset(self):
        user = self.request.user
        
        qs = Sale.objects.select_related(
            "customer", "seller", "sales_supervisor", "sales_manager",
            "branch", "marketing_campaign", "supplier"
        ).prefetch_related(
            "cancellation_reasons",
            "products",
            "attachments",
            "tags",
            "payments",
            "contract_submissions",
            Prefetch(
                "projects",
                queryset=Project.objects
                    .with_is_released_to_engineering()
                    .prefetch_related(
                        "units",
                        "inspection__final_service_opinion",
                        "homologator",
                    )
            ),
            Prefetch(
                "attachments",
                queryset=Attachment.objects.filter(
                    content_type=sale_content_type,
                    status="EA"
                ),
                to_attr="attachments_under_analysis"
            ),
        ).annotate(
            total_paid=Sum(
                'payments__installments__installment_value',
                filter=Q(payments__installments__is_paid=True),
                default=0
            )
        ).order_by('-created_at')


        if user.is_superuser or user.has_perm('resolve_crm.view_all_sales'):
            return qs

        stakeholder_filter = Q(customer=user) | Q(seller=user) | Q(sales_supervisor=user) | Q(sales_manager=user)

        if hasattr(user, 'employee') and user.employee.related_branches.exists():
            branch_ids = user.employee.related_branches.values_list('id', flat=True)
            return qs.filter(Q(branch__id__in=branch_ids) | stakeholder_filter).distinct()

        return qs.filter(stakeholder_filter)


    def apply_filters(self, queryset, query_params):
        if query_params.get('documents_under_analysis') == 'true':
            queryset = queryset.filter(attachments__document_type__required=True, attachments__status='EA')
        elif query_params.get('documents_under_analysis') == 'false':
            queryset = queryset.exclude(attachments__document_type__required=True, attachments__status='EA')

        if tag := query_params.get('tag_name__exact'):
            queryset = queryset.filter(tags__tag__exact=tag)

        if final_ops := query_params.get('final_service_options'):
            queryset = queryset.filter(projects__inspection__final_service_opinion__id__in=final_ops.split(','))

        if borrower := query_params.get('borrower__in'):
            queryset = queryset.filter(payments__borrower__id__in=borrower.split(','))

        if homologator := query_params.get('homologator'):
            queryset = queryset.filter(projects__homologator__id=homologator)

        if is_signed := query_params.get('is_signed'):
            if is_signed == 'true':
                queryset = queryset.filter(signature_date__isnull=False)
            elif is_signed == 'false':
                queryset = queryset.filter(signature_date__isnull=True)

        if invoice_status := query_params.get('invoice_status'):
            queryset = queryset.filter(payments__invoice_status__in=invoice_status.split(','))
            
        if query_params.get('payments_types__in'):
            queryset = queryset.filter(payments__payment_type__in=query_params.get('payments_types__in').split(','))

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.apply_filters(queryset, request.query_params)

        queryset = queryset.distinct()

        indicators = queryset.aggregate(
            pending_count=Count('id', filter=Q(status="P")),
            pending_total_value=Sum('total_value', filter=Q(status="P")),
            finalized_count=Count('id', filter=Q(status="F")),
            finalized_total_value=Sum('total_value', filter=Q(status="F")),
            in_progress_count=Count('id', filter=Q(status="EA")),
            in_progress_total_value=Sum('total_value', filter=Q(status="EA")),
            canceled_count=Count('id', filter=Q(status="C")),
            canceled_total_value=Sum('total_value', filter=Q(status="C")),
            terminated_count=Count('id', filter=Q(status="D")),
            terminated_total_value=Sum('total_value', filter=Q(status="D")),
            total_value_sum=Sum('total_value')
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            self.paginator.extra_meta = {"indicators": indicators}
            serialized_data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(serialized_data)

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response({'results': serialized_data, 'meta': {'indicators': indicators}})

    def get_documents_under_analysis(self, obj):
        documents = obj.documents_under_analysis[:10]
        from .serializers import AttachmentSerializer
        return AttachmentSerializer(documents, many=True).data
    

    @action(detail=True, methods=['post'])
    def create_process(self, request, pk=None):
        sale = self.get_object()

        if not sale.signature_date:
            return Response({"error": "Essa venda não tem data de assinatura."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            modelo = ProcessBase.objects.get(id=1)
        except ProcessBase.DoesNotExist:
            return Response({"error": "Modelo de processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        projects = Project.objects.filter(sale=sale)
        content_type = ContentType.objects.get_for_model(Project)

        existing_process_ids = set(
            Process.objects.filter(
                content_type=content_type,
                object_id__in=projects.values_list('id', flat=True)
            ).values_list('object_id', flat=True)
        )

        for project in projects:
            if project.id in existing_process_ids:
                continue

            create_process_async.delay(
                process_base_id=modelo.id,
                content_type_id=content_type.id,
                object_id=project.id,
                nome=f"Processo {modelo.name} {sale.contract_number} - {sale.customer.complete_name}",
                descricao=modelo.description,
                user_id=sale.customer.id if sale.customer else None,
                completion_date=sale.signature_date.isoformat()
            )

        return Response({"message": "Processos estão sendo criados."}, status=status.HTTP_202_ACCEPTED)
    
    
class ProjectViewSet(BaseModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        metrics = self.request.query_params.get('metrics')
        queryset = Project.objects.all()

        method_map = {
            'is_released_to_engineering': lambda qs: qs.with_is_released_to_engineering(),
            'trt_status': lambda qs: qs.with_trt_status(),
            'pending_material_list': lambda qs: qs.with_pending_material_list(),
            'access_opnion': lambda qs: qs.with_access_opnion(),
            'trt_pending': lambda qs: qs.with_trt_pending(),
            'request_requested': lambda qs: qs.with_request_requested(),
            'last_installation_final_service_opinion': lambda qs: qs.with_last_installation_final_service_opinion(),
            'supply_adquance_names': lambda qs: qs.with_supply_adquance_names(),
            'access_opnion_status': lambda qs: qs.with_access_opnion_status(),
            'load_increase_status': lambda qs: qs.with_load_increase_status(),
            'branch_adjustment_status': lambda qs: qs.with_branch_adjustment_status(),
            'new_contact_number_status': lambda qs: qs.with_new_contact_number_status(),
            'final_inspection_status': lambda qs: qs.with_final_inspection_status(),
            'purchase_status': lambda qs: qs.with_purchase_status(),
            'delivery_status': lambda qs: qs.with_delivery_status(),
            'expected_delivery_date': lambda qs: qs.with_expected_delivery_date(),
            'installments_indicators': lambda qs: qs.with_installments_indicators(),
            'all_status_annotations': lambda qs: qs.with_status_annotations(),
        }

        if metrics:
            for metric in metrics.split(','):
                metric = metric.strip()
                if metric in method_map:
                    queryset = method_map[metric](queryset)

        queryset = queryset.select_related(
            'sale',
            'inspection__final_service_opinion'
        ).prefetch_related(
            'attachments',
            'attachments__document_type',
            'units',
            'requests_energy_company',
            Prefetch(
                'units',
                queryset=Units.objects.filter(main_unit=True).select_related('address'),
                to_attr='main_unit_prefetched'
            ),
        )

        return queryset.order_by('-created_at').distinct()


    def apply_additional_filters(self, queryset, request):
        from django.db.models import Q, Exists, OuterRef
        from django.contrib.contenttypes.models import ContentType

        q = request.query_params.get('q')
        customer = request.query_params.get('customer')
        is_released_to_engineering = request.query_params.get('is_released_to_engineering')
        inspection_status = request.query_params.get('inspection_status')
        signature_date = request.query_params.get('signature_date')
        product_kwp = request.query_params.get('product_kwp')

        access_opnion = request.query_params.get('access_opnion')
        trt_status = request.query_params.get('trt_status')
        new_contract_number = request.query_params.get('new_contract_number')
        supply_adquance = request.query_params.get('supply_adquance')
        request_energy_company_type = request.query_params.get('request_energy_company_type__in')

        access_opnion_status = request.query_params.get('access_opnion_status')
        trt_pending = request.query_params.get('trt_pending')
        load_increase_status = request.query_params.get('load_increase_status')
        branch_adjustment_status = request.query_params.get('branch_adjustment_status')
        final_inspection_status = request.query_params.get('final_inspection_status')
        new_contact_number_status = request.query_params.get('new_contact_number_status')

        seller = request.query_params.get('seller')
        sale_status = request.query_params.get('sale_status')
        sale_branches = request.query_params.get('sale_branches')
        state = request.query_params.get('state')
        city = request.query_params.get('city')
        invoice_status = request.query_params.get('invoice_status')
        payment_types = request.query_params.get('payment_types')
        financiers = request.query_params.get('financiers')
        borrower = request.query_params.get('borrower')
        purchase_status = request.query_params.get('purchase_status')
        delivery_status = request.query_params.get('delivery_status')
        expected_delivery_date = request.query_params.get('expected_delivery_date__range')
        attachments_status = request.query_params.get('attachments_status')

        if attachments_status:
            queryset = queryset.filter(attachments__status__in=attachments_status.split(','))

        if 'purchase_status' in queryset.query.annotations and purchase_status:
            queryset = queryset.filter(purchase_status__in=purchase_status.split(','))

        if 'delivery_status' in queryset.query.annotations and delivery_status:
            queryset = queryset.filter(delivery_status__in=delivery_status.split(','))

        if 'expected_delivery_date' in queryset.query.annotations and expected_delivery_date:
            date_range = expected_delivery_date.split(',')
            if len(date_range) == 2:
                queryset = queryset.filter(expected_delivery_date__range=date_range)
            else:
                queryset = queryset.filter(expected_delivery_date=expected_delivery_date)

        if borrower:
            queryset = queryset.filter(sale__payments__borrower__id=borrower)
        if payment_types:
            queryset = queryset.filter(sale__payments__payment_type__in=payment_types.split(','))
        if financiers:
            queryset = queryset.filter(sale__payments__financier__id__in=financiers.split(','))
        if seller:
            queryset = queryset.filter(sale__seller__id=seller)
        if sale_status:
            queryset = queryset.filter(sale__status__in=sale_status.split(','))
        if sale_branches:
            queryset = queryset.filter(sale__branch__id__in=sale_branches.split(','))
        if invoice_status:
            queryset = queryset.filter(sale__payments__invoice_status__in=invoice_status.split(','))
        if state:
            queryset = queryset.filter(main_unit_prefetched__address__state__icontains=state)
        if city:
            queryset = queryset.filter(main_unit_prefetched__address__city__icontains=city)

        if request_energy_company_type:
            queryset = queryset.filter(requests_energy_company__id__in=request_energy_company_type.split(','))

        if q:
            queryset = queryset.filter(
                Q(sale__customer__complete_name__icontains=q) |
                Q(sale__customer__first_document__icontains=q) |
                Q(project_number__icontains=q)
            )

        if new_contract_number == 'true':
            queryset = queryset.filter(units__new_contract_number=True)
        elif new_contract_number == 'false':
            queryset = queryset.filter(units__new_contract_number=False)

        if supply_adquance:
            queryset = queryset.filter(units__supply_adquance__id__in=supply_adquance.split(','))

        if access_opnion == 'liberado':
            queryset = queryset.filter(access_opnion__icontains='Liberado')
        elif access_opnion == 'bloqueado':
            queryset = queryset.filter(access_opnion__icontains='Bloqueado')

        if trt_status:
            queryset = queryset.filter(trt_status__in=trt_status.split(','))

        if trt_pending:
            queryset = queryset.filter(trt_pending__iexact=trt_pending)

        if access_opnion_status:
            queryset = queryset.filter(access_opnion_status__icontains=access_opnion_status)
        if load_increase_status:
            queryset = queryset.filter(load_increase_status__icontains=load_increase_status)
        if branch_adjustment_status:
            queryset = queryset.filter(branch_adjustment_status__icontains=branch_adjustment_status)
        if final_inspection_status:
            queryset = queryset.filter(final_inspection_status__icontains=final_inspection_status)
        if new_contact_number_status:
            queryset = queryset.filter(new_contact_number_status__icontains=new_contact_number_status)

        if inspection_status:
            queryset = queryset.filter(inspection__final_service_opinion__id=inspection_status)

        if signature_date:
            date_range = signature_date.split(',')
            if len(date_range) == 2:
                queryset = queryset.filter(sale__signature_date__range=date_range)
            else:
                queryset = queryset.filter(sale__signature_date=signature_date)

        if product_kwp:
            try:
                product_kwp_value = float(product_kwp)
                queryset = queryset.filter(
                    product__params__gte=product_kwp_value - 2.5,
                    product__params__lte=product_kwp_value + 2.5
                )
            except ValueError:
                raise ValidationError({'product_kwp': 'Valor inválido para KWP.'})

        if is_released_to_engineering == 'true':
            queryset = queryset.filter(is_released_to_engineering=True)
        elif is_released_to_engineering == 'false':
            queryset = queryset.filter(is_released_to_engineering=False)

        if customer:
            queryset = queryset.filter(sale__customer__id=customer)

        current_step_in = request.query_params.get('current_step__in')
        if current_step_in:
            steps_list = current_step_in.split(',')
            project_ct = ContentType.objects.get_for_model(Project)
            queryset = queryset.annotate(
                has_current_step=Exists(
                    Process.objects.filter(
                        content_type=project_ct,
                        object_id=OuterRef('pk'),
                        current_step__id__in=steps_list
                    )
                )
            ).filter(has_current_step=True)

        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.apply_additional_filters(queryset, request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = self.get_serializer(page, many=True).data
            return self.get_paginated_response(serialized_data)

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data)


    @action(detail=False, methods=['get'])
    def indicators(self, request, *args, **kwargs):
        request.query_params._mutable = True
        request.query_params['metrics'] = 'is_released_to_engineering,trt_status,pending_material_list'
        request.query_params._mutable = False

        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.apply_additional_filters(queryset, request)

        raw_indicators = queryset.distinct().aggregate(
            designer_pending_count=Count('id', filter=Q(designer_status="P")),
            designer_in_progress_count=Count('id', filter=Q(designer_status="EA")),
            designer_complete_count=Count('id', filter=Q(designer_status="CO")),
            designer_canceled_count=Count('id', filter=Q(designer_status="C")),
            designer_termination_count=Count('id', filter=Q(designer_status="D")),

            pending_count=Count('id', filter=Q(status="P")),
            in_progress_count=Count('id', filter=Q(status="EA")),
            complete_count=Count('id', filter=Q(status="CO")),
            canceled_count=Count('id', filter=Q(status="C")),
            termination_count=Count('id', filter=Q(status="D")),

            is_released_to_engineering_count=Count('id', filter=Q(is_released_to_engineering=True)),
            pending_material_list=Count('id', filter=Q(is_released_to_engineering=True) & Q(
                designer_status="CO",
                material_list_is_completed=False
            )),
            blocked_to_engineering=Count('id', filter=~Q(is_released_to_engineering=True) |
                Q(units__bill_file__isnull=True, units__new_contract_number=False))
        )

        return Response({"indicators": raw_indicators})


    @action(detail=False, methods=["get"], url_path="logistics-indicators")
    def logistics_indicators(self, request, *args, **kwargs):
        filter_params = request.GET.dict()
        filter_hash = md5(str(filter_params).encode()).hexdigest()
        cache_key = f"logistics_indicators_{filter_hash}"

        indicators = cache.get(cache_key)
        if indicators:
            return Response({"indicators": indicators})

        request.query_params._mutable = True
        request.query_params['metrics'] = 'is_released_to_engineering,purchase_status,delivery_status'
        request.query_params._mutable = False

        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.apply_additional_filters(queryset, request)
        queryset = queryset.with_is_released_to_engineering().with_purchase_status().with_delivery_status()

        PURCHASE_STATUSES = [
            "Bloqueado", "Liberado", "Pendente", "Compra Realizada", "Cancelado", "Distrato",
            "Aguardando Previsão de Entrega", "Aguardando Pagamento"
        ]
        DELIVERY_STATUSES = [
            "Bloqueado", "Liberado", "Agendado", "Entregue", "Cancelado"
        ]

        purchase_result = {status: 0 for status in PURCHASE_STATUSES}
        delivery_result = {status: 0 for status in DELIVERY_STATUSES}
        total_count = queryset.count()

        for project in queryset:
            if hasattr(project, 'purchase_status') and project.purchase_status in purchase_result:
                purchase_result[project.purchase_status] += 1
            if hasattr(project, 'delivery_status') and project.delivery_status in delivery_result:
                delivery_result[project.delivery_status] += 1

        indicators = {
            "purchase_status": purchase_result,
            "delivery_status": delivery_result,
            "total_count": total_count,
        }

        cache.set(cache_key, indicators, 60)
        return Response({"indicators": indicators})

                
    # @action(detail=False, methods=['get'], url_path='installments-indicators')
    # def installments_indicators(self, request, *args, **kwargs):
    #     # 1) monta a cache key
    #     filter_params = request.GET.dict()
    #     filter_hash   = md5(str(filter_params).encode()).hexdigest()
    #     cache_key     = f"payments_indicators_{filter_hash}"
    #     cached        = cache.get(cache_key)
    #     if cached:
    #         return Response({"indicators": cached})

    #     # 2) pega apenas os projetos filtrados pela view
    #     qs_projects = self.filter_queryset(self.get_queryset())
    #     project_ids = qs_projects.values_list("id", flat=True)

    #     # 3) monta um queryset de parcelas que pertençam a esses projetos
    #     now = timezone.now()
    #     qs_inst = PaymentInstallment.objects.filter(
    #         payment__sale__projects__id__in=project_ids
    #     )

    #     # 4) agrega tudo numa única query sobre Installment
    #     installments_indicators = qs_inst.aggregate(
    #         overdue_installments_count=Count(
    #             "id",
    #             filter=Q(is_paid=False, due_date__lte=now)
    #         ),
    #         overdue_installments_value=Coalesce(
    #             Sum(
    #                 "installment_value",
    #                 filter=Q(is_paid=False, due_date__lte=now),
    #                 output_field=DecimalField()
    #             ),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         on_time_installments_count=Count(
    #             "id",
    #             filter=Q(is_paid=False, due_date__gt=now)
    #         ),
    #         on_time_installments_value=Coalesce(
    #             Sum(
    #                 "installment_value",
    #                 filter=Q(is_paid=False, due_date__gt=now),
    #                 output_field=DecimalField()
    #             ),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         paid_installments_count=Count(
    #             "id",
    #             filter=Q(is_paid=True)
    #         ),
    #         paid_installments_value=Coalesce(
    #             Sum(
    #                 "installment_value",
    #                 filter=Q(is_paid=True),
    #                 output_field=DecimalField()
    #             ),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         total_installments=Count("id"),
    #         total_installments_value=Coalesce(
    #             Sum("installment_value", output_field=DecimalField()),
    #             Value(0, output_field=DecimalField())
    #         ),
    #     )

    #     # 5) mantém seu bloco de consistência (idem antes)
    #     qs_consistency = qs_projects.annotate(
    #         total_installments_value=Coalesce(
    #             Sum("installments__installment_value", output_field=DecimalField()),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         total_installments_count=Count("installments"),
    #         paid_installments_count=Count(
    #             "installments",
    #             filter=Q(sale__payments__installments__is_paid=True)
    #         ),
    #     ).annotate(
    #         is_consistent=Case(
    #             When(
    #                 Q(total_installments_count=F("paid_installments_count")) &
    #                 Q(value=F("total_installments_value")),
    #                 then=Value(True)
    #             ),
    #             default=Value(False),
    #             output_field=BooleanField()
    #         )
    #     )
    #     consistency_indicators = qs_consistency.aggregate(
    #         total_payments=Count("id"),
    #         total_payments_value=Coalesce(
    #             Sum("value", output_field=DecimalField()),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         consistent_payments=Count("id", filter=Q(is_consistent=True)),
    #         consistent_payments_value=Coalesce(
    #             Sum("value", filter=Q(is_consistent=True), output_field=DecimalField()),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         inconsistent_payments_value=Coalesce(
    #             Sum("value", filter=~Q(is_consistent=True), output_field=DecimalField()),
    #             Value(0, output_field=DecimalField())
    #         ),
    #         inconsistent_payments=Count("id", filter=~Q(is_consistent=True))
    #     )

    #     # 6) combina, cacheia e retorna
    #     combined = {
    #         "installments": installments_indicators,
    #         "consistency": consistency_indicators
    #     }
    #     cache.set(cache_key, combined, 60)
    #     return Response({"indicators": combined})

    
    
    
class ContractSubmissionViewSet(BaseModelViewSet):
    queryset = ContractSubmission.objects.all()
    serializer_class = ContractSubmissionSerializer


class GenerateSalesProjectsView(APIView):
    http_method_names = ['post', 'get']

    @transaction.atomic
    def post(self, request):
        sale_id = request.data.get('sale_id')

        # Verificar se a venda existe
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recuperar os produtos da venda
        sale_products = SaleProduct.objects.filter(sale=sale)
        
        if not sale_products.exists():
            return Response({'message': 'Venda não possui produtos associados.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Projetos já criados para esta venda
        projects = Project.objects.filter(sale=sale)
        
        # Listas para rastrear os resultados
        created_projects = []
        already_existing_projects = []
        
        # Criar um projeto para cada produto da venda, se ainda não existir
        for sale_product in sale_products:
            if projects.filter(product=sale_product.product).exists():
                already_existing_projects.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
                continue  # Pula para o próximo produto

            # Dados do projeto
            project_data = {
                'sale_id': sale.id,
                'status': 'P',
                'product_id': sale_product.product.id,
            }
            # Serializar e salvar
            project_serializer = ProjectSerializer(data=project_data)
            if project_serializer.is_valid():
                project = project_serializer.save()
                created_projects.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
            else:
                return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Verificar o resultado
        if not created_projects:
            return Response({'message': 'Todos os projetos já foram criados.', 'already_existing_projects': already_existing_projects}, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Projetos gerados com sucesso.',
            'created_projects': created_projects,
            'already_existing_projects': already_existing_projects,
        }, status=status.HTTP_200_OK)


    def get(self, request):
        sale_id = request.query_params.get('sale_id')
        
        if not sale_id:
            return Response({'message': 'É necessário informar o ID da venda.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recuperar os produtos e os projetos associados à venda
        sale_products = SaleProduct.objects.filter(sale=sale)
        projects = Project.objects.filter(sale=sale)
        
        already_generated = []
        pending_generation = []
        
        # Verificar quais produtos já possuem projetos e quais estão pendentes
        for sale_product in sale_products:
            if projects.filter(product=sale_product.product).exists():
                already_generated.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                    'amount': sale_product.amount,
                    'value': sale_product.value,
                    'reference_value': sale_product.reference_value,
                    'cost_value': sale_product.cost_value,
                })
            else:
                pending_generation.append({
                    'product_id': sale_product.product.id,
                    'product_name': sale_product.product.name,
                })
        
        response_data = {
            'sale_id': sale.id,
            'sale_status': sale.status,
            'already_generated': already_generated,
            'pending_generation': pending_generation,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)



class GeneratePreSaleView(APIView):
    http_method_names = ['post']

    def post(self, request):
        with transaction.atomic():
            data = request.data
            lead_id = data.get('lead_id')
            products = data.get('products')
            commercial_proposal_id = data.get('commercial_proposal_id')

            # Validações iniciais
            if not lead_id:
                return Response({'message': 'lead_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

            if not products and not commercial_proposal_id:
                return Response({'message': 'É obrigatório possuir um produto ou uma Proposta Comercial.'},
                                status=status.HTTP_400_BAD_REQUEST)

            if commercial_proposal_id and products:
                return Response({'message': 'commercial_proposal_id e products são mutuamente exclusivos.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Obtenção da Proposta Comercial (se fornecida)
            comercial_proposal = None
            if commercial_proposal_id:
                try:
                    comercial_proposal = ComercialProposal.objects.select_related(
                        'lead'
                        ).get(id=commercial_proposal_id)
                except ComercialProposal.DoesNotExist:
                    return Response({'message': 'Proposta Comercial não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

            # Obtenção do Lead com seus relacionamentos críticos
            try:
                lead = Lead.objects.select_related(
                    'seller',
                    'seller__employee',
                    'seller__employee__branch',
                    'seller__employee__user_manager',
                    'seller__employee__user_manager__employee',
                    'seller__employee__user_manager__employee__user_manager'
                ).prefetch_related('addresses').get(id=lead_id)
            except Lead.DoesNotExist:
                return Response({'message': 'Lead não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

            if not lead.first_document:
                return Response({'message': 'Lead não possui CPF cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validação e criação do telefone (única validação)
            phone_number = lead.phone
            if not phone_number or not re.match(r'^\d{10,11}$', phone_number):
                return Response({'message': 'Telefone no formato inválido.'}, status=status.HTTP_400_BAD_REQUEST)
            phone = self._create_phone(phone_number)
            if isinstance(phone, Response):
                return phone

            # Busca usuário existente pelo CPF formatado
            formatted_document = lead.first_document.replace('.', '').replace('-', '')
            customer = User.objects.filter(first_document=formatted_document).first()

            # Atualiza ou cria o cliente
            if customer:
                customer = self._update_customer(customer, lead, phone)
                if isinstance(customer, Response):
                    return customer
            else:
                customer = self._create_customer(lead, phone)
                if isinstance(customer, Response):
                    return customer

            # Associação do Lead ao cliente
            lead.customer = customer
            lead.save()

            products_ = []
            total_value = comercial_proposal.value if comercial_proposal else 0

            # Processa os produtos (novo ou existentes)
            if products:
                for prod_data in products:
                    if 'id' not in prod_data:
                        product_serializer = ProductSerializer(data=prod_data)
                        if product_serializer.is_valid():
                            new_product = product_serializer.save()
                            products_.append(new_product)
                            total_value += self._calculate_product_value(new_product)
                        else:
                            return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        try:
                            existing_product = Product.objects.get(id=prod_data['id'])
                            products_.append(existing_product)
                            total_value += self._calculate_product_value(existing_product)
                        except Product.DoesNotExist:
                            return Response({'message': f'Produto com id {prod_data["id"]} não encontrado.'},
                                            status=status.HTTP_400_BAD_REQUEST)

            # Obtém os IDs relacionados à venda
            sale_ids = self._get_sale_related_ids(lead)
            if isinstance(sale_ids, Response):
                return sale_ids
            seller_id, sales_supervisor_id, sales_manager_id = sale_ids

            # Cria a pré-venda
            sale_data = {
                'customer': customer.id,
                'lead': lead.id,
                'is_pre_sale': True,
                'status': 'P',
                'branch': lead.seller.employee.branch.id,
                'seller': seller_id,
                'sales_supervisor': sales_supervisor_id,
                'sales_manager': sales_manager_id,
                'total_value': round(total_value, 3),
            }
            if products:
                sale_data['products_ids'] = [p.id for p in products_]

            sale_serializer = SaleSerializer(data=sale_data)
            if sale_serializer.is_valid():
                pre_sale = sale_serializer.save()
            else:
                return Response(sale_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Caso exista Proposta Comercial, vincula produtos à pré-venda
            if comercial_proposal:
                salesproducts = SaleProduct.objects.filter(commercial_proposal=comercial_proposal)
                for sp in salesproducts:
                    if sp.sale:
                        return Response({'message': 'Proposta Comercial já vinculada à uma pré-venda.'},
                                        status=status.HTTP_400_BAD_REQUEST)
                # Atualiza status da proposta e vincula os SaleProducts à pré-venda
                comercial_proposal.status = 'A'
                comercial_proposal.save()
                for sp in salesproducts:
                    sp.sale = pre_sale
                SaleProduct.objects.bulk_update(salesproducts, ['sale'])

                # Cria os projetos para cada produto da proposta comercial
                for sp in salesproducts:
                    project_data = {
                        'sale': pre_sale.id,
                        'status': 'P',
                        'product': sp.product.id,
                    }
                    project_serializer = ProjectSerializer(data=project_data)
                    if project_serializer.is_valid():
                        project_serializer.save()
                    else:
                        return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Cria os projetos para os produtos (se fornecidos)
            if products:
                for product in products_:
                    project_data = {
                        'sale': pre_sale.id,
                        'status': 'P',
                        'product': product.id,
                    }
                    project_serializer = ProjectSerializer(data=project_data)
                    if project_serializer.is_valid():
                        project_serializer.save()
                    else:
                        return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Criação do pagamento (comentado conforme a versão original)
            """
            payment_data = data.get('payment', {})
            payment_data['value'] = total_value
            payment_data['sale'] = pre_sale.id
            payment_serializer = PaymentSerializer(data=payment_data)
            if payment_serializer.is_valid():
                payment_serializer.save()
            else:
                return Response(payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            """

            return Response({
                'message': 'Cliente, products, pré-venda, projetos e ~~pagamentos~~ gerados com sucesso.',
                'pre_sale_id': pre_sale.id
            }, status=status.HTTP_200_OK)

    def _create_phone(self, phone_number):
        """
        Valida e cria o telefone utilizando o PhoneNumberSerializer.
        """
        match = re.match(r'(\d{2})(\d+)', phone_number)
        if match:
            area_code, number = match.groups()
            phone_data = {
                'country_code': 55,
                'area_code': area_code,
                'phone_number': number,
                'is_main': True,
            }
            phone_serializer = PhoneNumberSerializer(data=phone_data)
            if phone_serializer.is_valid():
                return phone_serializer.save()
            else:
                return Response(phone_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Telefone no formato inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    def _update_customer(self, customer, lead, phone):
        """
        Atualiza o usuário existente com os dados do Lead.
        """
        phone_ids = list(customer.phone_numbers.values_list('id', flat=True))
        if phone.id not in phone_ids:
            phone_ids.append(phone.id)

        update_data = {
            'complete_name': lead.name,
            'addresses': list(lead.addresses.values_list('id', flat=True)),
            'phone_numbers_ids': phone_ids,
        }
        if lead.contact_email != customer.email:
            update_data['email'] = lead.contact_email

        user_serializer = UserSerializer(customer, data=update_data, partial=True)
        if user_serializer.is_valid():
            return user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_customer(self, lead, phone):
        """
        Cria um novo usuário com base nos dados do Lead.
        """
        base_username = f"{lead.name.split(' ')[0]}.{lead.name.split(' ')[-1]}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user_data = {
            'complete_name': lead.name,
            'username': username,
            'first_name': lead.name.split(' ')[0],
            'last_name': lead.name.split(' ')[-1],
            'email': lead.contact_email,
            'addresses': list(lead.addresses.values_list('id', flat=True)),
            'user_types': [UserType.objects.get(name='Cliente').id],
            'first_document': lead.first_document,
            'phone_numbers_ids': [phone.id],
        }
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            return user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _calculate_product_value(self, product):
        base_value = product.product_value
        aggregation = ProductMaterials.objects.filter(product=product, is_deleted=False).aggregate(
            total_cost=Sum(F('material__price') * F('amount'))
        )
        materials_cost = aggregation.get('total_cost') or 0
        return base_value + materials_cost

    def _get_sale_related_ids(self, lead):
        try:
            seller = lead.seller
            seller_id = seller.id
            supervisor = seller.employee.user_manager
            supervisor_id = supervisor.id if supervisor else None
            manager = None
            if supervisor and hasattr(supervisor, 'employee') and supervisor.employee.user_manager:
                manager = supervisor.employee.user_manager
            manager_id = manager.id if manager else None
            return seller_id, supervisor_id, manager_id
        except Exception as e:
            logger.error(f'Erro ao recuperar informações do vendedor: {str(e)}')
            return Response({'message': 'Erro ao recuperar informações do vendedor.'},
                            status=status.HTTP_400_BAD_REQUEST)



class ContractTemplateViewSet(BaseModelViewSet):
    queryset = ContractTemplate.objects.all()
    serializer_class = ContractTemplateSerializer
    
    
class ValidateContractView(APIView):
    http_method_names = ['get']
    permission_classes = [AllowAny]
    
    def get(self, request):
        envelope_id = request.query_params.get('envelope_id')
        
        if not envelope_id:
            return Response({'message': 'envelope_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        contract_submission = ContractSubmission.objects.filter(envelope_id=envelope_id).first()
        if contract_submission is None:
            return Response({'message': 'Contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        customer_name = contract_submission.sale.customer.complete_name
        masked_email = re.sub(r'(?<=.{2}).(?=.*@)', '*', contract_submission.sale.customer.email)
        masked_phone = re.sub(r'(?<=.{2}).(?=.{2})', '*', contract_submission.sale.customer.phone_numbers.first().phone_number)
        masked_first_document = re.sub(r'(?<=.{3}).', '*', contract_submission.sale.customer.first_document)
        
        return Response({
            'message': f'Contrato validado com sucesso. Cliente: {customer_name}',
            'contract_submission': {
                'sale': {
                    'customer': {
                        'complete_name': customer_name,
                        'email': masked_email,
                        'phone_number': masked_phone,
                        'first_document': masked_first_document,
                    },
                    'seller': {
                        "complete_name": contract_submission.sale.seller.complete_name
                    }
                },
                'status': contract_submission.status,
                'submit_datetime': contract_submission.submit_datetime,
                'due_date': contract_submission.due_date,
            }
        }, status=status.HTTP_200_OK)


class GenerateContractView(APIView):
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request):
        sale_id = request.data.get('sale_id')
        sale = self._get_sale(sale_id)
        if isinstance(sale, Response):
            return sale

        # Valida campos obrigatórios da venda e do cliente
        missing_fields_response = self._validate_sale_data(sale)
        if missing_fields_response:
            return missing_fields_response

        if not sale.payments.exists():
            return Response({'message': 'Venda não possui pagamentos associados.'}, status=status.HTTP_400_BAD_REQUEST)

        total_payments_value = sum(payment.value for payment in sale.payments.all())
        if total_payments_value != sale.total_value:
            return Response({'message': 'A soma dos valores dos pagamentos é diferente do valor total da venda.'}, status=status.HTTP_400_BAD_REQUEST)

        total_payments_value_formatted = formats.number_format(total_payments_value, 2)

        variables = self._validate_variables(request.data.get('contract_data', {}))
        if isinstance(variables, Response):
            return variables

        contract_template = ContractTemplate.objects.first()
        if not contract_template:
            return Response({'message': 'Template de contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        customer_data = self._get_customer_data(sale.customer)
        if isinstance(customer_data, Response):
            return customer_data

        # Verifica se é modo preview; se for, gera o PDF e retorna a pré-visualização
        preview = request.query_params.get('preview') == 'true'

        materials_list = self._generate_materials_list(sale)
        payments_list = self._generate_payments_list(sale)
        projects_data = self._get_projects_data(sale)
        # Como o envio para o Clicksign será processado de forma assíncrona,
        # não geramos QR code ou URL de validação nesta etapa.
        contract_content = self._replace_variables(
            contract_template.content,
            variables,
            customer_data,
            sale.branch.energy_company.name,
            materials_list,
            total_payments_value_formatted,
            payments_list,
            projects_data,
            sale.branch.address.city,
            qr_code="",
            validation_url=""
        )

        pdf = self._generate_pdf(contract_content)
        if isinstance(pdf, Response):
            return pdf

        if preview:
            return self._preview_pdf(pdf)

        # Enfileira o envio do contrato para o Clicksign via Celery.
        from resolve_crm.task import send_contract_to_clicksign
        send_contract_to_clicksign.delay(sale.id, pdf)

        return Response({
            'message': 'Contrato enfileirado com sucesso para envio ao Clicksign.'
        }, status=status.HTTP_200_OK)

    def _validate_sale_data(self, sale):
        missing = []
        if not sale.branch or not sale.branch.energy_company:
            missing.append('Empresa de energia (branch)')
        if not sale.customer:
            missing.append('Dados do cliente')
        else:
            if not sale.customer.complete_name:
                missing.append('Nome do cliente')
            if not sale.customer.first_document:
                missing.append('Documento (CPF/CNPJ) do cliente')
        if missing:
            return Response(
                {'message': f'Campos obrigatórios ausentes: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    def _get_sale(self, sale_id):
        try:
            return Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    def _validate_variables(self, variables):
        if not isinstance(variables, dict):
            return Response({'message': 'As variáveis devem ser um dicionário.'}, status=status.HTTP_400_BAD_REQUEST)
        return variables

    def _get_customer_data(self, customer):
        address = customer.addresses.first()
        if not address:
            return Response({'message': 'Endereço do cliente não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        return {
            'customer_name': customer.complete_name,
            'customer_first_document': customer.first_document,
            'customer_second_document': customer.second_document,
            'customer_street': address.street,
            'customer_house_number': address.number,
            'customer_neighborhood': address.neighborhood,
            'customer_city': address.city,
            'customer_state': address.state,
            'customer_zip_code': address.zip_code,
            'customer_country': address.country,
            'customer_complement': address.complement,
        }

    def _get_projects_data(self, sale):
        projects = sale.projects.all()
        watt_peaks = [f"{project.product.params} kWp" for project in projects]
        if len(watt_peaks) > 1:
            watt_peak = ', '.join(watt_peaks[:-1]) + ' e ' + watt_peaks[-1]
        elif watt_peaks:
            watt_peak = watt_peaks[0]
        else:
            watt_peak = ''
        return {
            'project_count': len(projects),
            'project_plural': "s" if len(projects) > 1 else "",
            'watt_peak': watt_peak
        }

    def _generate_materials_list(self, sale):
        materials = []
        for project in sale.projects.all():
            product_materials = ProductMaterials.objects.filter(
                product=project.product,
                is_deleted=False
            )
            for pm in product_materials:
                materials.append({
                    'name': pm.material.name,
                    'amount': round(pm.amount, 2),
                    'price': pm.material.price
                })
        return "".join(f"<li>{m['name']} - Quantidade: {m['amount']:.2f}</li>" for m in materials)

    def _generate_payments_list(self, sale):
        payments = [
            {
                'type': payment.get_payment_type_display(),
                'value': f"{payment.value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'financier': f" - Financiadora: {payment.financier}" if payment.financier else ""
            }
            for payment in sale.payments.all()
        ]
        return "".join(f"<li>Tipo: {p['type']}{p['financier']} - Valor: R$ {p['value']}</li>" for p in payments)

    def _replace_variables(self, content, variables, customer_data, energy_company, materials_list, total_value, payments_list, projects_data, city, qr_code, validation_url):
        now = datetime.datetime.now()
        day = now.day
        month = formats.date_format(now, 'F')
        year = now.year
        today_formatted = f'{day} de {month} de {year}'

        variables.update({
            'materials_list': materials_list,
            'payments_list': payments_list,
            'energy_company': energy_company,
            **projects_data,
            **customer_data,
            'today': today_formatted,
            'city': city,
            'total_value': total_value,
            'qr_code': qr_code,
            'validation_url': validation_url
        })
        for key, value in variables.items():
            content = re.sub(fr"{{{{\s*{key}\s*}}}}", str(value), content)
        return content

    def _generate_pdf(self, content):
        try:
            rendered_html = render_to_string('contract_base.html', {'content': content})
            return HTML(string=rendered_html).write_pdf()
        except Exception as e:
            logger.error(f'Erro ao gerar o PDF: {e}')
            return Response({'message': f'Erro ao gerar o PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _preview_pdf(self, pdf):
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="preview_contract.pdf"'
        return response


class GenerateCustomContract(APIView):
    def post(self, request):
        sale_id = request.data.get('sale_id')
        contract_html = request.data.get('contract_html')

        if not sale_id:
            return Response({'message': 'sale_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not contract_html:
            return Response({'message': 'contract_html é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'message': 'Venda não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Gerando o PDF a partir do HTML
        try:
            rendered_html = render_to_string('contract_base.html', {'content': contract_html})
            pdf = HTML(string=rendered_html).write_pdf()
        except Exception as e:
            return Response({'message': f'Erro ao gerar o PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Salvando o arquivo PDF no backend de armazenamento padrão
        try:
            # Sanitizar o nome do arquivo
            file_name = f"contract_sale_{sale_id}.pdf"
            sanitized_file_name = re.sub(r'[^a-zA-Z0-9_.]', '_', file_name)
            
            # Criar o arquivo no Google Cloud Storage
            attachment = Attachment.objects.create(
                object_id=sale.id,
                content_type_id=ContentType.objects.get_for_model(Sale).id,
                status="Em Análise",
            )
            
            # Salvar o arquivo diretamente no campo `file` do modelo
            attachment.file.save(sanitized_file_name, ContentFile(pdf))

        except Exception as e:
            return Response({'message': f'Erro ao salvar o arquivo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'message': 'Contrato gerado com sucesso. Envio ao Clicksign efetuado.', 'attachment_id': attachment.id}, status=status.HTTP_200_OK)


class ReasonViewSet(BaseModelViewSet):
    queryset = Reason.objects.all()
    serializer_class = ReasonSerializer


def save_all_sales_func(request):
    save_all_sales.delay()
    messages.success(request, 'Todas as vendas foram salvas com sucesso.')
    return redirect('admin:index')


@api_view(['GET'])
def list_sales_func(request):
    fields = [f.name for f in Sale._meta.get_fields() if not f.many_to_many and not f.one_to_many]
    sales = Sale.objects.values(*fields)

    # Paginação
    paginator = PageNumberPagination()
    paginator.page_size = 10  # Define o número de itens por página
    paginated_sales = paginator.paginate_queryset(sales, request)

    return paginator.get_paginated_response(paginated_sales)