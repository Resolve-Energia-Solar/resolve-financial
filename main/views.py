from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
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
    

class TaskDetailView(DetailView):
    model = Task
    template_name = "task_detail.html"


class TaskCreateView(CreateView):
    model = Task
    fields = "__all__"
    template_name = "task_create.html"
    success_url = reverse_lazy("main:tasks")


class TaskUpdateView(UpdateView):
    model = Task
    fields = "__all__"
    template_name = "task_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()
    

class BoardsView(ListView):
    model = Board
    template_name = "boards.html"
    context_object_name = "boards"
    paginate_by = 10


class BoardDetailView(DetailView):
    model = Board
    template_name = "board_detail.html"
    

class BoardCreateView(CreateView):
    model = Board
    fields = "__all__"
    template_name = "board_create.html"
    success_url = reverse_lazy("main:boards")


class BoardUpdateView(UpdateView):
    model = Board
    fields = "__all__"
    template_name = "board_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


