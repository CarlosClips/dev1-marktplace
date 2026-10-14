from django.db.models import F, Q, Sum
from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pedido, PerfilVendedor, Produto, Tag
from .permissions import IsDonoOuSomenteLeitura
from .serializers import (PedidoSerializer, PerfilVendedorSerializer,
                          ProdutoSerializer, RegistroSerializer, TagSerializer)


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ProdutoViewSet(viewsets.ModelViewSet):
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsDonoOuSomenteLeitura]

    def get_queryset(self):
        qs = Produto.objects.select_related("vendedor").prefetch_related("tags")
        if self.request.query_params.get("disponiveis") == "true":
            qs = qs.disponiveis()  
        return qs

    def perform_create(self, serializer):
        perfil = getattr(self.request.user, "perfil_vendedor", None)  
        if perfil is None:
            raise PermissionDenied("Crie um perfil de vendedor antes de cadastrar produtos.")
        serializer.save(vendedor=perfil)


class PerfilVendedorViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilVendedorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsDonoOuSomenteLeitura]
    queryset = PerfilVendedor.objects.select_related("user").prefetch_related("produtos__tags")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TotalVendidoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        dados = (
            PerfilVendedor.objects.annotate(
                total_vendido=Sum(
                    F("produtos__itens_pedido__quantidade")
                    * F("produtos__itens_pedido__preco_unitario"),
                    filter=Q(produtos__itens_pedido__pedido__status=Pedido.Status.CONFIRMADO),
                )
            )
            .order_by("-total_vendido")
            .values("id", "nome_loja", "total_vendido")
        )
        return Response([{**d, "total_vendido": d["total_vendido"] or 0} for d in dados])


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]  
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (Pedido.objects.filter(comprador=self.request.user)  
                .prefetch_related("itens__produto"))

    def perform_create(self, serializer):
        serializer.save(comprador=self.request.user)
