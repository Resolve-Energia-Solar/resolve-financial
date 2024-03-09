from django.views.generic import TemplateView, DetailView
from .models import *


class IndexView(TemplateView):
    template_name = "index.html"


class KanbanView(DetailView):
    model = Board
    template_name = "leads_kanban.html"


class TaskView(DetailView):
    model = Task
    template_name = "tasks.html"