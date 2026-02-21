Here is the updated `README.md` in the exact professional format you requested. It highlights the dynamic field capabilities and secure document handling within the existing structure.

```markdown
# Partner Portal – Backend (Visa Business)

Django REST backend for a secure partner portal: partners manage their own applicants, documents, payments, commissions, and support tickets. Admin/staff manage all data.

## Features

- **Roles**: Partner (own data only), Admin/Staff (full access)
- **Partner registration & login** (JWT) with **admin approval workflow**: Partners must be approved by admin before they can log in (status: pending → approved)
- **Applicants**: Comprehensive visa profiles (passport, travel dates, biometrics) with **dynamic custom fields** via JSON (`extra_data`) to support varying country requirements.
- **Documents**: Secure upload per applicant with UUID obfuscation and strict type validation (PDF, JPG, PNG). Supports multiple documents per applicant. **Admin document verification** with approval/rejection and notes.
- **Payments**: Per applicant; receipt download
- **Commissions**: Per applicant; admin sets rate per partner and marks payouts
- **Reports**: Partner (own) and Admin (rankings, totals); CSV/PDF export
- **Support**: Ticket system; partner creates, admin replies
- **Dashboard**: Stats (applicants, docs, payments, commission)
- **Security**: RBAC, strict partner isolation, Axes brute-force protection, secure file uploads, audit logging

## Setup

1. **PostgreSQL**: Create a database (e.g. `portal`).
   ```bash
   # In psql or pgAdmin:
   CREATE DATABASE portal;

```

2. **Env**: In `.env` and set at least:
* `SECRET_KEY`, `PG_NAME`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`
* Or use a single `DATABASE_URL=postgresql://user:password@localhost:5432/portal`


3. **Install and run**:
```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

```



## API Overview

* **Auth**: `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/token/refresh/`, `GET /api/auth/me/`
* **Admin partners**: `GET /api/auth/partners/`, `GET/PATCH /api/auth/partners/<id>/` — List or manage all partners, update status/commission rate
  * **Partner approval**: `POST /api/auth/partners/<id>/approve/` — Admin endpoint to approve a pending partner (change status to approved). Partners with status `pending` cannot log in.
* **Dashboard**: `GET /api/dashboard/` (admin can add `?partner_id=` for a partner)
* **Applicants**: `GET/POST /api/applicants/`, `GET/PUT/PATCH/DELETE /api/applicants/<id>/`
* *Note: Supports `extra_data` JSON object for custom fields.*
* **Documents**: `GET/POST /api/documents/`, `GET/PUT/PATCH/DELETE /api/documents/<id>/`, `GET /api/documents/<id>/download/`
  * **Admin document verification**: `PATCH /api/documents/<id>/` with `status` (pending/approved/rejected) and optional `notes` for rejection reason. Admins see all documents across all partners.
* **Payments**: `GET/POST /api/payments/`, `GET /api/payments/<id>/download-receipt/`
* **Commissions**: `GET /api/commissions/` (admin can POST/PATCH/DELETE)
* **Reports**: `GET /api/reports/partner/`, `GET /api/reports/admin/`, export CSV/PDF endpoints
* **Support**: `GET/POST /api/tickets/`, `GET/PATCH /api/tickets/<id>/`, `POST /api/tickets/<id>/reply/`

All authenticated endpoints use JWT: `Authorization: Bearer <access_token>`.

## How to test

1. **Create superuser (admin):**
```bash
python manage.py createsuperuser

```


Use email as username (e.g. `admin@portal.com`). You'll need a password (min 12 chars).
2. **Start the server:**
```bash
python manage.py runserver

```


API base: `http://127.0.0.1:8000/`
3. **Register a partner (no auth):**
```bash
curl -X POST [http://127.0.0.1:8000/api/auth/register/](http://127.0.0.1:8000/api/auth/register/) -H "Content-Type: application/json" -d "{\"email\":\"partner@test.com\",\"password\":\"SecurePass123!\",\"company_name\":\"Test Agency\",\"contact_name\":\"John\"}"

```


4. **Login (get JWT):**
```bash
curl -X POST [http://127.0.0.1:8000/api/auth/login/](http://127.0.0.1:8000/api/auth/login/) -H "Content-Type: application/json" -d "{\"email\":\"partner@test.com\",\"password\":\"SecurePass123!\"}"

```


Copy `access` from the response.
5. **Dashboard (as partner):**
```bash
curl [http://127.0.0.1:8000/api/dashboard/](http://127.0.0.1:8000/api/dashboard/) -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

```


6. **Create applicant (with dynamic fields):**
Partners can send standard fields plus an `extra_data` object for custom requirements (e.g., father's name, previous visa number) without backend schema changes.
```bash
curl -X POST [http://127.0.0.1:8000/api/applicants/](http://127.0.0.1:8000/api/applicants/) \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "passport_number": "A12345678",
    "visa_type": "Tourist",
    "destination_country": "UAE",
    "status": "new",
    "extra_data": {
      "father_name": "John Doe",
      "previous_visa_ref": "US-998877"
    }
  }'

```


7. **Upload Document:**
Attach files (PDF/JPG/PNG) to an applicant.
```bash
curl -X POST [http://127.0.0.1:8000/api/documents/](http://127.0.0.1:8000/api/documents/) \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "applicant=<APPLICANT_UUID>" \
  -F "document_type=passport" \
  -F "file=@/path/to/passport.jpg"

```

## Optional: Use S3 / Object Storage for media files (recommended)

For production it's recommended to store uploaded files in object storage (S3, GCS, Azure Blob) and keep only metadata in the database. To enable AWS S3 storage using `django-storages`:

1. Install updated requirements:
```bash
pip install -r requirements.txt
```

2. Add these env vars to your `.env` (example):
```
USE_S3=true
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
# Optional if using a custom domain or CDN
AWS_S3_CUSTOM_DOMAIN=cdn.example.com
# Optional for S3-compatible providers
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com
```

3. With `USE_S3=true` Django will use `django-storages` to store uploaded files to S3 while the `Document` model continues to store metadata (file path, original filename, status) in the DB.

Notes:
- You can continue using the existing `POST /api/documents/` endpoint; Django will save the file to S3 automatically if `USE_S3` is enabled.
- For large-scale traffic consider using presigned uploads so clients post directly to S3 and your server only stores metadata.


8. **Admin panel:** Open `http://127.0.0.1:8000/admin/` and log in with the superuser. Approve partners, manage applicants, documents, payments, commissions, tickets.

## Security

* **Partner data isolation**: every list/detail is filtered by partner; direct URLs to other partners’ data return 404/403.
* **File uploads**: Filenames are obfuscated to UUIDs to prevent RCE. Whitelisted extensions (PDF, JPG, PNG) and size limits enforced.
* **Login**: Axes limits failed attempts (5 failures, 1-hour cooldown).
* **Passwords**: Django validators (length, common passwords, etc.).
* **HTTPS** and secure cookies recommended in production.

```

```