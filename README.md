# 0711-Build: OpenHands Add-on Standalone Service

A thin, reliable bridge between your platform and your self-hosted OpenHands instance at `http://34.40.104.64:3020`.

## What it does

- **Accepts build/run requests** from any client with a valid token
- **Starts OpenHands conversations** with compiled prompts and optional repositories
- **Persists run state** in PostgreSQL database
- **Polls OpenHands** for status and exposes clean progress endpoints
- **Handles GitHub/GitLab webhooks** to mark runs complete when PRs/MRs are created

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
OPENHANDS_BASE_URL=http://34.40.104.64:3020
OPENHANDS_TOKEN=your_token_here
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/runner
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations (optional, tables are auto-created)
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Docker

```bash
# Build and run
docker build -t openhands-runner .
docker run -p 8080:8080 --env-file .env openhands-runner
```

## API Usage

### Start a Run

```bash
curl -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "compiled_prompt": "Create a simple Python web server",
    "repository": "owner/repo",
    "metadata": {"branch": "feature-branch"}
  }'
```

Response:
```json
{
  "run_id": "run_abc123",
  "status": "QUEUED"
}
```

### Check Run Status

```bash
curl http://localhost:8080/runs/run_abc123
```

Response:
```json
{
  "run_id": "run_abc123",
  "status": "RUNNING",
  "percent": 45,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "metadata": {"branch": "feature-branch"}
}
```

### Get Detailed Run Information

```bash
curl http://localhost:8080/runs/run_abc123/detail
```

### List Runs

```bash
# All runs
curl http://localhost:8080/runs

# Filter by project
curl http://localhost:8080/runs?project_id=my-project

# Filter by status
curl http://localhost:8080/runs?status=COMPLETED
```

### Health Check

```bash
curl http://localhost:8080/health
```

## Deployment

### Google Cloud Run (Recommended)

1. **Set up GitHub Secrets:**
   - `GCP_PROJECT`: Your Google Cloud project ID
   - `GCP_REGION`: Deployment region (e.g., `us-central1`)
   - `WIF_PROVIDER`: Workload Identity Federation provider
   - `DEPLOYER_SA`: Service account email for deployment
   - `DATABASE_URL`: PostgreSQL connection string
   - `OPENHANDS_BASE_URL`: Your OpenHands instance URL
   - `OPENHANDS_TOKEN`: OpenHands API token (optional)
   - `GITHUB_WEBHOOK_SECRET`: GitHub webhook secret (optional)

2. **Push to main branch** - GitHub Actions will automatically deploy

3. **Manual deployment:**
   ```bash
   gcloud run deploy openhands-runner \
     --source . \
     --region=us-central1 \
     --allow-unauthenticated \
     --set-env-vars="OPENHANDS_BASE_URL=http://34.40.104.64:3020,DATABASE_URL=postgresql://..."
   ```

### Alternative: Cloud Run YAML

```bash
# Update cloudrun.yaml with your project ID and secrets
gcloud run services replace cloudrun.yaml --region=us-central1
```

## Database Setup

### PostgreSQL on Google Cloud SQL

The provided connection details:
- **Instance**: `universe-vm:europe-west3:postgresql-0711-ai`
- **Public IP**: `34.107.63.251`
- **Private IP**: `34.159.4.248`
- **Port**: `5432`

Connection string format:
```
postgresql+psycopg2://username:password@34.107.63.251:5432/database_name
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Webhooks

### GitHub Webhook Setup

1. Go to your repository settings → Webhooks
2. Add webhook URL: `https://your-service-url/webhooks/github`
3. Select "Pull requests" events
4. Set the secret to match `GITHUB_WEBHOOK_SECRET`

The service will automatically mark runs as completed when PRs are opened.

## Security Considerations

- **Database**: Use connection pooling and SSL connections
- **API Access**: Consider adding authentication middleware for production
- **Webhooks**: Always verify webhook signatures
- **Network**: Deploy OpenHands on a private network when possible
- **Secrets**: Use Google Secret Manager or similar for sensitive data

## Monitoring

### Health Checks

The service includes built-in health checks:
- `/health` - Service and OpenHands connectivity
- Docker health check every 30 seconds
- Cloud Run readiness/liveness probes

### Logging

Structured logging with configurable levels:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Metrics

Consider adding:
- Prometheus metrics endpoint
- Cloud Monitoring integration
- Custom dashboards for run success rates

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Code Formatting

```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/
```

### Project Structure

```
0711-Build/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── config.py            # Settings and environment variables
│   ├── models.py            # SQLAlchemy models
│   ├── db.py                # Database session management
│   ├── schemas.py           # Pydantic request/response models
│   ├── clients/
│   │   └── openhands.py     # OpenHands HTTP client
│   ├── services/
│   │   ├── orchestrator.py  # Run orchestration logic
│   │   └── artifacts.py     # Artifact management
│   └── webhooks/
│       └── github.py        # GitHub webhook handlers
├── migrations/              # Alembic database migrations
├── tests/                   # Test files
├── .github/workflows/       # GitHub Actions
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

### Common Issues

1. **OpenHands Connection Failed**
   - Check `OPENHANDS_BASE_URL` is correct
   - Verify network connectivity
   - Check if authentication token is required

2. **Database Connection Issues**
   - Verify `DATABASE_URL` format
   - Check database server is accessible
   - Ensure database exists and user has permissions

3. **Webhook Not Working**
   - Verify webhook URL is publicly accessible
   - Check `GITHUB_WEBHOOK_SECRET` matches
   - Review webhook delivery logs in GitHub

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with auto-reload
uvicorn app.main:app --reload --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.