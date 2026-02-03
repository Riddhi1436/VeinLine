# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

VeinLine is a blood donation platform built with Django and Django REST Framework. It connects donors, patients, and blood banks through:

- **Role-based system**: donor, patient, admin
- **Privacy-first SOS**: Donor phone numbers hidden by default; revealed only after explicit consent per SOS request
- **SMS bidirectional flow**: Alerts sent to donors, replies processed via webhook
- **Appointment booking**: Slot management with health questionnaire and eligibility checks
- **Analytics dashboard**: Admin panel with Chart.js visualizations

**Tech Stack**: Django 5.1.6, Django REST Framework, SimpleJWT, MySQL (via PyMySQL), Bootstrap 5, Chart.js

## Development Commands

### Environment Setup

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
.\venv\Scripts\pip install -r requirements.txt

# Create .env from template
Copy-Item .env.example .env
# Then edit .env with actual values
```

### Database Management

```powershell
# Run migrations
.\venv\Scripts\python manage.py migrate

# Create superuser
.\venv\Scripts\python manage.py createsuperuser

# Make migrations after model changes
.\venv\Scripts\python manage.py makemigrations

# Reset specific app migrations (development only)
.\venv\Scripts\python manage.py migrate <app_name> zero
```

### Running the Server

```powershell
# Development server
.\venv\Scripts\python manage.py runserver

# Collect static files (before deployment)
.\venv\Scripts\python manage.py collectstatic --noinput
```

### Testing

```powershell
# Run all tests
.\venv\Scripts\python manage.py test

# Run tests for specific app
.\venv\Scripts\python manage.py test <app_name>

# Run standalone test scripts
.\venv\Scripts\python test_api_endpoints.py
.\venv\Scripts\python test_sos_match.py
.\venv\Scripts\python test_appointment_flow.py
```

### Django Shell

```powershell
# Interactive shell
.\venv\Scripts\python manage.py shell

# Shell with custom imports
.\venv\Scripts\python manage.py shell_plus  # if django-extensions is installed
```

### Utility Scripts

```powershell
# Inspect donor matching
.\venv\Scripts\python scripts\inspect_donors.py

# Test matching algorithm
.\venv\Scripts\python scripts\test_match.py
```

## Architecture

### App Structure

VeinLine follows Django's app-based architecture:

- **accounts/**: User authentication, profile, and role management (donor/patient/admin)
  - Custom Profile model extends Django User with role, phone_e164, city, area
  - UserRole enum: DONOR, PATIENT, ADMIN

- **core/**: Shared constants and services
  - `constants.py`: BloodGroup definitions (O+, O-, A+, A-, B+, B-, AB+, AB-)
  - `services/sms.py`: SMS delivery abstraction (Fast2SMS/Textlocal)
  - `services/emailing.py`: Email notifications

- **donations/**: Donor profiles, blood bank inventory, badges, feedback
  - DonorDetails: blood_group, city, area, is_available, last_donated_at, geo coordinates
  - DonorStatistics: gamification (badges, points, leaderboard rank, donation streak)
  - BloodBankInventory: units_available per city+blood_group
  - DonorFeedback: patient ratings and thank-you messages

- **sos/**: Emergency blood requests and responses
  - SOSRequest: blood_group_needed, city, area, hospital_name, priority, sms_reply_token
  - SOSResponse: donor response (yes/no/pending), consent_to_share_contact, channel (web/SMS)
  - `services.py`: Blood compatibility matching logic using DEFAULT_COMPATIBILITY dict
  - Privacy-enforced: contact revealed only after donor consent + patient reveal request

- **appointments/**: Appointment slot booking system
  - AppointmentSlot: blood_bank, city, date/time, max_donors, booked_donors
  - Appointment: donor booking with confirmation, health questionnaire tracking
  - HealthQuestionnaire: 20+ eligibility questions (fever, diseases, recent procedures, weight, hemoglobin)
  - `check_eligibility()`: Automated eligibility validation

- **notifications/**: Multi-channel notification system
  - NotificationService: Create and send notifications (in-app, email, SMS, push)
  - NotificationType: SOS_REQUEST, SOS_RESPONSE, APPOINTMENT_REMINDER, NEW_BADGE, etc.
  - Linked to content objects via ContentType (generic foreign key)

- **analyticsapp/**: Analytics API endpoint
  - AdminAnalyticsView: donors by blood group, activity stats, SOS stats, inventory
  - Requires admin permissions

- **webui/**: Server-rendered dashboards with Bootstrap templates
  - Role-specific dashboards: donor, patient, admin
  - Chart.js integration for admin analytics
  - Leaderboard, appointments, blood banks, eligibility checker

- **veinline_backend/**: Django project settings and root URL config

### Key Architectural Patterns

**Blood Compatibility Matching**  
Located in `sos/services.py`:
- `DEFAULT_COMPATIBILITY` dict maps recipient blood groups → allowed donor groups
- Falls back to BloodGroupCompatibility model if present
- Matching filters: compatible blood group + city (strict by default) + is_available

**Privacy Model**  
Donor phone numbers stored in `Profile.phone_e164` (E.164 format):
- Never exposed in donor list responses
- SOSResponse has `donor_consented_to_share_contact` boolean
- Patient must call `/api/sos/responses/{id}/reveal_contact/` endpoint
- Contact revealed only if donor explicitly consented for that specific SOS

**SMS Flow**  
Outbound (alerts):
- SOS matching sends alerts via `core.services.sms.send_sms()`
- Message includes reply token: "YES <token>" or "NO <token>" or "YES SHARE <token>"

Inbound (webhook):
- Endpoint: `POST /api/sms/inbound/`
- Payload: `{"from_phone": "+911234567890", "message": "YES SHARE ab12cd34"}`
- Parses token to find SOSRequest, updates SOSResponse with consent

**Gamification System**  
DonorStatistics tracks:
- total_donations, total_lives_saved, sos_responses
- Badges (first_donation, five_donations, hero, lifesaver, consistent, emergency_responder, etc.)
- Leaderboard: points awarded for donations, badges, SOS responses
- `check_badges()` auto-awards based on milestones

**Authentication**  
- JWT via djangorestframework-simplejwt
- Token endpoints: `/api/auth/token/` (obtain), `/api/auth/token/refresh/`
- Google OAuth via django-allauth (`/accounts/google/login/`)
- Session-based for web UI (LoginView, RegisterView, LogoutViewCustom)

## Database

**Primary**: MySQL (recommended)
- Connection via PyMySQL (no native build tools required on Windows)
- Configured in settings.py based on `DB_ENGINE` env var

**Fallback**: SQLite (development only)
- Set `DB_ENGINE=sqlite` in .env

**Indexes**: Optimized for common queries
- SOS: (status, blood_group_needed, city), (priority, status)
- DonorDetails: (blood_group, city, is_available), (city, area)
- Appointments: (date, city, status), (donor, status)

## Environment Configuration

Required `.env` variables:
- `DJANGO_SECRET_KEY`: Django secret
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`

Optional:
- `SMS_PROVIDER`: fast2sms | textlocal
- `SMS_API_KEY`: API key for SMS gateway
- `SMS_SENDER`: Sender ID (default: VEINLN)
- `CITY_MATCH_STRICT`: 1 (strict city matching) | 0 (loose)
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`: For Google OAuth

Email settings:
- `EMAIL_BACKEND`: Use console backend for development, SMTP for production
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

## REST API Structure

Base URL: `/api/`

**Authentication**:
- POST `/api/auth/register/` - Register new user
- POST `/api/auth/token/` - Get JWT tokens
- POST `/api/auth/token/refresh/` - Refresh access token
- GET `/api/auth/me/` - Get current user profile (requires Bearer token)

**SOS Flow**:
- POST `/api/sos/requests/` - Create SOS request
- POST `/api/sos/requests/{id}/match/` - Match and alert donors
- GET `/api/sos/responses/` - List responses (filtered by role)
- POST `/api/sos/responses/{id}/respond/` - Donor responds (yes/no + consent)
- POST `/api/sos/responses/{id}/reveal_contact/` - Patient reveals donor contact (if consented)

**Appointments**:
- GET `/api/slots/upcoming/` - List available slots (public, no auth)
- GET `/api/slots/by_city/?city=<city>&date=<date>` - Filter slots
- POST `/api/my-appointments/` - Book appointment (requires auth)
- GET `/api/my-appointments/` - List user's appointments
- POST `/api/appointments/{id}/health-questionnaire/` - Submit health form

**Notifications**:
- GET `/api/notifications/` - List user notifications
- POST `/api/notifications/{id}/mark-read/` - Mark as read

**Analytics** (admin only):
- GET `/api/analytics/` - Dashboard stats

## Important Notes

**Windows Development**:
- Use PowerShell commands throughout (`.ps1` scripts)
- Virtual environment activation: `.\venv\Scripts\Activate.ps1`
- Path format: Windows backslashes or forward slashes

**SMS Integration**:
- In development, set empty `SMS_API_KEY` - SMS sending will log and skip
- In production, configure Fast2SMS or Textlocal credentials
- Webhook endpoint `/api/sms/inbound/` requires adapter for gateway-specific payload format

**Testing**:
- Standalone test scripts (`test_*.py`) directly use Django setup, not pytest
- Run from project root with activated venv

**Static Files**:
- Development: served via `STATICFILES_DIRS = [BASE_DIR / "static"]`
- Production: use `collectstatic` with WhiteNoise compression

**Migrations**:
- Always run `makemigrations` after model changes
- Migration dependencies: sos depends on core (BloodGroup constants)

**PyMySQL Setup**:
- Django uses PyMySQL adapter (pure Python, no C dependencies)
- Configured in settings.py: `ENGINE: django.db.backends.mysql`
