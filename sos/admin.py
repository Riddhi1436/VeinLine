from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from .models import SOSRequest, SOSResponse


# Temporary: register a minimal admin for SOSRequest to isolate rendering errors
@admin.register(SOSRequest)
class SOSRequestAdmin(admin.ModelAdmin):
    list_display = (
        "sos_id_display",
        "requester_display",
        "blood_group_display",
        "location_display",
        "units_display",
        "priority_display",
        "status_display",
        "responses_count_display",
        "time_display",
    )
    list_filter = ("status", "priority", "blood_group_needed", "city", "created_at")
    search_fields = ("city", "area", "hospital_name", "message", "requester__username", "requester__email")
    readonly_fields = (
        "id",
        "sms_reply_token",
        "created_at",
        "updated_at",
        "requester_display_detail",
        "priority_display_detail",
        "status_detail",
        "responses_detail",
    )

    fieldsets = (
        ("Emergency Details", {
            "fields": ("id", "requester_display_detail", "blood_group_needed", "units_needed", "priority_display_detail"),
        }),
        ("Location", {
            "fields": ("city", "area", "hospital_name"),
        }),
        ("Patient Message", {
            "fields": ("message",),
        }),
        ("Status & Responses", {
            "fields": ("status_detail", "responses_detail", "sms_reply_token"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Override fieldsets to handle display methods properly
        """
        fieldsets = super().get_fieldsets(request, obj)
        # Only show display detail methods when viewing an existing object
        if obj is None:  # Adding new
            fieldsets = (
                ("Emergency Details", {
                    "fields": ("blood_group_needed", "units_needed", "priority_display_detail"),
                }),
                ("Location", {
                    "fields": ("city", "area", "hospital_name"),
                }),
                ("Patient Message", {
                    "fields": ("message",),
                }),
                ("Status & Responses", {
                    "fields": ("status_detail", "sms_reply_token"),
                }),
            )
        return fieldsets

    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        qs = super().get_queryset(request)
        qs = qs.annotate(responses_count=Count('responses'))
        return qs

    def sos_id_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #006699;">SOS #{}</span>',
            obj.id
        )
    sos_id_display.short_description = "SOS ID"

    def requester_display(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.requester.email,
            obj.requester.username
        )
    requester_display.short_description = "Patient"

    def requester_display_detail(self, obj):
        return format_html(
            '<strong>{}</strong><br>Email: {}<br>Phone: {}',
            obj.requester.username,
            obj.requester.email,
            getattr(obj.requester.profile, 'phone_e164', 'Not set')
        )
    requester_display_detail.short_description = "Patient"

    def blood_group_display(self, obj):
        color_map = {
            'O+': '#ff6b6b', 'O-': '#ff8c8c',
            'A+': '#ff9999', 'A-': '#ffb3b3',
            'B+': '#ffcc00', 'B-': '#ffdd33',
            'AB+': '#4ecdc4', 'AB-': '#95e1d3',
        }
        color = color_map.get(obj.blood_group_needed, '#cccccc')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</span>',
            color,
            obj.blood_group_needed
        )
    blood_group_display.short_description = "Blood"

    def location_display(self, obj):
        location = f"{obj.city}"
        if obj.area:
            location += f", {obj.area}"
        return format_html(
            '<span title="{}">📍 {}</span>',
            location,
            location
        )
    location_display.short_description = "Location"

    def units_display(self, obj):
        return format_html(
            '<span style="color: #d63031; font-weight: bold;">{} units</span>',
            obj.units_needed
        )
    units_display.short_description = "Units"

    def priority_display(self, obj):
        colors = {
            'normal': '#3498db',
            'urgent': '#f39c12',
            'critical': '#e74c3c',
        }
        icons = {
            'normal': '🔵',
            'urgent': '🟠',
            'critical': '🔴',
        }
        color = colors.get(obj.priority, '#95a5a6')
        icon = icons.get(obj.priority, '⚪')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_priority_display()
        )
    priority_display.short_description = "Priority"

    def priority_display_detail(self, obj):
        colors = {
            'normal': '#3498db',
            'urgent': '#f39c12',
            'critical': '#e74c3c',
        }
        icons = {
            'normal': '🔵',
            'urgent': '🟠',
            'critical': '🔴',
        }
        color = colors.get(obj.priority, '#95a5a6')
        icon = icons.get(obj.priority, '⚪')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; font-size: 14px;">{} {}</span>',
            color,
            icon,
            obj.get_priority_display()
        )
    priority_display_detail.short_description = "Priority"

    def status_display(self, obj):
        colors = {
            'open': '#27ae60',
            'fulfilled': '#3498db',
            'cancelled': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Status"

    def status_detail(self, obj):
        colors = {
            'open': '#27ae60',
            'fulfilled': '#3498db',
            'cancelled': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_detail.short_description = "Status"

    def responses_count_display(self, obj):
        count = getattr(obj, 'responses_count', 0)
        if count == 0:
            return format_html('<span style="color: #e74c3c;">0 responses</span>')
        elif count < 3:
            return format_html('<span style="color: #f39c12;"><strong>{}</strong> responses</span>', count)
        else:
            return format_html('<span style="color: #27ae60;"><strong>{}</strong> responses ✓</span>', count)
    responses_count_display.short_description = "Donors Notified"

    def responses_detail(self, obj):
        responses = obj.responses.all()
        if not responses:
            return format_html('<span style="color: #e74c3c;">❌ No responses yet</span>')
        
        html = '<div style="margin-top: 10px;">'
        pending = responses.filter(response='pending').count()
        accepted = responses.filter(response='yes').count()
        declined = responses.filter(response='no').count()
        
        if pending:
            html += format_html('<p style="color: #3498db;">⏳ Pending: <strong>{}</strong></p>', pending)
        if accepted:
            html += format_html('<p style="color: #27ae60;">✅ Accepted: <strong>{}</strong></p>', accepted)
        if declined:
            html += format_html('<p style="color: #e74c3c;">❌ Declined: <strong>{}</strong></p>', declined)
        
        html += '<p><a href="{}?request__id__exact={}" target="_blank">View all responses →</a></p>'.format(
            reverse('admin:sos_sosresponse_changelist'),
            obj.id
        )
        html += '</div>'
        return format_html(html)
    responses_detail.short_description = "Donor Responses"

    def time_display(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.created_at.strftime('%b %d, %H:%M')
        )
    time_display.short_description = "Created"

    def has_add_permission(self, request):
        """Only admins can create SOS in admin. Patients use the form."""
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        """Allow admins to delete SOS"""
        return request.user.is_staff


@admin.register(SOSResponse)
class SOSResponseAdmin(admin.ModelAdmin):
    list_display = (
        "response_id_display",
        "sos_display",
        "donor_display",
        "response_display",
        "channel_display",
        "contact_shared_display",
        "time_display",
    )
    list_filter = ("response", "channel", "donor_consented_to_share_contact", "created_at", "request__blood_group_needed")
    search_fields = ("donor__username", "donor__email", "request__city", "request__hospital_name")
    readonly_fields = (
        "id",
        "request_display",
        "donor_display_detail",
        "response_display_detail",
        "channel_display_detail",
        "created_at",
        "responded_at",
        "patient_contact_revealed_at",
    )

    fieldsets = (
        ("Response ID", {
            "fields": ("id",),
        }),
        ("Request Details", {
            "fields": ("request_display",),
        }),
        ("Donor Details", {
            "fields": ("donor_display_detail",),
        }),
        ("Response", {
            "fields": ("response_display_detail", "channel_display_detail"),
        }),
        ("Contact Sharing", {
            "fields": ("donor_consented_to_share_contact", "patient_contact_revealed_at"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "responded_at"),
            "classes": ("collapse",),
        }),
    )

    def response_id_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">Response #{}</span>',
            obj.id
        )
    response_id_display.short_description = "ID"

    def sos_display(self, obj):
        url = reverse('admin:sos_sosrequest_change', args=[obj.request.id])
        return format_html(
            '<a href="{}" style="color: #006699;">SOS #{} - {}</a>',
            url,
            obj.request.id,
            obj.request
        )
    sos_display.short_description = "SOS Request"

    def request_display(self, obj):
        return format_html(
            '<strong>SOS #{}</strong><br>'
            'Blood: <span style="color: #d63031; font-weight: bold;">{}</span><br>'
            'Location: {} <br>'
            'Units: {}<br>'
            'Priority: {}<br>'
            'Status: {}',
            obj.request.id,
            obj.request.blood_group_needed,
            obj.request.city,
            obj.request.units_needed,
            obj.request.get_priority_display(),
            obj.request.get_status_display()
        )
    request_display.short_description = "SOS Request"

    def donor_display(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.donor.email,
            obj.donor.username
        )
    donor_display.short_description = "Donor"

    def donor_display_detail(self, obj):
        phone = getattr(obj.donor.profile, 'phone_e164', 'Not set')
        return format_html(
            '<strong>{}</strong><br>'
            'Email: {}<br>'
            'Phone: {}',
            obj.donor.username,
            obj.donor.email,
            phone
        )
    donor_display_detail.short_description = "Donor"

    def response_display(self, obj):
        colors = {
            'yes': '#27ae60',
            'no': '#e74c3c',
            'pending': '#f39c12',
        }
        icons = {
            'yes': '✅',
            'no': '❌',
            'pending': '⏳',
        }
        color = colors.get(obj.response, '#95a5a6')
        icon = icons.get(obj.response, '❓')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_response_display()
        )
    response_display.short_description = "Response"

    def response_display_detail(self, obj):
        colors = {
            'yes': '#27ae60',
            'no': '#e74c3c',
            'pending': '#f39c12',
        }
        icons = {
            'yes': '✅',
            'no': '❌',
            'pending': '⏳',
        }
        color = colors.get(obj.response, '#95a5a6')
        icon = icons.get(obj.response, '❓')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; font-size: 14px;">{} {}</span>',
            color,
            icon,
            obj.get_response_display()
        )
    response_display_detail.short_description = "Response"

    def channel_display(self, obj):
        icons = {
            'web': '🌐',
            'sms': '📱',
        }
        icon = icons.get(obj.channel, '📨')
        return format_html('{} {}', icon, obj.get_channel_display())
    channel_display.short_description = "Channel"

    def channel_display_detail(self, obj):
        icons = {
            'web': '🌐',
            'sms': '📱',
        }
        icon = icons.get(obj.channel, '📨')
        return format_html('{} {}', icon, obj.get_channel_display())
    channel_display_detail.short_description = "Channel"

    def contact_shared_display(self, obj):
        if obj.donor_consented_to_share_contact:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 4px;">✅ Shared</span>'
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 5px 10px; border-radius: 4px;">🔒 Private</span>'
        )
    contact_shared_display.short_description = "Contact"

    def time_display(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            obj.created_at.strftime('%b %d, %H:%M')
        )
    time_display.short_description = "Created"
