from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from acham.users.models import User

from .serializers import AccountDeleteSerializer
from .serializers import UserSerializer
from .serializers import UserUpdateSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        if request.method.lower() == "patch":
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        data = UserSerializer(request.user, context={"request": request}).data
        return Response(status=status.HTTP_200_OK, data=data)

    @action(detail=False, methods=["post"], url_path="delete-account")
    def delete_account(self, request):
        """
        Soft delete user account (deactivate).
        Simply POST to this endpoint to deactivate your account.
        """
        serializer = AccountDeleteSerializer(
            data={},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": _("Your account has been successfully deleted.")},
            status=status.HTTP_200_OK,
        )
