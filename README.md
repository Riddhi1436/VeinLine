# VeinLine — Blood Donation Platform

A production-ready Django-based blood donation platform connecting donors, patients, and blood banks with privacy-first SOS emergency blood requests, smart matching, and gamification.

**Key Features**:
- 🩸 **Blood Group Compatibility Matching** - Automatically matches donors to recipients
- 🔐 **Privacy-First Architecture** - Donor phone numbers hidden by default, revealed only with explicit consent
- 📱 **Bidirectional SMS** - Send alerts to donors, receive YES/NO replies via webhook
- 📅 **Appointment Booking** - Slots with health questionnaire & eligibility checks
- 🏆 **Gamification System** - Badges, points, leaderboard, donation streaks
- 📊 **Admin Analytics** - Chart.js dashboards with donor stats, blood inventory, SOS metrics
- 🔐 **Role-Based Access** - Donor, Patient, and Admin roles with JWT authentication
- 🔔 **Multi-Channel Notifications** - SMS, Email, In-app notifications

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Django 5.1.6, Django REST Framework |
| **Database** | MySQL (via PyMySQL for Windows compatibility) |
| **Authentication** | SimpleJWT, Google OAuth (via django-allauth) |
| **Frontend** | Django Templates, Bootstrap 5, Chart.js |
| **SMS/Notifications** | Fast2SMS/Textlocal API, SMTP/Console Email |

---

## Project Architecture

```
VeinLine/
├── veinline_backend/          # Django settings & root URL config
├── accounts/                  # User authentication, profiles, roles
├── core/                      # Shared constants, SMS/email services
├── donations/                 # Donor profiles, blood bank inventory, badges
├── sos/                       # Emergency requests, responses, matching
├── appointments/              # Slots, booking, health questionnaire
├── notifications/             # Multi-channel notification system
├── analyticsapp/              # Analytics API & admin dashboard
├── webui/                     # Server-rendered role-based dashboards
├── templates/                 # Bootstrap 5 HTML templates
├── static/                    # CSS, JS assets
├── scripts/                   # Utility scripts
└── requirements.txt           # Python dependencies
```

### Core App Responsibilities

| App | Purpose |
|-----|---------|
| **accounts** | User roles (DONOR/PATIENT/ADMIN), profile management, JWT auth |
| **core** | Blood group constants, SMS gateway abstraction, email service |
| **donations** | Donor details, blood bank inventory, gamification badges & stats |
| **sos** | Emergency blood requests, donor matching, SMS webhook handling, privacy logic |
| **appointments** | Appointment slots, booking system, health eligibility questionnaire |
| **notifications** | Notification service across SMS, email, in-app, and push |
| **analyticsapp** | Admin-only analytics API with Chart.js dashboard integration |
| **webui** | Role-specific dashboards and server-rendered pages |

---

## Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+ (or SQLite for development)
- Windows PowerShell / Bash terminal

### 1) Set Up Virtual Environment

```powershell
# On Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2) Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure Environment

```powershell
# Copy the example .env file
Copy-Item .env.example .env

# Edit .env with your configuration
# Required variables:
#   - DJANGO_SECRET_KEY (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
#   - Database credentials (MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD)
#   - SMS API key and provider (optional)
#   - Email settings (optional)
```

### 4) Create MySQL Database

```sql
CREATE DATABASE veinline CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Optionally create dedicated user:
CREATE USER 'veinline'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON veinline.* TO 'veinline'@'localhost';
FLUSH PRIVILEGES;
```

### 5) Run Migrations

```powershell
python manage.py migrate
```

### 6) Create Superuser (Admin)

```powershell
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 7) Load Sample Data (Optional)

```powershell
# Create sample appointment slots
python check_and_create_slots.py

# Or use test scripts
python test_features.py
```

### 8) Start Development Server

```powershell
python manage.py runserver
```

Access the platform:
- **Web UI**: http://localhost:8000/
- **Admin Dashboard**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/

---

## Environment Configuration

### Required Variables

```ini
# Django
DJANGO_SECRET_KEY=<django-secret-key>
DEBUG=True  # Set to False in production

# Database
DB_ENGINE=mysql  # or 'sqlite' for development
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=veinline
MYSQL_USER=veinline
MYSQL_PASSWORD=<password>

# SMS (optional - leave empty to skip SMS in development)
SMS_PROVIDER=fast2sms  # or 'textlocal'
SMS_API_KEY=<api-key>
SMS_SENDER=VEINLN

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<app-password>

# Optional Features
CITY_MATCH_STRICT=1  # Strict city matching for SOS (1) or loose (0)
GOOGLE_OAUTH_CLIENT_ID=<oauth-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<oauth-secret>
```

---

## Core Features

### 🩸 Blood Group Compatibility

Automatic matching using compatibility matrix (O+ donors → all recipients, AB- recipients → O donors only, etc.)

```python
# Example compatibility matching
donor_blood_group = "O+"
recipient_blood_group = "AB+"
# System automatically determines if donor can help
```

### 🔐 Privacy-First SOS System

1. **Patient Creates SOS Request** → blood group, hospital, priority
2. **System Matches Compatible Donors** → by blood group & location
3. **SMS Alerts Sent** → "Your blood type needed in [hospital]. YES/NO?"
4. **Donor Responds** → "YES SHARE <token>" (consents to share contact)
5. **Patient Reveals Contact** → Only if donor consented for that specific SOS

### 📱 Bidirectional SMS Flow

**Outbound**: SOS alerts with reply tokens
```
"Your blood type O+ needed at City Hospital. Reply: YES <token> or NO <token>"
```

**Inbound**: Webhook processes donor responses
```
POST /api/sms/inbound/
{ "from_phone": "+911234567890", "message": "YES SHARE ab12cd34" }
```

### 📅 Appointment Booking

1. Browse available slots by city & date
2. Submit health questionnaire (20+ eligibility questions)
3. Automatic eligibility validation
4. Confirm appointment
5. Receive appointment reminders

**Eligibility Questions Cover**:
- Recent infections, surgeries, medications
- Weight, hemoglobin levels
- Lifestyle factors (tattoos, piercings)
- Travel history

### 🏆 Gamification

**Donor Points & Badges**:
- Badges: First Donation, Five Donations, Hero, Lifesaver, Consistent, Emergency Responder
- Leaderboard: Points awarded for donations, badges, SOS responses
- Streak: Days of consistent donations

---

## API Endpoints

### Authentication

```http
POST   /api/auth/register/              # Register new user
POST   /api/auth/token/                 # Get JWT tokens
POST   /api/auth/token/refresh/         # Refresh access token
GET    /api/auth/me/                    # Get current user (requires Bearer token)
```

### SOS (Emergency Requests)

```http
POST   /api/sos/requests/               # Create SOS request
POST   /api/sos/requests/{id}/match/    # Match & alert donors
GET    /api/sos/responses/              # List responses (role-filtered)
POST   /api/sos/responses/{id}/respond/ # Donor responds (yes/no + consent)
POST   /api/sos/responses/{id}/reveal_contact/ # Patient reveals donor contact
```

### Appointments

```http
GET    /api/slots/upcoming/             # List available slots (public)
GET    /api/slots/by_city/?city=&date=  # Filter slots by city/date
POST   /api/my-appointments/            # Book appointment (auth required)
GET    /api/my-appointments/            # List user's appointments
POST   /api/appointments/{id}/health-questionnaire/ # Submit health form
```

### Notifications

```http
GET    /api/notifications/              # List user notifications
POST   /api/notifications/{id}/mark-read/ # Mark notification as read
```

### Analytics (Admin Only)

```http
GET    /api/analytics/                  # Dashboard stats
```

---

## Development Commands

### Database Management

```powershell
# Run migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Reset app migrations (development only)
python manage.py migrate <app_name> zero

# View migration status
python manage.py showmigrations
```

### Testing

```powershell
# Run all tests
python manage.py test

# Run app-specific tests
python manage.py test <app_name>

# Run standalone test scripts
python test_api_endpoints.py
python test_sos_match.py
python test_appointment_flow.py
python test_otp_registration.py
```

### Django Shell

```powershell
# Interactive Python shell with Django models
python manage.py shell

# Example commands in shell
from accounts.models import Profile
from donations.models import DonorDetails
users = Profile.objects.filter(role='DONOR')
```

### Utility Scripts

```powershell
# Inspect donor matching for a specific SOS
python scripts/inspect_donors.py

# Test the matching algorithm
python scripts/test_match.py

# Check database connection
python check_connection.py

# Create sample appointment slots
python check_and_create_slots.py

# Test SOS SMS integration
python check_sms_debug.py
```

### Static Files (Production)

```powershell
# Collect static files for deployment
python manage.py collectstatic --noinput
```

---

## Important Notes

### Windows Development

- Use PowerShell commands throughout
- Virtual environment activation: `.\venv\Scripts\Activate.ps1`
- Path format: Windows backslashes or forward slashes work in Django

### SMS Integration

- **Development**: Leave `SMS_API_KEY` empty — SMS will log instead of sending
- **Production**: Configure Fast2SMS or Textlocal credentials
- **Webhook**: Gateway adapter needed for `/api/sms/inbound/` payload parsing

### Database

- **Primary**: MySQL (recommended for production)
- **Alternative**: SQLite (development only, set `DB_ENGINE=sqlite` in .env)
- **PyMySQL**: Pure Python adapter, no native build tools needed on Windows

### Static Files & Deployment

- **Development**: Django serves files directly from `STATICFILES_DIRS`
- **Production**: Run `collectstatic` with WhiteNoise compression for CDN/static file serving

---

## Project Files Reference

Key documentation files in the project:

- [AGENTS.md](AGENTS.md) — Detailed architecture & development guide
- [START_HERE.md](START_HERE.md) — Quick reference for common tasks
- [OTP_REGISTRATION_COMPLETE.md](OTP_REGISTRATION_COMPLETE.md) — OTP authentication setup
- [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) — Google OAuth integration
- [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md) — SMS configuration & testing
- [APPOINTMENT_SYSTEM_COMPLETE.md](APPOINTMENT_SYSTEM_COMPLETE.md) — Appointment feature guide

---

## Troubleshooting

### Database Connection Issues

```powershell
# Test database connection
python check_connection.py

# Check MySQL service is running
# Windows: Services app → look for MySQL
# macOS: brew services list
# Linux: systemctl status mysql
```

### SMS Not Sending

```powershell
# Check SMS gateway credentials in .env
# If SMS_API_KEY is empty, SMS will only log (development mode)
# Run test to see SMS output:
python check_sms_debug.py
```

### Migration Errors

```powershell
# Reset migrations for an app (development only - WILL DELETE DATA)
python manage.py migrate <app_name> zero

# Recreate migrations
python manage.py makemigrations <app_name>
python manage.py migrate <app_name>
```

### Port Already in Use

```powershell
# Run on different port
python manage.py runserver 8001
```

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Commit with clear messages: `git commit -m "Add feature description"`
4. Push and create a pull request

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or contributions, please refer to [AGENTS.md](AGENTS.md) for detailed architecture documentation and troubleshooting guides.

- **Required**: `DJANGO_SECRET_KEY`, `MYSQL_*`
- **Optional**: `SMS_*`, SMTP email settings

### 3) Install dependencies

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### 4) Run migrations + seed compatibility

```powershell
.\venv\Scripts\python manage.py migrate
```

### 5) Create an admin user

```powershell
.\venv\Scripts\python manage.py createsuperuser
```

### 6) Run the server

```powershell
.\venv\Scripts\python manage.py runserver
```

Open:
- **Home/UI**: `http://127.0.0.1:8000/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`

---

## REST API (JWT)

### Auth

- **Register**: `POST /api/auth/register/`
- **Token**: `POST /api/auth/token/`
- **Me**: `GET /api/auth/me/` (Bearer token)

### SOS flow (patient)

1) Create SOS:
- `POST /api/sos/requests/`

2) Match + send alerts:
- `POST /api/sos/requests/{id}/match/`

3) View responses:
- `GET /api/sos/responses/`

4) Reveal donor contact (only if donor consented):
- `POST /api/sos/responses/{responseId}/reveal_contact/`

### Donor response

- `POST /api/sos/responses/{responseId}/respond/`

Body:

```json
{
  "response": "yes",
  "consent_to_share_contact": true
}
```

### Appointment booking

#### 1. Get available slots (public access, no auth required)

```bash
GET /api/slots/upcoming/
GET /api/slots/by_city/?city=Delhi&date=2026-02-15
```

Response: List of available appointment slots with:
- `blood_bank`: Name of the blood bank
- `city`, `address`: Location
- `date`, `start_time`, `end_time`: Schedule
- `remaining_slots`: Available spots
- `is_available_for_booking`: Boolean

#### 2. Book an appointment (authenticated user required)

```bash
POST /api/my-appointments/
Authorization: Bearer {access_token}

{
  "slot_id": 123
}
```

Response (201): Appointment object with:
- `id`: Appointment ID
- `status`: "scheduled"
- `slot_details`: Full slot information

#### 3. Submit health questionnaire

```bash
POST /api/appointments/{appointment_id}/health-questionnaire/
Authorization: Bearer {access_token}

{
  "has_fever": false,
  "has_cold_or_cough": false,
  "is_pregnant": false,
  "is_breastfeeding": false,
  "has_hiv_or_aids": false,
  "has_hepatitis": false,
  "has_cancer": false,
  "has_bleeding_disorder": false,
  "has_high_blood_pressure": false,
  "has_diabetes": false,
  "has_heart_condition": false,
  "recent_tattoo_or_piercing": false,
  "recent_surgery": false,
  "recent_blood_transfusion": false,
  "recent_vaccination": false,
  "takes_blood_thinners": false,
  "takes_antibiotics": false,
  "weight_kg": 70.5,
  "hemoglobin_level": 14.2,
  "additional_notes": "Any relevant medical info"
}
```

Response (201): Health questionnaire with:
- `id`: Questionnaire ID
- `is_eligible`: true/false based on eligibility criteria

#### 4. Get user's appointments

```bash
GET /api/my-appointments/
Authorization: Bearer {access_token}
```

Response: List of user's booked appointments with full details

---

## SMS integration

### Outbound alerts

Set:
- `SMS_PROVIDER=fast2sms` or `textlocal`
- `SMS_API_KEY=...`

VeinLine sends messages like:
`YES <token>` or `NO <token>` (optional: `YES SHARE <token>`)

### Inbound webhook (SMS replies)

Endpoint:
- `POST /api/sms/inbound/`

Expected JSON:

```json
{
  "from_phone": "+911234567890",
  "message": "YES SHARE ab12cd34"
}
```

Note: Each SMS gateway has its own webhook format; in production you can map their payload to this JSON or add a small adapter endpoint.

---

## Notes

- MySQL driver: we use **PyMySQL** to avoid native build tools on Windows.
- You can temporarily run with SQLite by setting `DB_ENGINE=sqlite` in `.env`, but **MySQL is the default and recommended** for VeinLine.


