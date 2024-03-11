from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.contrib.auth import get_user_model


class UsersListView(ListView):
    model = get_user_model()
    template_name = "accounts/users.html"
    context_object_name = "users"
    paginate_by = 10


class UserCreateView(CreateView):
    model = get_user_model()
    fields = "__all__"
    template_name = "accounts/user_create.html"
    success_url = reverse_lazy("accounts:users")