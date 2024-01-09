from rest_framework.permissions import BasePermission


class IsShopUser(BasePermission):
    """Разрешает доступ к API только магазинам"""

    def has_permission(self, request, view):
        return bool(request.user and request.user.type == 'shop')