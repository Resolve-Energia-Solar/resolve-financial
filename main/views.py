from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.db.models import F
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from .models import *


class IndexView(TemplateView):
    template_name = "index.html"


class KanbanView(DetailView):
    model = Board
    template_name = "leads_kanban.html"
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        board = self.get_object()
        column = Column(name=name, board=board)
        column.order = self.get_object().column_set.count()
        column.save()
        return redirect('main:board-detail', pk=board.pk)


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


class MoveCardView(View):
    def post(self, request, table_id, column_id, card_id, *args, **kwargs):
        card = get_object_or_404(Card, id=card_id)
        column = get_object_or_404(Column, id=column_id)
        card.column = column
        card.save()
        return JsonResponse({'status': 'success'})


class CreateCardView(View):
    def post(self, request, pk, column_id, *args, **kwargs):
        title = request.POST.get('title')
        column = get_object_or_404(Column, id=column_id)
        order = column.card_set.count() + 1
        card = Card(column=column, title=title, order=order)
        card.save()
        return JsonResponse({'status': 'success', 'card_id': card.id})


class DeleteCardView(View):
    def post(self, request, pk, column_id, card_id, *args, **kwargs):
        card = get_object_or_404(Card, id=card_id)
        card.delete()
        return JsonResponse({'status': 'success'})


class DeleteColumnView(View):
    def post(self, request, column_id, *args, **kwargs):
        column = get_object_or_404(Column, id=column_id)
        column.delete()
        return JsonResponse({'status': 'success'})