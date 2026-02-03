from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        if not profile:
            return False
        return profile.role in self.allowed_roles or user.is_staff


class IsDonor(HasRole):
    allowed_roles = {"donor"}


class IsPatient(HasRole):
    allowed_roles = {"patient"}


class IsAdminRole(HasRole):
    allowed_roles = {"admin"}


