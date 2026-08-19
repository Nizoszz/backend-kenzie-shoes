from django.contrib import admin
from django.utils import timezone

from .models import OIDCIdentity, PartnerApplication, User


@admin.register(PartnerApplication)
class PartnerApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at", "reviewer")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email")
    actions = ("approve", "reject")

    @admin.action(description="Aprovar solicitações selecionadas")
    def approve(self, request, queryset):
        pending = queryset.filter(status=PartnerApplication.Status.PENDING)
        for application in pending.select_related("user"):
            application.status = PartnerApplication.Status.APPROVED
            application.reviewer = request.user
            application.reviewed_at = timezone.now()
            application.save(update_fields=("status", "reviewer", "reviewed_at"))
            application.user.is_seller = True
            application.user.save(update_fields=("is_seller",))

    @admin.action(description="Rejeitar solicitações selecionadas")
    def reject(self, request, queryset):
        queryset.filter(status=PartnerApplication.Status.PENDING).update(
            status=PartnerApplication.Status.REJECTED,
            reviewer=request.user,
            reviewed_at=timezone.now(),
        )


admin.site.register(User)
admin.site.register(OIDCIdentity)
