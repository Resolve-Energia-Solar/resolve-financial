from django.urls import path, include
from .views import *


app_name = "accounts"
urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("usuarios/criar/", UserCreateView.as_view(), name="user_create"),
    path("usuarios/", UsersListView.as_view(), name="users_list"),
    path("usuarios/<slug:slug>/", UserDetailView.as_view(), name="user_detail"),
    path("usuarios/<slug:slug>/editar/", UserUpdateView.as_view(), name="user_update"),
    # API
    path("api/addresses/", addresses_api, name="addresses_api"),
]