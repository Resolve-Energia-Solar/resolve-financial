from django.forms import ValidationError
from core.serializers import AttachmentSerializer
from financial.models import FranchiseInstallment
from resolve_crm.models import *
from accounts.serializers import AddressSerializer
from api.serializers import BaseSerializer
from logistics.models import Materials, ProjectMaterials, Product, SaleProduct
from rest_framework.serializers import SerializerMethodField, ListField, DictField
import re
from rest_framework import serializers
class OriginSerializer(BaseSerializer):
    class Meta:
        model = Origin
        fields = '__all__'
      

 
class LeadSerializer(BaseSerializer):
    proposals = SerializerMethodField()
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
    child=serializers.IntegerField(), write_only=True, required=False
    )

    commercial_proposal_id = serializers.IntegerField(write_only=True, required=False)
    
    documents_under_analysis = SerializerMethodField()
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    final_service_opinion = SerializerMethodField()
    signature_status = SerializerMethodField()
    is_released_to_engineering = SerializerMethodField()

    class Meta:
        model = Sale
        fields = '__all__'
    
    def get_documents_under_analysis(self, obj):
        attachments = getattr(obj, 'attachments_under_analysis', [])
        return AttachmentSerializer(attachments, many=True, context=self.context).data


    def get_is_released_to_engineering(self, obj):
        return any(
            getattr(p, 'is_released_to_engineering', False)
            for p in obj.projects.all()
        )

    
    def get_signature_status(self, obj):
        submissions = list(obj.contract_submissions.all())
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
        opinions = [
            {
                "id": p.inspection.final_service_opinion.id,
                "name": p.inspection.final_service_opinion.name
            }
            for p in obj.projects.all()
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
        sale = super().create(validated_data)

        print('criando venda com produtos:', products)
        if commercial_proposal_id:
            self._handle_products(sale, commercial_proposal_id=commercial_proposal_id)
        else:
            self._handle_products(sale, products_ids=products)
            
        return sale

    def update(self, instance, validated_data):
        # Atualizar os campos restantes
        cancellation_reasons = validated_data.pop('cancellation_reasons', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if cancellation_reasons is not None:
            instance.cancellation_reasons.set(cancellation_reasons)

        return instance

    def _handle_products(self, sale, products_ids=None, commercial_proposal_id=None):
        products_list = []

        if commercial_proposal_id:
            try:
                commercial_proposal = ComercialProposal.objects.get(id=commercial_proposal_id)
                sale_products = SaleProduct.objects.filter(commercial_proposal=commercial_proposal)

                if not sale_products.exists():
                    raise ValidationError({"detail": "Proposta comercial não possui produtos associados."})

                if sale_products.filter(sale__isnull=False).exists():
                    raise ValidationError({"detail": "Proposta comercial já vinculada a uma venda."})

                for sale_product in sale_products:
                    sale_product.sale = sale
                    sale_product.save()
                    products_list.append(sale_product)

            except ComercialProposal.DoesNotExist:
                raise ValidationError({"detail": "Proposta comercial não encontrada."})
        
        elif products_ids:
            validated_products = self.validate_products_ids(products_ids)
            print(validated_products)
            sale_products = [
                SaleProduct(
                    sale=sale,
                    product=product,
                    value=product.cost_value or 0,
                    amount=1
                )
                for product in validated_products
            ]
            SaleProduct.objects.bulk_create(sale_products)
            products_list.extend(sale_products)
                

        self.create_projects(sale, products_list)

        if sale.total_value is None or sale.total_value == 0:
            total_value = self.calculate_total_value(products_list)
            sale.total_value = total_value
            sale.save()

        if sale.sale_products.exists():
            total_installment_value = self.calculate_total_installment_value(sale, sale.sale_products.all())
            if sale.total_value:
                FranchiseInstallment.objects.create(
                    sale=sale,
                    installment_value=total_installment_value,
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
    is_released_to_engineering = serializers.SerializerMethodField()
    documents_under_analysis = serializers.SerializerMethodField()
    access_opnion = serializers.SerializerMethodField()
    trt_pending = serializers.SerializerMethodField()
    trt_status = serializers.SerializerMethodField()
    request_requested = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    materials_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = '__all__'

    def get_is_released_to_engineering(self, obj):
        return obj.is_released_to_engineering

    def get_documents_under_analysis(self, obj):
        documents = obj.documents_under_analysis[:10]
        return [{"id": d.id, "name": d.document_type.name, "status": d.status} for d in documents]


    def get_access_opnion(self, obj):
        return obj.access_opnion

    def get_trt_pending(self, obj):
        return obj.trt_pending

    def get_trt_status(self, obj):
        return obj.trt_status

    def get_request_requested(self, obj):
        return obj.request_requested

    def get_address(self, obj):
        main_unit = obj.main_unit_prefetched[0] if hasattr(obj, 'main_unit_prefetched') and obj.main_unit_prefetched else None
        return AddressSerializer(main_unit.address).data if main_unit and main_unit.address else None


    
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
    class Meta:
        model = ComercialProposal
        fields = '__all__'

    def create(self, validated_data):
        products_data = validated_data.pop('commercial_products', [])
        proposal = super().create(validated_data)
        for product in products_data:
            SaleProduct.objects.create(
                commercial_proposal=proposal,
                product=product,
                amount=1,
                cost_value=product.cost_value,
                reference_value=product.reference_value,
                value = product.product_value
            )

        return proposal

    def update(self, instance, validated_data):
        products_data = validated_data.pop('commercial_products', [])
        proposal = super().update(instance, validated_data)

        SaleProduct.objects.filter(commercial_proposal=instance).delete()

        for product in products_data:
            SaleProduct.objects.create(
                commercial_proposal=proposal,
                product=product,
                amount=1,
                cost_value=product.cost_value,
                reference_value=product.reference_value, 
                value = product.product_value
            )

        return proposal


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