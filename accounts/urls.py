from django.urls import path, include
from .views import *


app_name = "accounts"
urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("usuarios/criar/", UserCreateView.as_view(), name="user_create"),
    path("usuarios/", UsersListView.as_view(), name="users_list"),
    path("usuarios/<slug:slug>/", UserDetailView.as_view(), name="user_detail"),
    path("usuarios/<slug:slug>/editar/", UserUpdateView.as_view(), name="user_update"),
    path("usuarios/<slug:username>/excluir/", delete_user, name="delete_user"),
    # Permissions
    path("permissoes/criar/", PermissionCreateView.as_view(), name="permission_create"),
    path("permissoes/", PermissionsListView.as_view(), name="permission_list"),
    path("permissoes/<slug:slug>/editar/", PermissionUpdateView.as_view(), name="permission_update"),
    # Groups
    path("perfis/criar/", GroupCreateView.as_view(), name="group_create"),
    path("perfis/", GroupsListView.as_view(), name="group_list"),
    path("perfis/<int:pk>/", GroupDetailView.as_view(), name="group_detail"),
    path("perfis/<int:pk>/editar/", GroupUpdateView.as_view(), name="group_update"),
    # API
    path("api/addresses/", addresses_api, name="addresses_api"),
]