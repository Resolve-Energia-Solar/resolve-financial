# ERP Resolve

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

## Conclusão

A biblioteca `drf-flex-fields` facilita a personalização das respostas da API, permitindo que os clientes escolham quais dados precisam. Isso melhora a performance da API e reduz a transferência de dados desnecessários.

- **`expand`** → Expande relacionamentos.
- **`fields`** → Seleciona campos específicos.
- **`omit`** → Remove campos da resposta.

Essa flexibilidade melhora a eficiência e a experiência do usuário ao consumir a API.
