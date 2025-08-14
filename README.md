# ERP Resolve Produção

Sistema de _Enterprise Resource Planning_ da Resolve Energia Solar.

# Documentação: Uso dos Parâmetros `expand`, `fields` e `omit` no Django REST Framework com `drf-flex-fields`

Esta documentação explica como utilizar os parâmetros `expand`, `fields` e `omit` ao consumir APIs construídas com Django REST Framework e `drf-flex-fields`. Estes parâmetros permitem maior flexibilidade na resposta da API, reduzindo ou expandindo dados conforme necessário.

## 1. Expansão de Relacionamentos (`expand`)

O parâmetro `expand` permite carregar objetos relacionados em vez de apenas retornar os seus IDs.

### **Exemplo de Uso na URL**

Requisição Padrão:

```plaintext
GET /api/services/
```

**Resposta Padrão:**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": 3
    }
]
```

Requisição com Expansão:

```plaintext
GET /api/services/?expand=category
```

**Resposta com Expansão:**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": {
            "id": 3,
            "name": "Categoria X",
            "main_category": 2
        }
    }
]
```

---

## 2. Selecionando Campos (`fields`)

O parâmetro `fields` permite definir quais campos devem ser incluídos na resposta.

### **Exemplo de Uso na URL**

Requisição Padrão:

```plaintext
GET /api/services/
```

**Resposta Completa:**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": 3,
        "created_at": "2024-03-12T10:00:00Z"
    }
]
```

Requisição com `fields`:

```plaintext
GET /api/services/?fields=id,name
```

**Resposta Apenas com `id` e `name`:**

```json
[
    {
        "id": 1,
        "name": "Serviço A"
    }
]
```

---

## 3. Removendo Campos (`omit`)

O parâmetro `omit` permite remover campos específicos da resposta.

### **Exemplo de Uso na URL**

Requisição Padrão:

```plaintext
GET /api/services/
```

**Resposta Completa:**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": 3,
        "created_at": "2024-03-12T10:00:00Z"
    }
]
```

Requisição com `omit`:

```plaintext
GET /api/services/?omit=created_at
```

**Resposta Sem o Campo `created_at`:**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": 3
    }
]
```

---

## 4. Combinação de Parâmetros

Os três parâmetros podem ser combinados para criar respostas ainda mais personalizadas.

### **Exemplo de Uso na URL**

```plaintext
GET /api/services/?fields=id,name,category&expand=category&omit=created_at
```

### **Resposta Final**

```json
[
    {
        "id": 1,
        "name": "Serviço A",
        "category": {
            "id": 3,
            "name": "Categoria X"
        }
    }
]
```

---

/**
 * @endpoint GET /projeto?metricas
 *
 * @descricao
 * Este endpoint recupera informações do projeto, aprimoradas com métricas anotadas.
 * O parâmetro de consulta "metricas" permite que os clientes especifiquem quais
 * anotações adicionais devem ser incluídas na resposta. Cada métrica corresponde a um 
 * método de anotação ORM do Django definido no gerenciador personalizado do modelo Projeto.
 *
 * @parametros metricas (string de consulta)
 * Uma lista separada por vírgulas de identificadores de métricas que determinam quais anotações
 * incluir. Os identificadores de métricas disponíveis e suas respectivas anotações são:
 *
 * - is_released_to_engineering: Adiciona uma anotação usando "Projeto.objects.with_is_released_to_engineering".
 * - delivery_status: Adiciona uma anotação usando "Projeto.objects.with_delivery_status".
 * - trt_status: Adiciona uma anotação usando "Projeto.objects.with_trt_status".
 * - pending_material_list: Adiciona uma anotação usando "Projeto.objects.with_pending_material_list".
 * - access_opnion: Adiciona uma anotação usando "Projeto.objects.with_access_opnion".
 * - trt_pending: Adiciona uma anotação usando "Projeto.objects.with_trt_pending".
 * - request_requested: Adiciona uma anotação usando "Projeto.objects.with_request_requested".
 * - last_installation_final_service_opinion: Adiciona uma anotação usando "Projeto.objects.with_last_installation_final_service_opinion".
 * - supply_adquance_names: Adiciona uma anotação usando "Projeto.objects.with_supply_adquance_names".
 * - access_opnion_status: Adiciona uma anotação usando "Projeto.objects.with_access_opnion_status".
 * - load_increase_status: Adiciona uma anotação usando "Projeto.objects.with_load_increase_status".
 * - branch_adjustment_status: Adiciona uma anotação usando "Projeto.objects.with_branch_adjustment_status".
 * - new_contact_number_status: Adiciona uma anotação usando "Projeto.objects.with_new_contact_number_status".
 * - final_inspection_status: Adiciona uma anotação usando "Projeto.objects.with_final_inspection_status".
 * - purchase_status: Adiciona uma anotação usando "Projeto.objects.with_purchase_status".
 *
 * @exemplo
 * Para solicitar múltiplas anotações, liste os identificadores de métricas separados por vírgulas.
 *
 * Exemplo:
 * GET /api/projects?metricas=is_released_to_engineering,delivery_status,trt_status
 *
 * O endpoint processará esses identificadores de métricas e incluirá as respectivas anotações
 * nos dados do projeto retornados.
 */

## Conclusão

A biblioteca `drf-flex-fields` facilita a personalização das respostas da API, permitindo que os clientes escolham quais dados precisam. Isso melhora a performance da API e reduz a transferência de dados desnecessários.

- **`expand`** → Expande relacionamentos.
- **`fields`** → Seleciona campos específicos.
- **`omit`** → Remove campos da resposta.

Essa flexibilidade melhora a eficiência e a experiência do usuário ao consumir a API.
