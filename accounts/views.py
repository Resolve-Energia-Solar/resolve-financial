import json
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Address, Branch, Department, Role, Squad, UserType
from .forms import BranchForm, SquadForm, UserForm, UserUpdateForm, GroupForm, AddressForm
from django.contrib.contenttypes.models import ContentType

class UsersListView(UserPassesTestMixin, ListView):
    model = get_user_model()
    template_name = "accounts/users/user_list.html"
    paginate_by = 10
    ordering = ['username']
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_user')
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        search_query = self.request.GET.get('search')
        department_id = self.request.GET.get('department')

        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) | 
                Q(first_name__icontains=search_query) |  
                Q(last_name__icontains=search_query)
            )
            
        if department_id:
            queryset = queryset.filter(department=department_id)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context

class UserDetailView(UserPassesTestMixin, DetailView):
    model = get_user_model()
    template_name = "accounts/users/user_detail.html"
    slug_field = "username"
    context_object_name = "user_obj"
    
    def test_func(self):
        user = self.request.user
        return user.username == self.get_object().username or user.has_perm('accounts.view_user')


class UserCreateView(UserPassesTestMixin, CreateView):
    model = get_user_model()
    form_class = UserForm
    template_name = "accounts/users/user_create.html"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.add_user')
    
    def form_valid(self, form):
        # Generate a random password
        password = get_user_model().objects.make_random_password()
        
        # Set the generated password for the user
        user = form.save(commit=False)
        user.set_password(password)
        # Save the user first to generate the user ID

        # Get the address_id from the POST data
        address_id = self.request.POST.get('address')
        if address_id:
            try:
                address = Address.objects.get(id=address_id)
                user.address = address
            except Address.DoesNotExist:
                form.add_error('address', 'Endereço inválido. Por favor, selecione um endereço válido.')
                return self.form_invalid(form)
        
        user.save()
        
        # Send an email to the user with the username and password
        send_mail(
            subject="Conta criada",
            message=f"Nome de usuário: {user.username}\nSenha: {password}\n\nAcesse em http://127.0.0.1:31813/",
            from_email='ti@resolvenergiasolar.com',
            recipient_list=[user.email],
        )

        # Now that the user has an ID, set the ManyToMany relationship
        funcionario_type = UserType.objects.get(id=3)
        user.user_types.set([funcionario_type])
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            field_object = form.fields[field]
            for error in errors:
                messages.error(self.request, f"Erro no campo {field_object.label}: {error} Por favor, corrija o erro e tente novamente.")
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    

class UserUpdateView(UserPassesTestMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "accounts/users/user_update.html"
    slug_field = "username"
    context_object_name = "user_obj"
    
    def test_func(self):
        user = self.request.user
        return user.username == self.get_object().username or user.has_perm('accounts.change_user')

    def get_success_url(self):
        return self.object.get_absolute_url()
    

def create_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        
        # Supondo que o nome completo seja armazenado no campo `first_name`
        user = get_user_model().objects.create_user(username=email, first_name=name, email=email)
        
        messages.success(request, 'Cliente criado com sucesso!')
        return redirect('resolve_crm:lead_detail')


class PermissionCreateView(UserPassesTestMixin, CreateView):
    model = Permission
    fields = ['name', 'content_type', 'codename']
    template_name = "accounts/permissions/permission_form.html"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.add_permission')
    
    def get_success_url(self):
        return reverse_lazy("accounts:permission_list")


class PermissionsListView(UserPassesTestMixin, ListView):
    model = Permission
    template_name = "accounts/permissions/permission_list.html"
    paginate_by = 10
    ordering = ['content_type', 'codename']
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_permission')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset


class PermissionUpdateView(UserPassesTestMixin, UpdateView):
    model = Permission
    fields = ['name', 'content_type', 'codename']
    template_name = "accounts/permissions/permission_form.html"
    slug_field = "codename"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.change_permission')
    
    def get_success_url(self):
        return reverse_lazy("accounts:permission_list")


class GroupCreateView(UserPassesTestMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "accounts/groups/group_form.html"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.add_group')
    
    def get_success_url(self):
        return reverse_lazy("accounts:group_list")


class GroupsListView(UserPassesTestMixin, ListView):
    model = Group
    template_name = "accounts/groups/group_list.html"
    ordering = ['name']
    paginate_by = 10
    
    def get_queryset(self):
        return super().get_queryset()
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_group')


class GroupDetailView(UserPassesTestMixin, DetailView):
    model = Group
    template_name = "accounts/groups/group_detail.html"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_group')


class GroupUpdateView(UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "accounts/groups/group_form.html"
    slug_field = "codename"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.change_group')
    
    def get_success_url(self):
        return reverse_lazy("accounts:group_detail", kwargs={"pk": self.object.pk})


class BranchCreateView(UserPassesTestMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'accounts/branches/branch_form.html'
    success_url = reverse_lazy('accounts:branch_list')
    
    def test_func(self):
        return self.request.user.has_perm('accounts.add_branch')
    
    # def get_success_url(self):
        # return reverse_lazy('branch_detail', kwargs={"pk": self.object.pk})


class BranchListView(UserPassesTestMixin, ListView):
    model = Branch
    template_name = "accounts/branches/branch_list.html"
    ordering = ['name']
    paginate_by = 10 
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    

    def test_func(self):
        return self.request.user.has_perm('accounts.view_branch')


class BranchDetailView(UserPassesTestMixin, DetailView):
    model = Branch
    template_name = "accounts/branches/branch_detail.html"
    context_object_name = "branch"

    def test_func(self):
        return self.request.user.has_perm('accounts.view_branch')


class BranchUpdateView(UserPassesTestMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'accounts/branches/branch_form.html'
    success_url = reverse_lazy('accounts:branch_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.change_branch')
    
    # def get_success_url(self):
        # return reverse_lazy('branch_detail', kwargs={"pk": self.object.pk})


class DepartmentCreateView(UserPassesTestMixin, CreateView):
    model = Department
    fields = '__all__'
    template_name = "accounts/departments/department_form.html"
    success_url = reverse_lazy('accounts:department_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.add_department')


class DepartmentListView(UserPassesTestMixin, ListView):
    model = Department
    template_name = "accounts/departments/department_list.html"
    ordering = ['name']
    paginate_by = 10
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_department')


class DepartmentUpdateView(UserPassesTestMixin, UpdateView):
    model = Department
    fields = '__all__'
    template_name = "accounts/departments/department_form.html"
    success_url = reverse_lazy('accounts:department_list')
    
    def test_func(self):
        return self.request.user.has_perm('accounts.change_department')


class RoleCreateView(UserPassesTestMixin, CreateView):
    model = Role
    fields = ['name',]
    template_name = "accounts/roles/role_form.html"
    success_url = reverse_lazy('accounts:role_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.add_role')


class RoleListView(UserPassesTestMixin, ListView):
    model = Role
    template_name = "accounts/roles/role_list.html"
    ordering = ['name']
    paginate_by = 10
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_role')


class RoleUpdateView(UserPassesTestMixin, UpdateView):
    model = Role
    fields = ('name',)
    template_name = "accounts/roles/role_form.html"
    success_url = reverse_lazy('accounts:role_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.change_role')


class AddressCreateView(UserPassesTestMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = "accounts/address/address_form.html"
    success_url = reverse_lazy('accounts:address_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.add_address')


class AddressListView(UserPassesTestMixin, ListView):
    model = Address
    template_name = "accounts/address/address_list.html"
    ordering = ['street']
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(street__icontains=search_query)

        return queryset

    def test_func(self):
        return self.request.user.has_perm('accounts.view_address')


class AddressUpdateView(UserPassesTestMixin, UpdateView):
    model = Address
    fields = ['street', 'city', 'state', 'zip_code', 'country', 'neighborhood', 'number', 'complement']
    template_name = "accounts/address/address_form.html"
    success_url = reverse_lazy('accounts:address_list')

    def test_func(self):
        return self.request.user.has_perm('accounts.change_address')


# API

@csrf_exempt
def addresses_api(request):
    
    if request.method == 'POST':
        # Carrega os dados JSON do corpo da requisição
        data = json.loads(request.body)
        
        # Extrai os dados necessários do JSON
        street = data.get('street')
        city = data.get('city')
        state = data.get('state')
        zip_code = data.get('zip_code')
        country = data.get('country')
        neighborhood = data.get('neighborhood')
        number = data.get('number')
        complement = data.get('complement')
        
        # Validação simples dos dados (exemplo básico, pode ser expandido)
        if not (street and city and state and zip_code and country):
            return JsonResponse({'error': 'Campos obrigatórios não fornecidos.'}, status=400)
        
        # Cria e salva o novo endereço no banco de dados
        new_address = Address(
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            neighborhood=neighborhood,
            number=number,
            complement=complement
        )
        new_address.save()
        
        # Retorna uma resposta JSON com os dados do novo endereço
        return JsonResponse({
            "id": new_address.id,
            "street": new_address.street,
            "city": new_address.city,
            "state": new_address.state,
            "zip_code": new_address.zip_code,
            "country": new_address.country,
            "neighborhood": new_address.neighborhood,
            "number": new_address.number,
            "complement": new_address.complement,
            "complete_address": str(new_address)
        }, status=201)
    else:    
        addresses = Address.objects.all()
        data = [
            {
                "id": address.id,
                "street": address.street,
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
                "country": address.country,
                "neighborhood": address.neighborhood,
                "number": address.number,
                "complement": address.complement,
                "complete_address": str(address)
            } for address in addresses
        ]

        return JsonResponse(data, safe=False)


class SquadCreateView(UserPassesTestMixin, CreateView):
    model = Squad
    form_class = SquadForm
    template_name = "accounts/squads/squad_form.html"
    
    def test_func(self):
        return self.request.user.has_perm('accounts.add_squad')

    def get_success_url(self):
        return reverse_lazy("accounts:squad_detail", kwargs={"pk": self.object.pk})

    
class SquadListView(UserPassesTestMixin, ListView):
    model = Squad
    template_name = "accounts/squads/squad_list.html"
    ordering = ['name']
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.has_perm('accounts.view_squad')
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_deleted=False)
        search_query = self.request.GET.get('name')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset

    
class SquadDetailView(UserPassesTestMixin, DetailView):
    model = Squad
    template_name = "accounts/squads/squad_detail.html"

    def test_func(self):
        return self.request.user.has_perm('accounts.view_squad')

    
class SquadUpdateView(UserPassesTestMixin, UpdateView):
    model = Squad
    form_class = SquadForm
    template_name = "accounts/squads/squad_form.html"

    def test_func(self):
        return self.request.user.has_perm('accounts.change_squad')

    def get_success_url(self):
        return self.object.get_absolute_url()


def soft_delete(request, app_label, model_name, pk):
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    obj = get_object_or_404(model_class, pk=pk)
    self_user = request.user
    
    if model_name == 'user':
        if self_user == obj:
            return redirect('accounts:user_list')
        obj.is_active = False
    else:
        obj.is_deleted = True
        obj.save()
    
    if model_name == 'user':
        list_url = 'accounts:user_list'
    elif model_name == 'board':
        list_url = 'core:board-list'
    elif model_name == 'rooftype':
        list_url = 'inspections:roof_type_list'
    elif model_name == 'materialtypes':
        list_url = 'logistics:material_type_list'
    elif model_name == 'task':
        list_url = 'resolve_crm:tasks'
    else:
        list_url = '{}:{}_list'.format(app_label,model_name)
        
    return redirect(list_url)

def deactive_user(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    user.is_active = False
    user.save()
    return redirect('accounts:user_list')

def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.delete()
    return redirect('accounts:group_list')