# Ocean Freight D&D Dispute Portal

Production-oriented Next.js 15 frontend for the Ocean Freight Detention and Demurrage Dispute Engine.

## Routes

- `/` - animated maritime product overview
- `/dashboard` - live invoice upload, processing status, ledger, and findings
- `/contact` - enterprise contact experience

## Run locally

1. Copy `.env.example` to `.env.local`.
2. Start FastAPI on `http://localhost:8000`.
3. Allow `http://localhost:3000` in the FastAPI CORS configuration.
4. Run:

   ```bash
   npm install
   npm run dev
   ```

5. Open `http://localhost:3000`.

## Environment

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=local-dev
```

The browser communicates only with FastAPI. It never accesses PostgreSQL, Redis, Celery, Gemini, or object storage directly.

## Backend contract

- `POST /upload/` accepts multipart form field `file` and returns `case_id`, `document_id`, `status`, and `message`.
- `GET /status/{document_id}` returns the extraction run status and is polled every two seconds until `READY_FOR_APPROVAL` or `FAILED`.
- `GET /results/{document_id}` returns the deterministic KPI totals, day-ledger rows, and findings after the extraction status reaches `READY_FOR_APPROVAL`.

The dashboard does not calculate charges and contains no fallback demonstration result. All displayed audit values come from the FastAPI results contract.

## Verification

```bash
npm run typecheck
npm run build
```
