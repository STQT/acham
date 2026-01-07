from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import admin as auth_admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User
from .tasks import send_bulk_email

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name", "phone", "registration_method")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "name", "phone", "registration_method", "is_superuser"]
    search_fields = ["email", "name", "phone"]
    list_filter = ["registration_method", "is_staff", "is_superuser", "is_active"]
    readonly_fields = ["registration_method"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone", "password1", "password2"),
            },
        ),
    )
    actions = ["send_bulk_email_action"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "send-bulk-email/",
                self.admin_site.admin_view(self.send_bulk_email_view),
                name="users_user_send_bulk_email",
            ),
        ]
        return custom_urls + urls

    @method_decorator(csrf_protect)
    def send_bulk_email_view(self, request):
        """View for bulk email form."""
        if request.method == "POST":
            subject = request.POST.get("subject", "").strip()
            message = request.POST.get("message", "").strip()
            html_message = request.POST.get("html_message", "").strip() or None
            user_ids = request.POST.getlist("user_ids")

            if not subject or not message:
                messages.error(request, _("Subject and message are required."))
                return HttpResponseRedirect(reverse("admin:users_user_changelist"))

            # Convert user_ids to integers
            user_ids = [int(uid) for uid in user_ids if uid.isdigit()] if user_ids else None

            # Queue the task
            task = send_bulk_email.delay(
                subject=subject,
                message=message,
                html_message=html_message,
                user_ids=user_ids,
            )

            if user_ids:
                count = len(user_ids)
            else:
                count = User.objects.filter(email__isnull=False).exclude(email="").count()

            messages.success(
                request,
                _(
                    "Bulk email task queued successfully. "
                    "Emails will be sent to {count} users. Task ID: {task_id}"
                ).format(count=count, task_id=task.id),
            )
            return HttpResponseRedirect(reverse("admin:users_user_changelist"))

        # GET request - show form
        selected_users = request.GET.get("ids", "").split(",") if request.GET.get("ids") else []
        selected_users = [int(uid) for uid in selected_users if uid.isdigit()]

        context = {
            **self.admin_site.each_context(request),
            "title": _("Send Bulk Email"),
            "selected_users": selected_users,
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }

        from django.template.response import TemplateResponse
        return TemplateResponse(
            request,
            "admin/users/send_bulk_email.html",
            context,
        )

    def send_bulk_email_action(self, request, queryset):
        """Admin action to send bulk email to selected users."""
        user_ids = list(queryset.values_list("id", flat=True))
        url = reverse("admin:users_user_send_bulk_email")
        if user_ids:
            url += f"?ids={','.join(map(str, user_ids))}"
        return HttpResponseRedirect(url)

    send_bulk_email_action.short_description = _("Send bulk email to selected users")
