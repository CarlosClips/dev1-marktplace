from django.conf import settings
from django.db import models


class PerfilVendedor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_vendedor"
    )
    nome_loja = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.nome_loja


class Tag(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome


class ProdutoQuerySet(models.QuerySet):
    def disponiveis(self):
        return self.filter(ativo=True, estoque__gt=0)


class ProdutoManager(models.Manager.from_queryset(ProdutoQuerySet)):
    """Manager customizado: Produto.objects.disponiveis()"""


class Produto(models.Model):
    vendedor = models.ForeignKey(
        PerfilVendedor, on_delete=models.CASCADE, related_name="produtos"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="produtos")
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    objects = ProdutoManager()

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"

    comprador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos"
    )
    produtos = models.ManyToManyField(Produto, through="ItemPedido", related_name="pedidos")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.pk} ({self.status})"


class ItemPedido(models.Model):
    """Through model: guarda quantidade e preço no momento da compra."""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="itens_pedido")
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade}x {self.produto}"
