from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth import get_user_model


class UsersListView(ListView):
    model = get_user_model()
    template_name = "accounts/users.html"
    context_object_name = "users"
    paginate_by = 10


class UserDetailView(DetailView):
    model = get_user_model()
    template_name = "accounts/user_detail.html"
    slug_field = "username"


class UserCreateView(CreateView):
    model = get_user_model()
    fields = "__all__"
    template_name = "accounts/user_create.html"
    success_url = reverse_lazy("accounts:users")
    

class UserUpdateView(UpdateView):
    model = get_user_model()
    fields = "__all__"
    template_name = "accounts/user_update.html"
    slug_field = "username"

    def get_success_url(self):
        return self.object.get_absolute_url()