from django.urls import reverse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import JsonResponse
from django.views import View
from .forms import LeadForm, TaskForm
from django.shortcuts import get_object_or_404, redirect
from .models import *


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "main/index.html"


class KanbanView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = "main/leads/leads_kanban.html"
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        board = self.get_object()
        column = Column(name=name, board=board)
        column.order = self.get_object().column_set.count()
        column.save()
        return redirect('main:board-detail', pk=board.pk)


class TasksView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "main/tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10
    

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "main/tasks/task_detail.html"


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "main/tasks/task_create.html"
    success_url = reverse_lazy("main:tasks")


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = "__all__"
    template_name = "main/tasks/task_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class BoardsView(LoginRequiredMixin, ListView):
    model = Board
    template_name = "main/boards/board_list.html"
    context_object_name = "boards"
    paginate_by = 10


class BoardDetailView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = "main/boards/board_detail.html"
    

class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board
    fields = "__all__"
    template_name = "main/boards/board_create.html"
    success_url = reverse_lazy("main:boards")


class BoardUpdateView(LoginRequiredMixin, UpdateView):
    model = Board
    fields = "__all__"
    template_name = "main/boards/board_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class MoveCardView(LoginRequiredMixin, View):
    def post(self, request, table_id, column_id, card_id, *args, **kwargs):
        card = get_object_or_404(Card, id=card_id)
        column = get_object_or_404(Column, id=column_id)
        card.column = column
        card.save()
        return JsonResponse({'status': 'success'})


class CreateCardView(LoginRequiredMixin, View):
    def post(self, request, pk, column_id, *args, **kwargs):
        title = request.POST.get('title')
        column = get_object_or_404(Column, id=column_id)
        order = column.card_set.count() + 1
        card = Card(column=column, title=title, order=order)
        card.save()
        return JsonResponse({'status': 'success', 'card_id': card.id})


class DeleteCardView(LoginRequiredMixin, View):
    def post(self, request, pk, column_id, card_id, *args, **kwargs):
        card = get_object_or_404(Card, id=card_id)
        card.delete()
        return JsonResponse({'status': 'success'})


class DeleteColumnView(LoginRequiredMixin, View):
    def post(self, request, column_id, *args, **kwargs):
        column = get_object_or_404(Column, id=column_id)
        column.delete()
        return JsonResponse({'status': 'success'})


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "main/leads/lead_form.html"
    
    def get_success_url(self):
        return reverse("main:lead_detail", kwargs={"pk": self.object.pk})


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "main/leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 10


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = "main/leads/lead_detail.html"


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "main/leads/lead_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()
