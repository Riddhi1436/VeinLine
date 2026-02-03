from django.contrib import admin
from django.utils.html import format_html

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Beautiful profile admin interface with color-coded display"""

    list_display = (
        "user_display",
        "role_display",
        "contact_display",
        "location_display",
        "updated_at",
    )
    list_filter = ("role", "city", "created_at")
    search_fields = ("user__username", "user__email", "phone_e164", "city", "area")
    readonly_fields = (
        "user_display",
        "role_display",
        "phone_display",
        "location_display",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("User Information", {"fields": ("user", "user_display")}),
        ("Profile Details", {"fields": ("role_display", "phone_display", "location_display")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def user_display(self, obj):
        """Display user with email"""
        if obj.user:
            email = obj.user.email or "—"
            return format_html(
                '<strong style="color: #1f2937;">{}</strong><br><span style="color: #6b7280; font-size: 0.9em;">{}</span>',
                obj.user.username,
                email,
            )
        return "—"

    user_display.short_description = "👤 User"

    def role_display(self, obj):
        """Display role with color coding"""
        colors = {
            "donor": ("#059669", "🩸 Donor"),
            "patient": ("#dc2626", "🏥 Patient"),
            "admin": ("#7c3aed", "⚙️ Admin"),
        }
        color, label = colors.get(obj.role, ("#6b7280", obj.role))
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 600;">{}</span>',
            color,
            label,
        )

    role_display.short_description = "📋 Role"

    def phone_display(self, obj):
        """Display phone number with privacy indicator"""
        if obj.phone_e164:
            return format_html(
                '<code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px;">{}</code><br><span style="font-size: 0.85em; color: #6b7280;">E.164 format</span>',
                obj.phone_e164,
            )
        return format_html('<span style="color: #d1d5db;">Not provided</span>')

    phone_display.short_description = "📞 Phone"

    def contact_display(self, obj):
        """Display phone status"""
        if obj.phone_e164:
            return format_html('<span style="color: #059669; font-weight: 600;">✅ {}</span>', obj.phone_e164)
        return format_html('<span style="color: #d1d5db;">—</span>')

    contact_display.short_description = "Contact"

    def location_display(self, obj):
        """Display city and area"""
        if obj.city or obj.area:
            location = f"{obj.city}, {obj.area}" if obj.area else obj.city
            return format_html('<span style="color: #1f2937;">📍 {}</span>', location)
        return format_html('<span style="color: #d1d5db;">—</span>')

    location_display.short_description = "📍 Location"

    def get_queryset(self, request):
        """Optimize queryset"""
        queryset = super().get_queryset(request)
        return queryset.select_related("user")
