from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView
from .models import Board
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "core/index.html"


class BoardList(LoginRequiredMixin, ListView):
    model = Board
    template_name = 'core/boards/board_list.html'
    context_object_name = 'boards'
    paginate_by = 10


class BoardDetailView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = "core/boards/board_detail.html"
    

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