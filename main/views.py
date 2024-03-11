from django.views.generic import TemplateView, ListView, DetailView, CreateView
from .models import *


class IndexView(TemplateView):
    template_name = "index.html"


class KanbanView(DetailView):
    model = Board
    template_name = "leads_kanban.html"


class TasksView(ListView):
    model = Task
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 10


class TaskCreateView(CreateView):
    model = Task
    fields = "__all__"
    template_name = "task_create.html"
    success_url = reverse_lazy("main:tasks")