import re
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum, Value, DecimalField
from django.db.models.functions import Coalesce

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError

from api.serializers import BaseSerializer
from core.serializers import AttachmentSerializer
from accounts.serializers import AddressSerializer
from financial.models import FranchiseInstallment
from logistics.models import Materials, Product, ProjectMaterials, SaleProduct
from resolve_crm.models import *

class OriginSerializer(BaseSerializer):
    class Meta:
        model = Origin
        fields = '__all__'
      

 
class LeadSerializer(BaseSerializer):
    proposals = serializers.SerializerMethodField()
    class Meta:
        model = Lead
        fields = '__all__'
        
    def validate(self, data):
        phone = data.get('phone')
        if phone and len(re.sub(r'\D', '', phone)) != 11:
            raise ValidationError({'phone': 'Phone number must have exactly 11 digits.'})
        return data
    
    def get_proposals(self, obj):
        proposals = obj.proposals.values_list('id', flat=True)
        return list(proposals)


class LeadTaskSerializer(BaseSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class MarketingCampaignSerializer(BaseSerializer):
    class Meta:
        model = MarketingCampaign
        fields = '__all__'


class SaleSerializer(BaseSerializer):
    products_ids = serializers.ListField(
    child=serializers.IntegerField(), required=False
    )
    commercial_proposal_id = serializers.IntegerField(write_only=True, required=False)
    
    documents_under_analysis = serializers.SerializerMethodField()
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    final_service_opinion = serializers.SerializerMethodField()
    signature_status = serializers.SerializerMethodField()
    is_released_to_engineering = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = '__all__'
        
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_can_edit(request.user)
        return False
    
    def get_documents_under_analysis(self, obj):
        attachments = getattr(obj, 'attachments_under_analysis', [])
        return AttachmentSerializer(attachments, many=True, context=self.context).data
    
    def get_is_released_to_engineering(self, obj):
        projects = getattr(obj, 'cached_projects', None)
        if projects is None:
            projects = obj.projects.with_is_released_to_engineering()
        return any(getattr(p, 'is_released_to_engineering', False) for p in projects)
    
    def get_signature_status(self, obj):
        submissions = list(getattr(obj, 'all_submissions', obj.contract_submissions.all()))
        statuses = {s.status for s in submissions}

        if not obj.signature_date:
            if not statuses:
                return 'Pendente'
            if 'P' in statuses and 'A' not in statuses:
                return 'Enviado'
            if 'A' in statuses:
                return 'Assinado'
            if 'R' in statuses:
                return 'Recusado'
        return 'Assinado'
  
    def get_final_service_opinion(self, obj):
        projects = getattr(obj, 'cached_projects', None)
        if projects is None:
            projects = obj.projects.select_related('inspection__final_service_opinion')
        opinions = [
            {
                "id": p.inspection.final_service_opinion.id,
                "name": p.inspection.final_service_opinion.name,
            }
            for p in projects
            if p.inspection and p.inspection.final_service_opinion
        ]
        return opinions or None
        
    def validate(self, data):
        # Validação para definir o percentual de repasse
        if self.instance is None:
            branch = data.get('branch')
            if 'transfer_percentage' not in data:
                if branch and branch.transfer_percentage:
                    data['transfer_percentage'] = branch.transfer_percentage
                else:
                    raise ValidationError({'transfer_percentage': 'Percentual de repasse não cadastrado.'})

        """
        # Validação adicional para pré-venda
        if data.get('is_pre_sale'):
            customer = data.get('customer')
            qs = Sale.objects.filter(customer=customer, is_pre_sale=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({'customer_id': 'Já existe uma pré-venda para esse cliente.'})
        """
        
        return data
    
    
    def create(self, validated_data):
        products = validated_data.pop('products_ids', [])
        commercial_proposal_id = validated_data.pop('commercial_proposal_id', None)
        cancellation_reasons = validated_data.pop('cancellation_reasons', None)

        try:
            sale = super().create(validated_data)
        except Exception as e:
            logging.error(f"❌ erro ao criar Sale: {e}")
            raise

        try:
            with transaction.atomic():
                self._handle_products(
                    sale,
                    products=products,
                    commercial_proposal_id=commercial_proposal_id
                )
                if cancellation_reasons is not None:
                    sale.cancellation_reasons.set(cancellation_reasons)
        except Exception as e:
            print("❌ erro em _handle_products ou M2M:", e)
            raise

        return sale

    def update(self, instance, validated_data):
        request_user = self.context['request'].user
        if not instance.user_can_edit(request_user):
            raise PermissionDenied("Você não pode editar vendas finalizadas.")

        cancellation_reasons = validated_data.pop('cancellation_reasons', None)

        # atualiza atributos simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        with transaction.atomic():
            instance.save()
            if cancellation_reasons is not None:
                instance.cancellation_reasons.set(cancellation_reasons)

        return instance


    def _handle_products(self, sale, products=None, commercial_proposal_id=None):
        products_list = []

        if commercial_proposal_id is not None:
            try:
                proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
            except ComercialProposal.DoesNotExist:
                raise ValidationError({"detail": "Proposta comercial não encontrada."})

            sale_products_qs = SaleProduct.objects.filter(
                commercial_proposal=proposal,
                sale__isnull=True
            )

            if not sale_products_qs.exists():
                raise ValidationError({"detail": "Proposta comercial não possui produtos disponíveis."})

            sale_products_qs.update(sale=sale)
            products_list = list(sale_products_qs)

        elif products:
            new_sale_products = [
                SaleProduct(
                    sale=sale,
                    product=prod,
                    value=prod.product_value or Decimal('0'),
                    reference_value=prod.reference_value or prod.product_value or Decimal('0'),
                    cost_value=prod.cost_value or Decimal('0'),
                    amount=1
                )
                for prod in products
            ]
            SaleProduct.objects.bulk_create(new_sale_products)

        # cria projetos diretamente
        sale_products = SaleProduct.objects.filter(sale=sale)
        project_instances = [
            Project(sale=sale, product=sp.product)
            for sp in sale_products
        ]
        if project_instances:
            Project.objects.bulk_create(project_instances)

        # atualiza total_value da venda
        aggregate_total = SaleProduct.objects.filter(sale=sale).aggregate(
            total=Sum(F('value') * F('amount'))
        )['total'] or Decimal('0')
        sale.total_value = aggregate_total
        sale.save(update_fields=['total_value'])

        # calcula parcela do franqueado
        aggregate_reference = SaleProduct.objects.filter(sale=sale).aggregate(
            reference_sum=Sum('reference_value')
        )['reference_sum'] or Decimal('0')

        installment_value = sale.calculate_franchise_installment_value(aggregate_reference)

        FranchiseInstallment.objects.create(
            sale=sale,
            installment_value=installment_value,
            marketing_tax=sale.branch.marketing_tax,
            margin=sale.branch.margin,
        )

            
    def create_projects(self, sale, products):
        projects = [
            Project(sale=sale, product=sp.product)
            for sp in products
        ]
        Project.objects.bulk_create(projects)

    def validate_products_ids(self, products_ids):
        products = []
        for product_id in products_ids:
            if isinstance(product_id, Product):
                products.append(product_id)
            else:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    raise ValidationError({"detail": f"Produto com ID {product_id} não encontrado."})
        return products

    def calculate_total_value(self, sale_products):
        total_value = 0
        for sp in sale_products:
            total_value += sp.value * sp.amount
        return total_value

    def calculate_total_installment_value(self, sale, products): 
            from decimal import Decimal

            reference_value = sum(Decimal(p.reference_value or 0) for p in products)
            difference_value = Decimal(sale.total_value) - reference_value

            transfer_percentage = sale.transfer_percentage
            if transfer_percentage is None:
                transfer_percentage = sale.branch.transfer_percentage or 0
            transfer_percentage = Decimal(transfer_percentage)

            if difference_value <= 0:
                total_value = reference_value * (transfer_percentage / Decimal("100")) - difference_value
            else:
                margin_7 = difference_value * Decimal("0.07")
                total_value = (reference_value * (transfer_percentage / Decimal("100"))) + difference_value - margin_7

            return total_value


class ProjectSerializer(BaseSerializer):
    address = serializers.SerializerMethodField()
    access_opnion = serializers.CharField(read_only=True)
    trt_pending = serializers.CharField(read_only=True)
    access_opnion_status = serializers.CharField(read_only=True)
    load_increase_status = serializers.CharField(read_only=True)
    branch_adjustment_status = serializers.CharField(read_only=True)
    new_contact_number_status = serializers.CharField(read_only=True)
    final_inspection_status = serializers.CharField(read_only=True)
    request_requested = serializers.BooleanField(read_only=True)
    pending_material_list = serializers.BooleanField(read_only=True)
    journey_counter  = serializers.IntegerField(read_only=True, required=False)
    is_released_to_engineering = serializers.BooleanField(read_only=True)
    trt_status = serializers.CharField(read_only=True)
    supply_adquance_names = serializers.CharField(read_only=True)
    purchase_status = serializers.CharField(read_only=True)
    expected_delivery_date = serializers.DateField(read_only=True)
    expected_delivery_status = serializers.CharField(read_only=True)
    delivery_status = serializers.CharField(read_only=True)
    installation_status = serializers.CharField(read_only=True)
    is_released_to_installation = serializers.BooleanField(read_only=True, required=False)
    latest_installation = serializers.SerializerMethodField()
    access_opnion_days_int = serializers.IntegerField(read_only=True)
    load_increase_days_int = serializers.IntegerField(read_only=True)
    branch_adjustment_days_int = serializers.IntegerField(read_only=True)
    new_contact_number_days_int = serializers.IntegerField(read_only=True)
    final_inspection_days_int = serializers.IntegerField(read_only=True)
    total_tickets = serializers.IntegerField(read_only=True)
    total_tickets_abertos = serializers.IntegerField(read_only=True)
    avg_tempo_resolucao = serializers.DurationField(read_only=True)
    ticket_aberto_mais_antigo = serializers.DateTimeField(read_only=True)
    
    distance_to_matriz_km = serializers.SerializerMethodField()

    materials_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = '__all__'
    
    
    def get_distance_to_matriz_km(self, obj):
        if obj.distance_to_matriz_km is not None:
            return obj.distance_to_matriz_km
        else:
            return 0

    def get_documents_under_analysis(self, obj):
        documents = obj.documents_under_analysis[:10]
        return [{"id": d.id, "name": d.document_type.name if d.document_type else None, "status": d.status} for d in documents]

    def get_address(self, obj):
        main_unit = obj.main_unit_prefetched[0] if hasattr(obj, 'main_unit_prefetched') and obj.main_unit_prefetched else None
        return AddressSerializer(main_unit.address).data if main_unit and main_unit.address else None
    
    def get_latest_installation(self, obj):
        inst = obj.latest_installation_obj
        if not inst:
            return None

        # 1 query para soma dos módulos
        panel_count = ProjectMaterials.objects.filter(
            project=inst.project,
            is_deleted=False,
            material__attributes__key='Tipo',
            material__attributes__value='MODULO',
            material__attributes__is_deleted=False
        ).aggregate(
            total=Coalesce(
                Sum('amount', output_field=DecimalField()),
                Value(0, output_field=DecimalField()),
                output_field=DecimalField()
            )
        )['total']

        inst = (
            Schedule.objects
            .select_related('address', 'schedule_agent', 'final_service_opinion_user')
            .get(pk=inst.pk)
        )

        addr = AddressSerializer(inst.address).data if inst.address else None

        return {
            'id': inst.id,
            'schedule_agent': inst.schedule_agent_id,
            'final_service_opinion_user': inst.final_service_opinion_user_id,
            'panel_count': panel_count,
            'complete_address': addr.get('complete_address') if addr else None,
            'neighborhood': addr.get('neighborhood') if addr else None
        }

    def update(self, instance, validated_data):
        materials_data = validated_data.pop('materials_data', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if materials_data:
            self._save_materials(instance, materials_data)

        return instance


    def _save_materials(self, project, materials_data):
        project.materials.clear()
        for material_data in materials_data:
            material_id = material_data.get('material_id')
            amount = material_data.get('amount', 1)
            is_exit = material_data.get('is_exit', False)
            serial_number = material_data.get('serial_number', None)

            try:
                material = Materials.objects.get(id=material_id)
            except Materials.DoesNotExist:
                raise ValidationError({'detail': f'Material com id {material_id} não encontrado.'}, code=404)

            ProjectMaterials.objects.create(
                project=project,
                material=material,
                amount=amount,
                is_exit=is_exit,
                serial_number=serial_number
        )
       

class ComercialProposalSerializer(BaseSerializer):
    products_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ComercialProposal
        fields = '__all__'

    def create(self, validated_data):
        products_ids = validated_data.pop('products_ids', [])
        proposal = super().create(validated_data)
        self._set_products(proposal, products_ids)
        return proposal

    def update(self, instance, validated_data):
        products_ids = validated_data.pop('products_ids', None)
        proposal = super().update(instance, validated_data)

        if products_ids is not None:
            SaleProduct.objects.filter(commercial_proposal=proposal).delete()
            self._set_products(proposal, products_ids)

        return proposal

    def _set_products(self, proposal, products_ids):
        products = Product.objects.filter(id__in=products_ids)

        sale_products = []
        for product in products:
            sale_product = SaleProduct(
                commercial_proposal=proposal,
                product=product,
                value=product.product_value,
                reference_value=product.reference_value or product.value,
                cost_value=product.cost_value or 0,
                amount=1 
            )
            sale_products.append(sale_product)

        SaleProduct.objects.bulk_create(sale_products)



class ContractSubmissionSerializer(BaseSerializer):
    class Meta:
        model = ContractSubmission
        fields = '__all__'


class ContractTemplateSerializer(BaseSerializer):
    class Meta:
        model = ContractTemplate
        fields = '__all__'


class ReasonSerializer(BaseSerializer):
    class Meta:
        model = Reason
        fields = '__all__'