import json
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from .models import Address, Branch, Department, Role, Squad
from .forms import BranchForm, SquadForm, UserForm, UserUpdateForm, GroupForm


class UsersListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "accounts/users/user_list.html"
    paginate_by = 10
    ordering = ['username']
    
    def get_queryset(self):
        queryset = super().get_queryset()
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


class UserDetailView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "accounts/users/user_detail.html"
    slug_field = "username"
    context_object_name = "user_obj"


class UserCreateView(LoginRequiredMixin, CreateView):
    model = get_user_model()
    form_class = UserForm
    template_name = "accounts/users/user_create.html"
    
    def form_valid(self, form):
        # Generate a random password
        password = get_user_model().objects.make_random_password()
        
        # Set the generated password for the user
        user = form.save(commit=False)
        user.set_password(password)
        
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
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            field_object = form.fields[field]
            for error in errors:
                messages.error(self.request, f"Erro no campo {field_object.label}: {error} Por favor, corrija o erro e tente novamente.")
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "accounts/users/user_update.html"
    slug_field = "username"

    def get_success_url(self):
        return self.object.get_absolute_url()


class PermissionCreateView(LoginRequiredMixin, CreateView):
    model = Permission
    fields = ['name', 'content_type', 'codename']
    template_name = "accounts/permissions/permission_form.html"
    
    def get_success_url(self):
        return reverse_lazy("accounts:permission_list")


class PermissionsListView(LoginRequiredMixin, ListView):
    model = Permission
    template_name = "accounts/permissions/permission_list.html"
    paginate_by = 10
    ordering = ['content_type', 'codename']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset


class PermissionUpdateView(LoginRequiredMixin, UpdateView):
    model = Permission
    fields = ['name', 'content_type', 'codename']
    template_name = "accounts/permissions/permission_form.html"
    slug_field = "codename"
    
    def get_success_url(self):
        return reverse_lazy("accounts:permission_list")


class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "accounts/groups/group_form.html"
    
    def get_success_url(self):
        return reverse_lazy("accounts:group_list")


class GroupsListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "accounts/groups/group_list.html"
    ordering = ['name']
    paginate_by = 10


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = "accounts/groups/group_detail.html"


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "accounts/groups/group_form.html"
    slug_field = "codename"
    
    def get_success_url(self):
        return reverse_lazy("accounts:group_detail", kwargs={"pk": self.object.pk})


class BranchCreateView(LoginRequiredMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'accounts/branches/branch_form.html'
    success_url = reverse_lazy('accounts:branch_list')
    
    # def get_success_url(self):
        # return reverse_lazy('branch_detail', kwargs={"pk": self.object.pk})


class BranchListView(LoginRequiredMixin, ListView):
    model = Branch
    template_name = "accounts/branches/branch_list.html"
    ordering = ['name']
    paginate_by = 10


class BranchDetailView(LoginRequiredMixin, DetailView):
    model = Branch
    template_name = "accounts/branches/branch_detail.html"
    context_object_name = "branch"


class BranchUpdateView(LoginRequiredMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'accounts/branches/branch_form.html'
    success_url = reverse_lazy('accounts:branch_list')
    
    # def get_success_url(self):
        # return reverse_lazy('branch_detail', kwargs={"pk": self.object.pk})


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    fields = '__all__'
    template_name = "accounts/departments/department_form.html"
    success_url = reverse_lazy('accounts:department_list')


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "accounts/departments/department_list.html"
    ordering = ['name']
    paginate_by = 10


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    fields = '__all__'
    template_name = "accounts/departments/department_form.html"
    success_url = reverse_lazy('accounts:department_list')


class RoleCreateView(LoginRequiredMixin, CreateView):
    model = Role
    fields = '__all__'
    template_name = "accounts/roles/role_form.html"
    success_url = reverse_lazy('accounts:role_list')


class RoleListView(LoginRequiredMixin, ListView):
    model = Role
    template_name = "accounts/roles/role_list.html"
    ordering = ['name']
    paginate_by = 10


class RoleUpdateView(LoginRequiredMixin, UpdateView):
    model = Role
    fields = '__all__'
    template_name = "accounts/roles/role_form.html"
    success_url = reverse_lazy('accounts:department_list')


class AddressCreateView(LoginRequiredMixin, CreateView):
    model = Address
    fields = '__all__'
    template_name = "accounts/address/address_form.html"
    success_url = reverse_lazy('accounts:address_list')


class AddressListView(LoginRequiredMixin, ListView):
    model = Address
    template_name = "accounts/address/address_list.html"
    ordering = ['street']
    paginate_by = 10


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = Address
    fields = '__all__'
    template_name = "accounts/address/address_form.html"
    success_url = reverse_lazy('accounts:address_list')


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


def delete_user(request, username):
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        messages.error(request, "Usuário não encontrado.")
        return redirect('accounts:users_list')
    
    if request.user.username == username:
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect(user.get_absolute_url())
    elif not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para excluir usuários.")
        return redirect(user.get_absolute_url())
    else:
        messages.success(request, f"Usuário {user.username} excluído com sucesso.")
        user.delete()
    return redirect('accounts:users_list')


class SquadCreateView(LoginRequiredMixin, CreateView):
    model = Squad
    form_class = SquadForm
    template_name = "accounts/squads/squad_form.html"

    def get_success_url(self):
        return redirect("accounts:squad_detail", kwargs={"pk": self.object.pk})

    
class SquadListView(LoginRequiredMixin, ListView):
    model = Squad
    template_name = "accounts/squads/squad_list.html"
    ordering = ['name']
    paginate_by = 10

    
class SquadDetailView(LoginRequiredMixin, DetailView):
    model = Squad
    template_name = "accounts/squads/squad_detail.html"

    
class SquadUpdateView(LoginRequiredMixin, UpdateView):
    model = Squad
    form_class = SquadForm
    template_name = "accounts/squads/squad_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    