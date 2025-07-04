import base64
from collections import defaultdict
from datetime import datetime
import io
import json
import json
import os
from PIL import Image, UnidentifiedImageError
from PIL.Image import Resampling

from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML 

from accounts.models import Address, PhoneNumber, User
from api.views import BaseModelViewSet
from core.models import Attachment
from logistics.models import Product
from resolve_crm.models import Lead
from resolve_erp import settings
from .models import (
    Answer,
    BlockTimeAgent,
    Category,
    Deadline,
    Forms,
    FormFile,
    FreeTimeAgent,
    RoofType,
    Route,
    Schedule,
    Service,
    ServiceOpinion,
)
from .serializers import (
    AnswerSerializer,
    BlockTimeAgentSerializer,
    CategorySerializer,
    DeadlineSerializer,
    FormsSerializer,
    FormFileSerializer,
    FreeTimeAgentSerializer,
    RoofTypeSerializer,
    RouteSerializer,
    ScheduleSerializer,
    ServiceOpinionSerializer,
    ServiceSerializer,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.template.loader import render_to_string

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign                        import signers
from pyhanko.sign.fields                 import SigFieldSpec
from pyhanko.sign.general                import (
    load_cert_from_pemder,
    load_private_key_from_pemder
)
from pyhanko.sign.signers import PdfSignatureMetadata
from pyhanko_certvalidator.registry      import SimpleCertificateStore

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter

from PyPDF2 import PdfReader, PdfWriter

class RoofTypeViewSet(BaseModelViewSet):
    queryset = RoofType.objects.all()
    serializer_class = RoofTypeSerializer


class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class DeadlineViewSet(BaseModelViewSet):
    queryset = Deadline.objects.all()
    serializer_class = DeadlineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class ServiceViewSet(BaseModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    @cached_property
    def filterset_fields(self):
        fs = super().filterset_fields
        fs.update(
            {
                "category__name": ["exact"],
            }
        )
        return fs

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            grupos = self.request.user.groups.values_list("id", flat=True)
            qs = qs.filter(groups__id__in=grupos)
        return qs.distinct()


class FormsViewSet(BaseModelViewSet):
    queryset = Forms.objects.all()
    serializer_class = FormsSerializer


class AnswerViewSet(BaseModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


class ScheduleViewSet(BaseModelViewSet):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        qs = Schedule.objects.select_related(
            "customer",
            "final_service_opinion",
            "service_opinion",
            "project",
            "project__sale",
            "project__sale__branch",
            "schedule_creator",
            "schedule_creator__employee",
            "schedule_creator__employee__branch",
            "schedule_agent",
            "schedule_agent__employee",
            "schedule_agent__employee__branch",
            "service",
            "service__category",
            "branch",
            "address",
        ).prefetch_related(
            Prefetch(
                "project__sale__products",
                queryset=Product.objects.select_related("roof_type"),
            ),
            Prefetch("attachments", queryset=Attachment.objects.all()),
            Prefetch("leads", queryset=Lead.objects.select_related("column")),
            Prefetch("products", queryset=Product.objects.select_related("roof_type")),
            Prefetch(
                "parent_schedules",
                queryset=Schedule.objects.select_related("customer", "service"),
            ),
            Prefetch(
                "customer__phone_numbers",
                queryset=PhoneNumber.objects.order_by("-is_main"),
            ),
            Prefetch(
                "customer__addresses",
                queryset=Address.objects.filter(is_deleted=False),
                to_attr="addresses_list",
            ),
        )

        user = self.request.user
        params = self.request.query_params

        if schedule_year := params.get("schedule_date_year"):
            qs = qs.filter(schedule_date__year=schedule_year)

        if schedule_month := params.get("schedule_date_month"):
            qs = qs.filter(schedule_date__month=schedule_month)

        # 1) filtros globais
        if q := params.get("q"):
            qs = qs.filter(
                Q(customer__complete_name__icontains=q)
                | Q(customer__first_document__icontains=q)
                | Q(project__sale__seller__complete_name__icontains=q)
                | Q(schedule_agent__complete_name__icontains=q)
                | Q(protocol__icontains=q)
            )
        if params.get("schedule_agent__isnull") in ("true", "false"):
            qs = qs.filter(
                schedule_agent__isnull=params["schedule_agent__isnull"] == "true"
            )
        if cat := params.get("category__icontains"):
            qs = qs.filter(service__category__name__icontains=cat)
        if cust := params.get("customer__icontains"):
            qs = qs.filter(
                Q(customer__complete_name__icontains=cust)
                | Q(customer__first_document__icontains=cust)
            )
        if opin := params.get("final_services_opnions"):
            qs = qs.filter(final_service_opinion__id__in=opin.split(","))
        if params.get("final_service_is_null") in ("true", "false"):
            qs = qs.filter(
                final_service_opinion__isnull=params["final_service_is_null"] == "true"
            )
        if params.get("service_opnion_is_null") in ("true", "false"):
            qs = qs.filter(
                service_opinion__isnull=params["service_opnion_is_null"] == "true"
            )
        if proj := params.get("project_confirmed"):
            qs = qs.filter(project__id=proj, status="Confirmado")
        if svc := params.get("service"):
            qs = qs.filter(service__id=svc)
        if params.get("customer_project_or") == "true":
            c, p = params.get("customer"), params.get("project")
            if c and p:
                qs = qs.filter(Q(customer=c) | Q(project=p))

        # 2) vê tudo?
        if params.get("view_all") == "true" or user.has_perm(
            "field_services.view_all_schedule"
        ):
            return qs

        # 3) branches do usuário
        branch_ids = []
        if hasattr(user, "employee"):
            branch_ids += list(user.employee.related_branches.values_list('id', flat=True))
        branch_ids += list(user.branch_owners.values_list('id', flat=True))
        branch_ids = list(set(branch_ids))

        # 4) filtro único (mantém select/prefetch)
        perms = (
            Q(schedule_creator=user)
            | Q(schedule_agent=user)
            | Q(project__sale__seller=user)
        )
        if branch_ids:
            perms |= Q(schedule_creator__employee__branch_id__in=branch_ids) | Q(
                project__sale__branch_id__in=branch_ids
            )

        return qs.filter(perms).distinct()

    # @method_decorator(cache_page(60 * 5))
    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())

    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serialized_data = self.get_serializer(page, many=True).data
    #         return self.get_paginated_response(serialized_data)

    #     serialized_data = self.get_serializer(queryset, many=True).data
    #     return Response(serialized_data)

    def perform_update(self, serializer):
        instance = self.get_object()
        if (
            instance.final_service_opinion is None
            and serializer.validated_data.get("final_service_opinion") is not None
        ):
            serializer.save(final_service_opinion_user=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=["get"])
    def get_timeline(self, request):
        date = datetime.now().date()
        hours = [
            ("09:00", "10:30"),
            ("10:30", "12:00"),
            ("13:00", "14:30"),
            ("14:30", "16:00"),
            ("16:00", "17:30"),
            ("17:30", "19:00"),
        ]

        date_param = request.query_params.get("date")
        agent_param = request.query_params.get("agent")

        if date_param:
            date = parse_datetime(date_param).date()

        if agent_param:
            agents_qs = User.objects.filter(
                complete_name__icontains=agent_param, user_types__name="agent"
            )
        else:
            agents_qs = User.objects.filter(user_types__name="agent")

        agents = agents_qs.values_list("id", flat=True)
        agent_objs = agents_qs.in_bulk()

        schedules = Schedule.objects.filter(
            schedule_date=date, schedule_agent_id__in=agents
        )

        schedules_by_agent = defaultdict(list)
        for s in schedules:
            schedules_by_agent[s.schedule_agent_id].append(s)

        blocks = BlockTimeAgent.objects.filter(agent_id__in=agents, start_date=date)

        blocks_by_agent = defaultdict(list)
        for b in blocks:
            blocks_by_agent[b.agent_id].append(b)

        data = []

        for agent_id in agents:
            agent = agent_objs.get(agent_id)
            if not agent:
                continue

            agent_data = {
                "agent": {
                    "id": agent.id,
                    "name": agent.complete_name,
                },
                "schedules": [],
            }

            agent_schedules = schedules_by_agent.get(agent_id, [])
            agent_blocks = blocks_by_agent.get(agent_id, [])

            for start, end in hours:
                ocupado = any(
                    s.schedule_start_time.strftime("%H:%M") < end
                    and s.schedule_end_time.strftime("%H:%M") > start
                    for s in agent_schedules
                )
                if ocupado:
                    status_ = "Ocupado"
                else:
                    bloqueado = any(
                        b.start_time.strftime("%H:%M") < end
                        and b.end_time.strftime("%H:%M") > start
                        for b in agent_blocks
                    )
                    status_ = "Bloqueado" if bloqueado else "Livre"

                agent_data["schedules"].append(
                    {"start_time": start, "end_time": end, "status": status_}
                )

            data.append(agent_data)

        return Response(data, status=status.HTTP_200_OK)


class BlockTimeAgentViewSet(BaseModelViewSet):
    queryset = BlockTimeAgent.objects.all()
    serializer_class = BlockTimeAgentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        agent = self.request.query_params.get("agent")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if agent:
            queryset = queryset.filter(agent__id=agent)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        return queryset


class FreeTimeAgentViewSet(BaseModelViewSet):
    queryset = FreeTimeAgent.objects.all()
    serializer_class = FreeTimeAgentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        agent = self.request.query_params.get("agent")
        day_of_week = self.request.query_params.get("day_of_week")

        if agent:
            queryset = queryset.filter(agent__id=agent)
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)

        return queryset


class FormFileViewSet(BaseModelViewSet):
    queryset = FormFile.objects.all()
    serializer_class = FormFileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        answer = self.request.query_params.get("answer")
        field_id = self.request.query_params.get("field_id")

        if answer:
            queryset = queryset.filter(answer__id=answer)
        if field_id:
            queryset = queryset.filter(field_id=field_id)

        return queryset


class ServiceOpinionViewSet(BaseModelViewSet):
    queryset = ServiceOpinion.objects.all()
    serializer_class = ServiceOpinionSerializer


class RouteViewSet(BaseModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


def compress_image(fieldfile, max_w=600, quality=50):
    fieldfile.open()
    img = Image.open(fieldfile)
    if img.width > max_w:
        h = int(max_w * img.height / img.width)
        img = img.resize((max_w, h), Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{data}"

class GenerateSchedulePDF(APIView):
    def get(self, request, pk):
        schedule = get_object_or_404(Schedule, pk=pk)
        answers  = Answer.objects.filter(schedule=schedule, is_deleted=False)
        fields   = json.loads(schedule.service.form.fields or '[]')

        # Cria dicionário de labels e lista de fields para fallback
        labels = {f"{f['type']}-{f['id']}": f['label'] for f in fields}
        options_map = {f"select-{f['id']}": {opt['value']:opt['label'] for opt in f.get('options',[])}
                       for f in fields if f['type']=='select'}

        # Separa imagens e campos PDF
        files_qs = FormFile.objects.filter(answer__in=answers, is_deleted=False)
        img_map, pdf_fields = {}, []
        for f in files_qs:
            name = f.file.name.lower()
            if name.endswith('.pdf'):
                pdf_fields.append(f)
            else:
                try:
                    # tenta abrir como imagem
                    f.file.open()
                    Image.open(f.file).verify()
                    uri = compress_image(f.file)
                    img_map.setdefault((f.answer_id, f.field_id), []).append(uri)
                except UnidentifiedImageError:
                    # não é imagem nem pdf -> ignora
                    continue

        attachment_labels = [labels.get(f"file-{pf.field_id}", pf.field_id) for pf in pdf_fields]

        # Monta resposta com fallback de label
        resp_list = []
        for ans in answers:
            items = []
            for key, val in (ans.answers or {}).items():
                # Resolve label: primeiro do dict, depois busca em fields
                if key in labels:
                    label = labels[key]
                else:
                    parts = key.split('-',1)
                    if len(parts)==2:
                        ftype, fid = parts
                        found = next((f for f in fields if f['type']==ftype and f['id']==fid), None)
                        label = found['label'] if found else key
                    else:
                        label = key
                # Processa valor ou imagens
                if key.startswith('file'):
                    imgs = img_map.get((ans.id, key), [])
                    if imgs:
                        items.append({'label': label, 'images': imgs})
                elif key.startswith('select'):
                    vals = val if isinstance(val,list) else [val]
                    disp = ", ".join(options_map.get(key,{}).get(v,v) for v in vals)
                    items.append({'label': label, 'value': disp})
                else:
                    items.append({'label': label, 'value': val})
            resp_list.append({'items': items})

        # Renderiza HTML e gera PDF
        html = render_to_string('schedule_pdf.html', {
            'schedule': schedule,
            'resp_list': resp_list,
            'pdf_requester': request.user.complete_name.title(),
        })
        html = html.replace('<head>', '<head><meta charset="utf-8"/>')
        pdf_bytes = HTML(string=html).write_pdf()

        # Anexa PDFs como páginas de apêndice com watermark de label
        if pdf_fields:
            writer = PdfWriter()
            main_reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in main_reader.pages:
                writer.add_page(page)
            for pf, label in zip(pdf_fields, attachment_labels):
                with pf.file.open('rb') as stream:
                    attach_reader = PdfReader(stream)
                    for page in attach_reader.pages:
                        # desenha watermark do label
                        buf_wm = io.BytesIO()
                        width = float(page.mediabox.upper_right[0])
                        height = float(page.mediabox.upper_right[1])
                        c = Canvas(buf_wm, pagesize=(width, height))
                        c.setFont("Helvetica", 10)
                        c.drawString(40, 30, label)
                        c.save()
                        buf_wm.seek(0)
                        wm = PdfReader(buf_wm).pages[0]
                        page.merge_page(wm)
                        writer.add_page(page)
            buf_out = io.BytesIO()
            writer.write(buf_out)
            pdf_bytes = buf_out.getvalue()

        # Assinatura digital
        pem = settings.SIGN_PEM
        if pem and os.path.exists(pem):
            cert = load_cert_from_pemder(pem)
            key  = load_private_key_from_pemder(pem, None)
            signer = signers.SimpleSigner(
                signing_cert=cert,
                signing_key=key,
                cert_registry=SimpleCertificateStore()
            )
            meta = PdfSignatureMetadata(
                field_name='Resolve Energia Solar',
                reason='Assinado digitalmente pelo sistema',
                location='Belém-PA'
            )
            spec = SigFieldSpec(sig_field_name='Resolve Energia Solar', box=(40,40,200,100), on_page=0)
            in_buf = io.BytesIO(pdf_bytes)
            writer_inc = IncrementalPdfFileWriter(in_buf)
            out_buf = io.BytesIO()
            signers.sign_pdf(
                writer_inc, meta, signer,
                new_field_spec=spec, existing_fields_only=False,
                output=out_buf
            )
            pdf_bytes = out_buf.getvalue()

        filename = f"agendamento_{schedule.protocol}_{datetime.now():%Y%m%d%H%M%S}.pdf"
        return HttpResponse(
            pdf_bytes,
            content_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
