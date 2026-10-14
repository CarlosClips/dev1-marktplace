## Tecnologias

- Python 3.10+
- Django 5
- Django REST Framework
- djangorestframework-simplejwt
- SQLite (padrão do Django, sem configuração extra)

## Instalação e execução

```bash
# 1. clonar o repositório
git clone https://github.com/CarlosClips/dev1-marktplace.git ou git@github.com:CarlosClips/dev1-marktplace.git
cd marketplace

# 2. criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. instalar as dependências
pip install -r requirements.txt

# 4. criar o banco de dados
python manage.py migrate

# 5. (opcional) criar um superusuário para o admin
python manage.py createsuperuser

# 6. iniciar o servidor
python manage.py runserver
```

A API fica disponível em `http://127.0.0.1:8000/api/` e o admin em `http://127.0.0.1:8000/admin/`.


## Endpoints

Nos exemplos abaixo, os tokens foram abreviados (`eyJ...`).

### Autenticação

#### `POST /api/registro/` — cria um usuário

Requisição:
```json
{
  "username": "maria",
  "email": "maria@email.com",
  "password": "senha123"
}
```
Resposta `201 Created`:
```json
{
  "id": 1,
  "username": "maria",
  "email": "maria@email.com"
}
```

#### `POST /api/token/` — obtém access e refresh token

Requisição:
```json
{
  "username": "maria",
  "password": "senha123"
}
```
Resposta `200 OK`:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### `POST /api/token/refresh/` — renova o access token

Requisição:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```
Resposta `200 OK`:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Tags — `/api/tags/`

CRUD completo (`GET`, `POST`, `GET /{id}/`, `PUT`, `PATCH`, `DELETE`). Escrita exige token.

`POST /api/tags/`

Requisição:
```json
{ "nome": "eletronicos" }
```
Resposta `201 Created`:
```json
{ "id": 1, "nome": "eletronicos" }
```

### Vendedores — `/api/vendedores/`

CRUD completo. Escrita exige token, e só o dono edita ou apaga o próprio perfil. O perfil é vinculado automaticamente ao usuário logado.

`POST /api/vendedores/`

Requisição:
```json
{
  "nome_loja": "Loja da Maria",
  "bio": "Acessorios"
}
```
Resposta `201 Created`:
```json
{
  "id": 1,
  "usuario": "maria",
  "nome_loja": "Loja da Maria",
  "bio": "Acessorios",
  "produtos": []
}
```

`GET /api/vendedores/1/` — serializer aninhado, com os produtos do vendedor e suas tags. Resposta `200 OK`:
```json
{
  "id": 1,
  "usuario": "maria",
  "nome_loja": "Loja da Maria",
  "bio": "Acessorios",
  "produtos": [
    {
      "id": 1,
      "nome": "Fone Bluetooth",
      "descricao": "Sem fio",
      "preco": "150.00",
      "estoque": 8,
      "ativo": true,
      "vendedor": "Loja da Maria",
      "tags": [{ "id": 1, "nome": "eletronicos" }]
    }
  ]
}
```

#### `GET /api/vendedores/total-vendido/` — total vendido por vendedor

Usa `annotate` + `Sum`, considerando só pedidos **confirmados**, ordenado do maior para o menor. Resposta `200 OK`:
```json
[
  {
    "id": 1,
    "nome_loja": "Loja da Maria",
    "total_vendido": 300.0
  }
]
```

### Produtos — `/api/produtos/`

CRUD completo. Escrita exige token e perfil de vendedor, e só o dono edita ou apaga. Aceita o filtro `?disponiveis=true`, que usa o Manager customizado (`Produto.objects.disponiveis()`: ativos e com estoque maior que zero).

`POST /api/produtos/`

Requisição (`tag_ids` é opcional):
```json
{
  "nome": "Fone Bluetooth",
  "descricao": "Sem fio",
  "preco": "150.00",
  "estoque": 10,
  "tag_ids": [1]
}
```
Resposta `201 Created`:
```json
{
  "id": 1,
  "nome": "Fone Bluetooth",
  "descricao": "Sem fio",
  "preco": "150.00",
  "estoque": 10,
  "ativo": true,
  "vendedor": "Loja da Maria",
  "tags": [{ "id": 1, "nome": "eletronicos" }]
}
```

### Pedidos — `/api/pedidos/`

Exige token. Cada usuário só enxerga os próprios pedidos. Métodos aceitos: `GET`, `POST`, `PATCH`, `DELETE`.

#### `POST /api/pedidos/` — cria um pedido

Requisição:
```json
{
  "itens": [
    { "produto": 1, "quantidade": 2 }
  ]
}
```
Resposta `201 Created`:
```json
{
  "id": 1,
  "status": "pendente",
  "criado_em": "2026-10-14T18:43:51.835372-03:00",
  "itens": [
    {
      "id": 1,
      "produto": 1,
      "produto_nome": "Fone Bluetooth",
      "quantidade": 2,
      "preco_unitario": "150.00"
    }
  ],
  "total": 300.0
}
```

#### `PATCH /api/pedidos/{id}/` — confirma o pedido

Requisição:
```json
{ "status": "confirmado" }
```
Resposta `200 OK`: o mesmo formato acima, com `"status": "confirmado"`. Nesse momento o Signal baixa o estoque (no exemplo, de 10 para 8).

#### `GET /api/pedidos/`

Sem token, resposta `401 Unauthorized`:
```json
{
  "detail": "As credenciais de autenticação não foram fornecidas."
}
```
Com token, resposta `200 OK` com a lista dos pedidos do usuário (`[]` se não houver nenhum).

## Fluxo completo de uso

1. `POST /api/registro/` — cria o usuário vendedor e o usuário comprador.
2. `POST /api/token/` — o vendedor obtém o token.
3. `POST /api/vendedores/` — o vendedor cria o perfil.
4. `POST /api/tags/` e `POST /api/produtos/` — cadastra tag e produto.
5. `POST /api/token/` — o comprador obtém o próprio token.
6. `POST /api/pedidos/` — o comprador cria o pedido.
7. `PATCH /api/pedidos/1/` com `{"status": "confirmado"}` — confirma, e o estoque é baixado.
8. `GET /api/vendedores/total-vendido/` — confere o total vendido.

## Evidências do fluxo de autenticação

Prints do Thunder Client/Postman, em sequência, na pasta [`docs/`](docs/):

1. **Obtenção do token** — `POST /api/token/` retornando `access` e `refresh`: `docs/01-obter-token.png`
2. **Requisição autenticada** — `GET /api/pedidos/` com `Authorization: Bearer <access>` retornando `200`: `docs/02-com-token.png`
3. **Endpoint protegido sem token** — `GET /api/pedidos/` sem o header retornando `401`: `docs/03-sem-token.png`

