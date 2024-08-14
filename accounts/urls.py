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
    # Units
    path("unidades/criar/", BranchCreateView.as_view(), name="branch_create"),
    path("unidades/", BranchListView.as_view(), name="branch_list"),
    path("unidades/<int:pk>/atualizar/", BranchUpdateView.as_view(), name="branch_update"),
    # Departments
    path("departamentos/criar/", DepartmentCreateView.as_view(), name="department_create"),
    path("departamentos/", DepartmentListView.as_view(), name="department_list"),
    path("departamentos/<int:pk>/atualizar/", DepartmentUpdateView.as_view(), name="department_update"),
    # Roles
    path("cargos/criar/", RoleCreateView.as_view(), name="role_create"),
    path("cargos/", RoleListView.as_view(), name="role_list"),
    path("cargos/<int:pk>/atualizar/", RoleUpdateView.as_view(), name="role_update"),
    # Addresses
    path("enderecos/criar/", AddressCreateView.as_view(), name="address_create"),
    path("enderecos/", AddressListView.as_view(), name="address_list"),
    path("enderecos/<int:pk>/atualizar/", AddressUpdateView.as_view(), name="address_update"),
    # Squads
    path('squads/criar/', SquadCreateView.as_view(), name='squad_create'),
    path('squads/', SquadListView.as_view(), name='squad_list'),
    path('squads/<int:pk>/', SquadDetailView.as_view(), name='squad_detail'),
    path('squads/<int:pk>/editar', SquadUpdateView.as_view(), name='squad_update'),
    # API
    path("api/addresses/", addresses_api, name="addresses_api"),
]