# SmileCraft Full-Stack Clinic Website

## Run locally (Python 3.9+; no dependencies)

Mac / Linux:

```bash
cd SmileCraft_Fullstack
export ADMIN_TOKEN="replace-with-a-long-random-secret"
python3 server.py
```

Windows PowerShell:

```powershell
cd SmileCraft_Fullstack
$env:ADMIN_TOKEN="replace-with-a-long-random-secret"
python server.py
```

Visit http://localhost:8000 for the site and http://localhost:8000/admin for the admin dashboard. Enter the same token to see requests and change statuses. Records persist in `appointments.db` (created on first run). Keep the token and database private. Backup the database securely.

## Included
- Working appointment request API: `POST /api/appointments`
- SQLite persistent storage, server-side validation, basic per-IP rate limiting
- Admin request list and status management via token-protected endpoints
- Mobile-friendly existing frontend

## Before production
- Deploy the Python server on a persistent host (static hosting alone won't run the backend). Set `ADMIN_TOKEN` as a strong environment secret. Use HTTPS, backups, access controls, audit logs, privacy notice and a retention/deletion policy for patient contact data. Use a proper authenticated staff login for a real clinic; a shared token is only a starter admin mechanism.
- Add real clinic contact information and doctor details. Email/WhatsApp notifications, calendar availability, payment and actual appointment confirmation are **not** configured. Submission is only a request, not a confirmed booking.
- Do not collect medical histories or sensitive clinical records through this starter form.
