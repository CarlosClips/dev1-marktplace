from rest_framework import permissions


class IsDonoOuSomenteLeitura(permissions.BasePermission):
    """Leitura para todos; escrita só para o dono do registro."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # PerfilVendedor tem .user; Produto tem .vendedor.user
        dono = obj.user if hasattr(obj, "user") else obj.vendedor.user
        return dono == request.user
