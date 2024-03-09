from django.views.generic import TemplateView, ListView, DetailView
from .models import *


class IndexView(TemplateView):
    template_name = "index.html"


class KanbanView(DetailView):
    model = Board
    template_name = "leads_kanban.html"


class TasksView(ListView):
    model = Task
    template_name = "tasks.html"