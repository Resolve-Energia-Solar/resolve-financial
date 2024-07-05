import json
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt

from .models import Address


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