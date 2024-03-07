from django.views.generic import ListView
from django.contrib.auth import get_user_model


class UsersListView(ListView):
    model = get_user_model()
    template_name = "accounts/users.html"

