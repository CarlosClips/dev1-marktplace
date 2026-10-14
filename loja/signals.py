from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Pedido, Produto


@receiver(pre_save, sender=Pedido)
def guardar_status_anterior(sender, instance, **kwargs):
    """Guarda o status antigo para detectar a transição para 'confirmado'."""
    if instance.pk:
        instance._status_anterior = (
            sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )
    else:
        instance._status_anterior = None


@receiver(post_save, sender=Pedido)
def atualizar_estoque(sender, instance, **kwargs):
    """Observer: ao confirmar um pedido, baixa o estoque dos produtos."""
    confirmou_agora = (
        instance.status == Pedido.Status.CONFIRMADO
        and instance._status_anterior != Pedido.Status.CONFIRMADO
    )
    if not confirmou_agora:
        return
    with transaction.atomic():
        for item in instance.itens.select_related("produto"):
            Produto.objects.filter(pk=item.produto_id).update(
                estoque=F("estoque") - item.quantidade
            )
