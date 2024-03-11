from django.urls import path, include
from .views import *


app_name = "accounts"
urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("usuarios/", UsersListView.as_view(), name="users_list"),
    path("usuarios/criar/", UserCreateView.as_view(), name="user_create"),
]