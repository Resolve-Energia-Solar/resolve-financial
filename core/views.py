from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView
from .models import Board, Column, Task
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "core/index.html"


class BoardList(LoginRequiredMixin, ListView):
    model = Board
    template_name = 'core/boards/board_list.html'
    context_object_name = 'boards'
    paginate_by = 10


def board_api(request, pk):
    try:
        board = Board.objects.get(pk=pk)
        columns = board.columns.all()
        
        board_data = {
            'id': board.id,
            'title': board.title,
            'description': board.description,
            'columns': [],
        }
        
        for column in columns:
            column_data = {
                'id': column.id,
                'title': column.title,
                'tasks': [],
            }
            
            tasks = Task.objects.filter(column=column)
            for task in tasks:
                task_data = {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    # 'owner': task.owner.username,
                    'start_date': task.start_date,
                    'due_date': task.due_date,
                    'is_completed_date': task.is_completed_date,
                    'depends_on': [t.id for t in task.depends_on.all()],
                    'is_archived': task.is_archived,
                    'archived_at': task.archived_at,
                    'id_integration': task.id_integration,
                }
                column_data['tasks'].append(task_data)
            
            board_data['columns'].append(column_data)
        
        return JsonResponse(board_data)
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class KanbanView(DetailView):
    model = Board
    template_name = "core/boards/board_kanban.html"
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        board = self.get_object()
        column = Column(title=name, board=board)
        column.order = self.get_object().columns.count()
        column.save()
        return redirect('core:board-detail', pk=board.pk)
    

class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board
    fields = "__all__"
    template_name = "core/boards/board_create.html"
    success_url = reverse_lazy("core:board-list")


class BoardUpdateView(LoginRequiredMixin, UpdateView):
    model = Board
    fields = "__all__"
    template_name = "core/boards/board_update.html"

    def get_success_url(self):
        return self.object.get_absolute_url()