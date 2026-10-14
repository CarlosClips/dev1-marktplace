from django.contrib import admin

from .models import ItemPedido, Pedido, PerfilVendedor, Produto, Tag


class ItemInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [ItemInline]
    list_display = ["id", "comprador", "status", "criado_em"]


admin.site.register([PerfilVendedor, Produto, Tag])
