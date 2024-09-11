from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import LeadForm, TaskForm, MarketingCampaignForm
from django.contrib import messages
from .models import *


class TasksView(UserPassesTestMixin, ListView):
    model = Task
    template_name = "resolve_crm/tasks/task_list.html"
    ordering = ['-created_at']
    paginate_by = 10

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_task')


class TaskDetailView(UserPassesTestMixin, DetailView):
    model = Task
    template_name = "resolve_crm/tasks/task_detail.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_task')


class TaskCreateView(UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "resolve_crm/tasks/task_create.html"
    success_url = reverse_lazy("resolve_crm:tasks")

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.create_task')


class TaskUpdateView(UserPassesTestMixin, UpdateView):
    model = Task
    fields = "__all__"
    template_name = "resolve_crm/tasks/task_update.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.change_task')

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class LeadCreateView(UserPassesTestMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "resolve_crm/leads/lead_form.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.create_lead')
    
    def get_success_url(self):
        return reverse("resolve_crm:lead_detail", kwargs={"pk": self.object.pk})


class LeadListView(UserPassesTestMixin, ListView):
    model = Lead
    template_name = "resolve_crm/leads/lead_list.html"
    ordering = ['-created_at']
    paginate_by = 10

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_lead')


class LeadDetailView(UserPassesTestMixin, DetailView):
    model = Lead
    template_name = "resolve_crm/leads/lead_detail.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_lead')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.get_object()
        history = lead.history.all().order_by('-history_date')

        for record in history:
            changes = []
            old_record = lead.history.filter(history_date__lt=record.history_date).first()
            if old_record:
                delta = record.diff_against(old_record)
                for change in delta.changes:
                    changes.append({
                        'field': change.field,
                        'old': change.old,
                        'new': change.new,
                        'user': record.history_user,
                        'date': record.history_date
                    })
            record.get_changes = changes

        context['history'] = history
        
        return context


class LeadUpdateView(UserPassesTestMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "resolve_crm/leads/lead_form.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.change_task')

    def get_success_url(self):
        return self.object.get_absolute_url()


class MarketingCampaignCreateView(UserPassesTestMixin, CreateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_form.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.create_marketingcampaign')
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class MarketingCampaignListView(UserPassesTestMixin, ListView):
    model = MarketingCampaign
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_list.html"
    ordering = ['-start_datetime']
    paginate_by = 10

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_marketingcampaign')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset


class MarketingCampaignDetailView(UserPassesTestMixin, DetailView):
    model = MarketingCampaign
    template_name = "resolve_crm/templates/resolve_crm/marketing_campaings/marketing_campaign_form.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.view_marketingcampaign')


class MarketingCampaignUpdateView(UserPassesTestMixin, UpdateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_form.html"

    def test_func(self):
        return self.request.user.has_perm('resolve_crm.change_marketingcampaign')

    def get_success_url(self):
        return self.object.get_absolute_url()


# class ComercialProposalDetailView(UserPassesTestMixin, DetailView):
#     model = ComercialProposal
#     template_name = 'resolve_crm/proposal/proposal_detail.html'

#     def test_func(self):
#         return self.request.user.has_perm('resolve_crm.view_comercialproposal')


def add_lead_attachment(request, lead_id):
    lead = Lead.objects.get(pk=lead_id)

    if request.method == 'POST':
        file = request.FILES.get('attachment')
        if file:
            attachment = Attachment()
            attachment.file = file
            attachment.object_id = lead.id
            attachment.content_type = ContentType.objects.get_for_model(lead)
            attachment.save()
            messages.success(request, 'Anexo adicionado com sucesso!')
            return redirect('resolve_crm:lead_detail', pk=lead_id)
        messages.error(request, 'Erro ao adicionar anexo!')
        return redirect('resolve_crm:lead_detail', pk=lead_id)
    
    else:
        messages.error(request, 'Erro na requisição!')
        return redirect('resolve_crm:lead_detail', pk=lead_id)


def delete_attachment(request, id):
    attachment = Attachment.objects.get(pk=id)
    object_id = attachment.object_id
    get_object = attachment.content_type.get_object_for_this_type(id=object_id)
    attachment.delete()
    messages.success(request, 'Anexo deletado com sucesso!')
    return redirect(get_object.get_absolute_url())
