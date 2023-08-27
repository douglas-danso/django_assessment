from rest_framework.permissions import BasePermission

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission class that allows only admin users to perform write
    operations, but allows all users to perform read operations.
    """

    def has_permission(self, request, view):
        # Allow read operations to everyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Allow write operations only to admin users
        return request.user.is_superuser
