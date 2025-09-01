# LocationService (MVP)

FastAPI service providing live location updates and latest tracking snapshot for orders. This MVP uses an in-memory store and implements endpoints according to `openapi/location.yaml`.

## Endpoints

- POST /location/updates
  - Submit live location update from courier app
  - Body: LocationUpdate
  - Response: 202 Accepted

- GET /location/track/{orderId}
  - Get latest location and ETA for an order
  - Path: orderId (string)
  - Response: 200 LocationSnapshot | 404 Not found

Refer to `openapi/location.yaml` for the full schema.

## Run locally

1. Create and activate a virtual environment (optional).
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the service:
   ```
   python -m app
   ```
   Service listens on http://0.0.0.0:8107

OpenAPI docs:
- Swagger UI: http://localhost:8107/docs
- ReDoc: http://localhost:8107/redoc

## Notes

- This MVP uses an in-memory dictionary; all data resets when the process restarts.
- ETA is a placeholder for demonstration.
