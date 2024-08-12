from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LeadForm, TaskForm, MarketingCampaignForm
from .models import *


class TasksView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "resolve_crm/tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10
    

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "resolve_crm/tasks/task_detail.html"


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "resolve_crm/tasks/task_create.html"
    success_url = reverse_lazy("resolve_crm:tasks")


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = "__all__"
    template_name = "resolve_crm/tasks/task_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "resolve_crm/leads/lead_form.html"
    
    def get_success_url(self):
        return reverse("resolve_crm:lead_detail", kwargs={"pk": self.object.pk})


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "resolve_crm/leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 10


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = "resolve_crm/leads/lead_detail.html"


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "resolve_crm/leads/lead_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class MarketingCampaignCreateView(LoginRequiredMixin, CreateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_form.html"
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class MarketingCampaignListView(LoginRequiredMixin, ListView):
    model = MarketingCampaign
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_list.html"
    context_object_name = "campaigns"
    paginate_by = 10
    ordering = ['-start_datetime']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset


class MarketingCampaignDetailView(LoginRequiredMixin, DetailView):
    model = MarketingCampaign
    template_name = "resolve_crm/templates/resolve_crm/marketing_campaings/marketing_campaign_form.html"


class MarketingCampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = "resolve_crm/marketing_campaings/marketing_campaign_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class ComercialProposalDetailView(LoginRequiredMixin, DetailView):
    model = ComercialProposal
    template_name = 'resolve_crm/proposal/proposal_detail.html'
