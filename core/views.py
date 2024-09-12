import json
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView
from .models import Board, Column, Task
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "core/index.html"


class BoardList(UserPassesTestMixin, ListView):
    model = Board
    template_name = 'core/boards/board_list.html'
    ordering = ['title']
    paginate_by = 10

    def test_func(self):
        return self.request.user.has_perm('core.view_board')
    
    def get_queryset(self):
        self.queryset = super().get_queryset().filter(is_deleted=False)
        title = self.request.GET.get('title')
        self.queryset = self.queryset.filter(title__icontains=title) if title else self.queryset
        return self.queryset
    
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
                    'owner': task.owner.get_full_name(),
                    'start_date': task.start_date,
                    'due_date': task.due_date,
                    'is_completed_date': task.is_completed_date,
                    'depends_on': [t.id for t in task.depends_on.all()],
                    'is_archived': task.is_archived,
                    'archived_at': task.archived_at,
                    'id_integration': task.id_integration,
                    'url': task.get_absolute_url(),
                    'created_at': task.created_at.strftime('%d/%m/%Y %H:%M'),
                }
                column_data['tasks'].append(task_data)
            
            board_data['columns'].append(column_data)
        
        return JsonResponse(board_data)
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board does not exist'}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)


class KanbanView(UserPassesTestMixin, DetailView):
    model = Board
    template_name = "core/boards/board_kanban.html"

    def test_func(self):
        return self.request.user.squad_members.filter(boards=self.get_object()).exists() or self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        board = self.get_object()
        column = Column(title=name, board=board)
        column.order = self.get_object().columns.count()
        column.save()
        return redirect('core:board-kanban', pk=board.pk)


class BoardDetailView(UserPassesTestMixin, DetailView):
    model = Board
    template_name = "core/boards/board_detail.html"

    def test_func(self):
        return self.request.user.has_perm('core.view_board')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_view'] = self.request.user.squad_members.filter(boards=self.get_object()).exists()
        return context
    

class BoardCreateView(UserPassesTestMixin, CreateView):
    model = Board
    fields = ['title', 'description', 'branch' ]
    template_name = "core/boards/board_create.html"
    success_url = reverse_lazy("core:board-list")

    def test_func(self):
        return self.request.user.has_perm('core.create_board')


class BoardUpdateView(UserPassesTestMixin, UpdateView):
    model = Board
    fields = "__all__"
    template_name = "core/boards/board_update.html"

    def test_func(self):
        return self.request.user.has_perm('core.change_board')

    def get_success_url(self):
        return self.object.get_absolute_url()


# class MoveCardView(UserPassesTestMixin, View):
#     def post(self, request, table_id, column_id, card_id, *args, **kwargs):
#         card = get_object_or_404(Card, id=card_id)
#         column = get_object_or_404(Column, id=column_id)
#         card.column = column
#         card.save()
#         return JsonResponse({'status': 'success'})


# class CreateCardView(UserPassesTestMixin, View):
#     def post(self, request, pk, column_id, *args, **kwargs):
#         title = request.POST.get('title')
#         column = get_object_or_404(Column, id=column_id)
#         order = column.card_set.count() + 1
#         card = Card(column=column, title=title, order=order)
#         card.save()
#         return JsonResponse({'status': 'success', 'card_id': card.id})


# class DeleteCardView(UserPassesTestMixin, View):
#     def post(self, request, pk, column_id, card_id, *args, **kwargs):
#         card = get_object_or_404(Card, id=card_id)
#         card.delete()
#         return JsonResponse({'status': 'success'})


class CreateColumnView(UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.has_perm('core.add_column')

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        board_id = data.get('board_id')
        title = data.get('title')
        order = data.get('order', 0)

        board = get_object_or_404(Board, id=board_id)
        column = Column.objects.create(board=board, title=title, order=order)

        return JsonResponse({
            'id': column.id,
            'title': column.title,
            'order': column.order,
            'created_at': column.created_at,
        })


class UpdateColumnView(UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.has_perm('core.change_column')

    def post(self, request, column_id, *args, **kwargs):
        column = get_object_or_404(Column, id=column_id)
        data = json.loads(request.body)
        column.title = data.get('title', column.title)
        column.order = data.get('order', column.order)
        column.save()

        return JsonResponse({
            'status': 'success',
            'id': column.id,
            'title': column.title,
            'order': column.order,
        })


class DeleteColumnView(UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.has_perm('core.delete_column')
    
    def post(self, request, column_id, *args, **kwargs):
        column = get_object_or_404(Column, id=column_id)
        column.delete()
        return JsonResponse({'status': 'success'})
