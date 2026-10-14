from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (PedidoViewSet, PerfilVendedorViewSet, ProdutoViewSet,
                    TagViewSet, TotalVendidoView)

router = DefaultRouter()
router.register("produtos", ProdutoViewSet, basename="produto")
router.register("vendedores", PerfilVendedorViewSet, basename="vendedor")
router.register("pedidos", PedidoViewSet, basename="pedido")
router.register("tags", TagViewSet, basename="tag")

urlpatterns = [
    path("vendedores/total-vendido/", TotalVendidoView.as_view(), name="total-vendido"),
] + router.urls
