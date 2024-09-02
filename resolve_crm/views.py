from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import LeadForm, TaskForm, MarketingCampaignForm
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
