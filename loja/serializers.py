from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import ItemPedido, Pedido, PerfilVendedor, Produto, Tag

User = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 6}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "nome"]


class ProdutoSerializer(serializers.ModelSerializer):
    # nested (leitura): mostra as tags completas; escrita via tag_ids
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True, source="tags", required=False
    )
    vendedor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Produto
        fields = ["id", "nome", "descricao", "preco", "estoque", "ativo",
                  "vendedor", "tags", "tag_ids"]


class PerfilVendedorSerializer(serializers.ModelSerializer):
    # nested: produtos do vendedor via related_name="produtos"
    produtos = ProdutoSerializer(many=True, read_only=True)
    usuario = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = PerfilVendedor
        fields = ["id", "usuario", "nome_loja", "bio", "produtos"]


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "produto", "produto_nome", "quantidade", "preco_unitario"]
        read_only_fields = ["preco_unitario"]


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)  # nested
    total = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = ["id", "status", "criado_em", "itens", "total"]
        read_only_fields = ["criado_em"]

    def get_total(self, obj):
        return sum(i.quantidade * i.preco_unitario for i in obj.itens.all())

    def validate_status(self, valor):
        if self.instance is None:
            return Pedido.Status.PENDENTE  # todo pedido nasce pendente
        if self.instance.status != Pedido.Status.PENDENTE:
            raise serializers.ValidationError("Só pedidos pendentes podem mudar de status.")
        return valor

    def update(self, instance, validated_data):
        # PATCH só altera o status; os itens não mudam depois de criados
        instance.status = validated_data.get("status", instance.status)
        instance.save()  # dispara o signal
        return instance

    def validate_itens(self, itens):
        if not itens:
            raise serializers.ValidationError("O pedido precisa ter ao menos um item.")
        for item in itens:
            if not item["produto"].ativo:
                raise serializers.ValidationError(f"{item['produto']} está inativo.")
            if item["quantidade"] > item["produto"].estoque:
                raise serializers.ValidationError(
                    f"Estoque insuficiente para {item['produto']}."
                )
        return itens

    @transaction.atomic
    def create(self, validated_data):
        itens = validated_data.pop("itens")
        pedido = Pedido.objects.create(**validated_data)
        for item in itens:
            ItemPedido.objects.create(
                pedido=pedido,
                produto=item["produto"],
                quantidade=item["quantidade"],
                preco_unitario=item["produto"].preco,  # preço congelado
            )
        return pedido
