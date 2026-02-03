## VeinLine — Blood Donation Platform (Django + DRF + MySQL + JWT)

VeinLine is a production-ready (local runnable) blood donation platform with:
- **Roles**: donor, patient, admin
- **Privacy**: donor phone hidden by default; revealed only after donor consent per SOS
- **SOS**: matching + SMS alerts + SMS YES/NO replies
- **Analytics**: Chart.js admin dashboard + REST analytics endpoint

---

## Tech stack

- **Backend**: Django, Django REST Framework, SimpleJWT
- **DB**: **MySQL** (via **PyMySQL** for easy Windows setup)
- **Frontend**: Django templates + Bootstrap 5 + Chart.js
- **Notifications**: SMS (Fast2SMS/Textlocal) + Email fallback (SMTP or console)

---

## Project structure

- `veinline_backend/`: Django project settings/urls
- `accounts/`: user roles + profile
- `donations/`: donor details + blood bank inventory
- `appointments/`: appointment slots, booking, health questionnaire
- `sos/`: SOS requests, responses, matching, SMS inbound webhook
- `analyticsapp/`: analytics API endpoint
- `webui/`: server-rendered dashboards
- `templates/`: Bootstrap UI
- `static/`: CSS assets

---

## Setup (Windows)

### 1) Create MySQL database

Create a database and user. Example (MySQL shell):

```sql
CREATE DATABASE veinline CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Optionally create a dedicated user instead of root:
-- CREATE USER 'veinline'@'localhost' IDENTIFIED BY 'strongpassword';
-- GRANT ALL PRIVILEGES ON veinline.* TO 'veinline'@'localhost';
FLUSH PRIVILEGES;
```

### 2) Create `.env`

Copy `.env.example` to `.env` and fill values:

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


