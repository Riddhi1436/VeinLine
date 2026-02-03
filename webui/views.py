from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.views import View
from django.contrib import messages
from django.db import transaction
import logging

from accounts.models import Profile
from accounts.services import make_user_admin
from django.utils import timezone
from datetime import timedelta

from donations.models import BloodBankInventory, DonorDetails
from appointments.models import AppointmentSlot, Appointment
from sos.models import SOSRequest, SOSResponse, SOSStatus, SOSPriority
from sos.services import match_donors_for_request, DEFAULT_COMPATIBILITY
from core.services.sms import send_sms
from core.services.emailing import send_fallback_email

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "home.html"


class AboutView(TemplateView):
    template_name = "about.html"


class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, self.template_name)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, self.template_name)


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        role = request.POST.get("role", "donor")
        full_name = request.POST.get("full_name", "")
        phone = request.POST.get("phone", "")

        # Validation
        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, self.template_name)

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name)

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, self.template_name)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, self.template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please use another email.")
            return render(request, self.template_name)

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else "",
                last_name=" ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            )

            # Make first user an admin
            is_first_user = User.objects.count() == 1
            if is_first_user:
                make_user_admin(user)
                admin_message = " You have been set as Admin!"
            else:
                admin_message = ""

            # Create profile (signals should handle this, but ensure it exists)
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    "role": role,
                    "phone_e164": phone if phone else None,
                },
            )
            if not created:
                # Update existing profile
                profile.role = role
                if phone:
                    profile.phone_e164 = phone
                profile.save()

            # Auto-login (specify backend because multiple auth backends are configured)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(
                request,
                f"Welcome to VeinLine, {user.username}! Your account has been created successfully.{admin_message}",
            )
            return redirect("home")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, self.template_name)


class LogoutViewCustom(View):
    """Custom logout view that handles both GET and POST"""
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("home")
    
    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("home")


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles: set[str] = set()

    def dispatch(self, request, *args, **kwargs):
        role = getattr(getattr(request.user, "profile", None), "role", "")
        if request.user.is_staff or role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        return redirect("home")


class DonorDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboards/donor.html"
    allowed_roles = {"donor"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        details = getattr(self.request.user, "donor_details", None)
        profile = getattr(self.request.user, "profile", None)
        ctx["donor_details"] = details
        ctx["pending_responses"] = SOSResponse.objects.filter(donor=self.request.user, response="pending").count()

        # Donor's city: DonorDetails first, then Profile, so we show patient requests even without full donor profile
        donor_city = (details.city if details else "") or (profile.city if profile else "") or ""
        donor_blood = details.blood_group if details else None

        # Open SOS: only those this donor can help (blood compatible) and optionally in their city
        qs = SOSRequest.objects.filter(status="open").order_by("-priority", "-created_at")
        if donor_blood:
            # Recipient blood groups this donor can fulfill
            allowed_recipient = [bg for bg, donors in DEFAULT_COMPATIBILITY.items() if donor_blood in donors]
            qs = qs.filter(blood_group_needed__in=allowed_recipient)
        if donor_city:
            qs = qs.filter(city__iexact=donor_city)
        ctx["open_sos_nearby"] = list(qs[:20])
        return ctx


class PatientDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboards/patient.html"
    allowed_roles = {"patient"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        my = SOSRequest.objects.filter(requester=self.request.user).order_by("-created_at")
        ctx["my_requests"] = my[:20]
        ctx["my_open_count"] = my.filter(status="open").count()
        ctx["responses_count"] = SOSResponse.objects.filter(request__requester=self.request.user).count()
        return ctx


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/admin.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["donors_by_group"] = list(
            DonorDetails.objects.values("blood_group").annotate(count=Count("id")).order_by("blood_group")
        )
        ctx["donors_active"] = DonorDetails.objects.filter(is_available=True).count()
        ctx["donors_inactive"] = DonorDetails.objects.filter(is_available=False).count()
        ctx["sos_by_status"] = list(
            SOSRequest.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        ctx["responses_by_choice"] = list(
            SOSResponse.objects.values("response").annotate(count=Count("id")).order_by("response")
        )
        ctx["inventory"] = BloodBankInventory.objects.all().order_by("city", "blood_group")[:50]
        return ctx


class CreateSOSView(RoleRequiredMixin, TemplateView):
    """Create emergency SOS request"""
    template_name = "create_sos.html"
    allowed_roles = {"patient"}

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle SOS creation from form"""
        try:
            blood_group = request.POST.get('blood_group_needed', '').strip()
            units = int(request.POST.get('units_needed', 1))
            city = request.POST.get('city', '').strip()
            area = request.POST.get('area', '').strip()
            hospital = request.POST.get('hospital_name', '').strip()
            message = request.POST.get('message', '').strip()
            priority = request.POST.get('priority', SOSPriority.NORMAL)

            # Validation
            if not blood_group:
                messages.error(request, "Blood group is required.")
                return render(request, self.template_name)
            
            if not city:
                messages.error(request, "City is required.")
                return render(request, self.template_name)

            if units < 1 or units > 10:
                messages.error(request, "Units must be between 1 and 10.")
                return render(request, self.template_name)

            if priority not in dict(SOSPriority.choices):
                priority = SOSPriority.NORMAL

            # Create SOS request
            sos_request = SOSRequest.objects.create(
                requester=request.user,
                blood_group_needed=blood_group,
                units_needed=units,
                city=city,
                area=area,
                hospital_name=hospital,
                message=message,
                status=SOSStatus.OPEN,
                priority=priority,
            )

            messages.success(
                request,
                f"🚨 SOS Request #{sos_request.id} created successfully! "
                f"Looking for matching {blood_group} donors in {city}..."
            )

            # Find and notify matching donors
            try:
                logger.info(f"[SOS #{sos_request.id}] Starting donor matching for {blood_group} in {city}")
                
                donors = match_donors_for_request(sos_request, limit=50)
                donors_list = list(donors)
                
                logger.info(f"[SOS #{sos_request.id}] Found {len(donors_list)} matching donors")
                
                if donors_list:
                    # Send SMS to each donor
                    sms_message = (
                        f"VeinLine SOS: Need {sos_request.blood_group_needed} blood in {sos_request.city}. "
                        f"Reply: YES {sos_request.sms_reply_token} or NO {sos_request.sms_reply_token}."
                    )

                    notified_count = 0
                    failed_count = 0
                    no_phone_count = 0
                    
                    with transaction.atomic():
                        for donor in donors_list:
                            donor_name = donor.user.username
                            
                            # Create response record
                            SOSResponse.objects.get_or_create(
                                request=sos_request,
                                donor=donor.user,
                                defaults={'response': 'pending', 'channel': 'sms'}
                            )

                            # Send SMS
                            phone = getattr(getattr(donor.user, 'profile', None), 'phone_e164', '')
                            if phone:
                                try:
                                    logger.info(f"[SOS #{sos_request.id}] Sending SMS to {donor_name} ({phone})")
                                    result = send_sms(phone, sms_message)
                                    
                                    if result.get('ok'):
                                        logger.info(f"[SOS #{sos_request.id}] ✓ SMS sent to {donor_name}")
                                        notified_count += 1
                                    else:
                                        logger.warning(f"[SOS #{sos_request.id}] ✗ SMS failed for {donor_name}: {result.get('reason')}")
                                        failed_count += 1
                                except Exception as e:
                                    logger.error(f"[SOS #{sos_request.id}] Error sending SMS to {donor_name}: {str(e)}")
                                    failed_count += 1
                            else:
                                logger.warning(f"[SOS #{sos_request.id}] Donor {donor_name} has no phone number")
                                no_phone_count += 1

                            # Email fallback
                            try:
                                send_fallback_email(
                                    to_email=getattr(donor.user, 'email', ''),
                                    subject="VeinLine SOS Alert",
                                    message=sms_message,
                                )
                            except Exception as e:
                                logger.warning(f"[SOS #{sos_request.id}] Error sending email to {donor.user.email}: {str(e)}")

                    summary = f"✅ Found {len(donors_list)} matching donors. "
                    if notified_count > 0:
                        summary += f"Notifications sent to {notified_count}"
                    if no_phone_count > 0:
                        summary += f" ({no_phone_count} donors missing phone)"
                    if failed_count > 0:
                        summary += f" ({failed_count} SMS failures)"
                    
                    logger.info(f"[SOS #{sos_request.id}] Summary: {summary}")
                    messages.success(request, summary)
                else:
                    logger.warning(f"[SOS #{sos_request.id}] No matching donors found for {blood_group} in {city}")
                    messages.warning(
                        request,
                        f"⚠️ No matching donors found in {city} with {blood_group} blood group. "
                        "Check the status regularly - more donors may become available."
                    )

            except Exception as e:
                logger.error(f"[SOS #{sos_request.id}] Error during donor notification: {str(e)}", exc_info=True)
                messages.warning(
                    request,
                    f"SOS created (#{sos_request.id}), but error notifying donors: {str(e)}"
                )

            # Redirect to patient dashboard
            return redirect('patient-dashboard')

        except Exception as e:
            messages.error(request, f"Error creating SOS: {str(e)}")
            return render(request, self.template_name)


class LeaderboardView(TemplateView):
    """Public leaderboard view for donors"""
    template_name = "leaderboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            from donations.models import DonorStatistics, Badge
            from donations.serializers import LeaderboardSerializer
            
            # Get top 100 donors
            stats = DonorStatistics.objects.filter(points__gt=0).order_by('-points')[:100]
            
            # Update ranks
            for idx, stat in enumerate(stats, 1):
                stat.rank = idx
            
            # Serialize data
            serializer = LeaderboardSerializer(stats, many=True)
            ctx['top_donors'] = serializer.data
            
            # Get badges from the same models module
            ctx['available_badges'] = [
                {'key': key, 'label': value} for key, value in Badge.choices
            ]
        except Exception as e:
            ctx['top_donors'] = []
            # Fall back to manually defined badges
            ctx['available_badges'] = [
                {'key': 'first_donation', 'label': 'First Donation'},
                {'key': 'five_donations', 'label': '5 Donations'},
                {'key': 'ten_donations', 'label': '10 Donations'},
                {'key': 'hero', 'label': 'Blood Hero (20+ Donations)'},
                {'key': 'lifesaver', 'label': 'Lifesaver (30+ Donations)'},
                {'key': 'consistent', 'label': 'Consistent Donor (Donated 6+ months consecutively)'},
                {'key': 'emergency', 'label': 'Emergency Responder (Responded to 3+ SOS)'},
                {'key': 'trusted', 'label': 'Trusted Donor (5+ positive confirmations)'},
                {'key': 'speed', 'label': 'Speed Donor (Responded to SOS within 1 hour)'},
            ]
            print(f"Error loading donors/badges: {e}")
        
        return ctx


class AppointmentsView(TemplateView):
    """Appointment booking view"""
    template_name = "appointments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_authenticated"] = self.request.user.is_authenticated
        today = timezone.now().date()
        thirty_days = today + timedelta(days=30)
        context["slots"] = (
            AppointmentSlot.objects.filter(
                status="available",
                date__range=[today, thirty_days],
            )
            .order_by("date", "start_time")
        )
        if self.request.user.is_authenticated:
            context["my_appointments"] = (
                Appointment.objects.filter(donor=self.request.user)
                .select_related("slot")
                .order_by("-booked_at")
            )
        else:
            context["my_appointments"] = []
        return context


class BloodBanksView(TemplateView):
    """Blood bank finder view"""
    template_name = "blood_banks.html"


class EligibilityCheckerView(TemplateView):
    """Medical eligibility checker view"""
    template_name = "eligibility_checker.html"


class ActivityTimelineView(LoginRequiredMixin, TemplateView):
    """User activity timeline view"""
    template_name = "activity_timeline.html"


class PrivacyPolicyView(TemplateView):
    """Privacy policy view"""
    template_name = "privacy.html"


class TermsOfServiceView(TemplateView):
    """Terms of service view"""
    template_name = "terms.html"


class ContactView(View):
    """Contact form view"""
    template_name = "contact.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        
        if not all([name, email, subject, message]):
            messages.error(request, "Please fill in all fields.")
            return render(request, self.template_name)
        
        try:
            # Here you could send an email or save to database
            # For now, we'll just show a success message
            messages.success(request, "Thank you for contacting us! We'll get back to you soon.")
            return redirect("contact")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, self.template_name)


class SupportView(TemplateView):
    """Support center view"""
    template_name = "support.html"


class AnalyticsView(TemplateView):
    """Public analytics dashboard view"""
    template_name = "analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["donors_by_group"] = list(
            DonorDetails.objects.values("blood_group").annotate(count=Count("id")).order_by("blood_group")
        )
        ctx["donors_active"] = DonorDetails.objects.filter(is_available=True).count()
        ctx["donors_inactive"] = DonorDetails.objects.filter(is_available=False).count()
        ctx["sos_by_status"] = list(
            SOSRequest.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        ctx["responses_by_choice"] = list(
            SOSResponse.objects.values("response").annotate(count=Count("id")).order_by("response")
        )
        ctx["inventory"] = BloodBankInventory.objects.all().order_by("-updated_at")[:20]
        
        # Calculate total SOS requests
        ctx["total_sos_requests"] = SOSRequest.objects.count()
        
        # Calculate response rate
        total_responses = SOSResponse.objects.count()
        accepted_responses = SOSResponse.objects.filter(response="accepted").count()
        ctx["response_rate"] = round((accepted_responses / total_responses * 100) if total_responses > 0 else 0, 1)
        
        return ctx


class PatientSOSDashboardView(RoleRequiredMixin, TemplateView):
    """Patient SOS management dashboard"""
    template_name = "dashboards/patient_sos.html"
    allowed_roles = {"patient"}
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all SOS requests by this patient
        sos_requests = SOSRequest.objects.filter(requester=user).order_by('-created_at')
        
        # For each SOS, get responses with tracking info
        requests_with_responses = []
        for sos in sos_requests:
            responses = SOSResponse.objects.filter(request=sos).select_related(
                'donor', 'donor__donor_details', 'donor__profile'
            ).order_by('-responded_at')
            
            # Get tracking info for each response
            responses_data = []
            for resp in responses:
                tracker = getattr(resp, 'donation_tracker', None)
                responses_data.append({
                    'response': resp,
                    'tracker': tracker,
                    'donor_details': getattr(resp.donor, 'donor_details', None),
                    'donor_stats': getattr(resp.donor, 'donor_stats', None),
                })
            
            requests_with_responses.append({
                'sos': sos,
                'responses': responses_data,
                'yes_count': responses.filter(response='yes').count(),
                'pending_count': responses.filter(response='pending').count(),
                'total_count': responses.count(),
            })
        
        ctx['requests_with_responses'] = requests_with_responses
        ctx['total_sos'] = sos_requests.count()
        ctx['open_sos'] = sos_requests.filter(status='open').count()
        
        return ctx


class DonorSOSDashboardView(RoleRequiredMixin, TemplateView):
    """Donor SOS alerts and response dashboard"""
    template_name = "dashboards/donor_sos.html"
    allowed_roles = {"donor"}
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        donor_details = getattr(user, 'donor_details', None)
        
        # Get active SOS requests in donor's city
        if donor_details:
            active_sos = SOSRequest.objects.filter(
                status='open',
                city__iexact=donor_details.city
            ).order_by('-priority', '-created_at')[:20]
        else:
            active_sos = SOSRequest.objects.filter(status='open').order_by('-priority', '-created_at')[:20]
        
        # Get donor's own responses
        my_responses = SOSResponse.objects.filter(
            donor=user
        ).select_related('request').order_by('-created_at')[:20]
        
        # Get responses with tracking
        responses_with_tracking = []
        for resp in my_responses:
            tracker = getattr(resp, 'donation_tracker', None)
            responses_with_tracking.append({
                'response': resp,
                'tracker': tracker,
            })
        
        ctx['active_sos'] = active_sos
        ctx['my_responses'] = responses_with_tracking
        ctx['pending_responses'] = my_responses.filter(response='pending').count()
        ctx['donor_details'] = donor_details
        
        return ctx


class DrivesView(TemplateView):
    """Blood donation drives listing"""
    template_name = "drives.html"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from drives.models import DonationDrive
        from django.utils import timezone
        
        # Get upcoming published drives
        today = timezone.now().date()
        ctx['upcoming_drives'] = DonationDrive.objects.filter(
            start_date__gte=today,
            status='published'
        ).order_by('start_date')[:20]
        
        return ctx
