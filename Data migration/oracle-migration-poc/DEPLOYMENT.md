# Deployment Guide - Oracle Migration POC

## Quick Start (5 Minutes)

### Prerequisites

- Docker Desktop installed and running
- Azure OpenAI API access
- 4GB RAM available
- Windows 10/11, macOS, or Linux

### Step-by-Step Setup

**1. Clone or extract the project**
```bash
cd oracle-migration-poc
```

**2. Configure Azure OpenAI**

Edit `.env` file and add your credentials:
```bash
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**3. Run setup script**

**Windows:**
```cmd
setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**4. Access the application**

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**5. Start migrating!**

The application will run in mock mode by default, so you can demo the full workflow without Oracle databases.

---

## Detailed Deployment Options

### Option 1: Docker Compose (Recommended for POC)

**Advantages:**
- Simplest setup
- Isolated environment
- Easy cleanup

**Commands:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

Access at http://localhost:3000

### Option 3: Production Deployment

**Cloud Options:**
- Azure App Service + Azure OpenAI
- AWS ECS/Fargate + Bedrock
- Google Cloud Run + Vertex AI
- Kubernetes cluster

**Production Checklist:**
- [ ] Use PostgreSQL/MongoDB for state
- [ ] Configure Redis for caching
- [ ] Set up load balancer
- [ ] Enable HTTPS/TLS
- [ ] Configure monitoring (Prometheus, Grafana)
- [ ] Set up log aggregation (ELK, Splunk)
- [ ] Implement backup strategy
- [ ] Configure auto-scaling
- [ ] Set up CI/CD pipeline
- [ ] Enable authentication (OAuth2, SAML)

---

## Configuration

### Environment Variables

**Required:**
```bash
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Optional:**
```bash
# Backend
BACKEND_PORT=8000
LOG_LEVEL=INFO
ENABLE_MOCK_MODE=true

# Database (when not using mock mode)
ORACLE_SOURCE_HOST=localhost
ORACLE_SOURCE_PORT=1521
ORACLE_SOURCE_SERVICE=ORCL19C
ORACLE_SOURCE_USER=migration_user
ORACLE_SOURCE_PASSWORD=password

# Similar for intermediate and target databases
```

### Mock Mode vs Real Databases

**Mock Mode (Default):**
- Set `ENABLE_MOCK_MODE=true`
- Uses simulated Oracle schemas
- Perfect for demos and testing
- No Oracle installation required

**Real Oracle Mode:**
- Set `ENABLE_MOCK_MODE=false`
- Configure Oracle connection details
- Requires Oracle 19c/23c access
- Actual migration execution

---

## Connecting Real Oracle Databases

### Oracle Database Setup

**Option 1: Oracle Docker Container**

```bash
# Oracle 19c Free
docker run -d \
  --name oracle19c \
  -p 1521:1521 \
  -e ORACLE_PWD=YourPassword123 \
  container-registry.oracle.com/database/free:latest

# Wait for database to be ready (5-10 minutes)
docker logs -f oracle19c
```

**Option 2: Oracle Cloud**
- Use Oracle Autonomous Database
- Configure network access
- Update `.env` with connection details

**Option 3: On-Premises Oracle**
- Ensure network connectivity
- Configure firewall rules
- Update `.env` with connection details

### Testing Database Connections

```bash
# Backend must be running
curl -X POST http://localhost:8000/api/discovery/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "db_id": "test",
    "db_type": "oracle_19c_standalone",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "username": "system",
    "password": "YourPassword123"
  }'
```

---

## Troubleshooting

### Common Issues

**1. Azure OpenAI Connection Failed**

**Symptoms:** Backend logs show OpenAI errors

**Solutions:**
- Verify API key in `.env`
- Check endpoint URL format
- Ensure deployment name is correct
- Verify API version compatibility
- Check Azure quota limits

**2. Docker Container Won't Start**

**Symptoms:** `docker-compose up` fails

**Solutions:**
```bash
# Check Docker is running
docker ps

# View detailed logs
docker-compose logs backend
docker-compose logs frontend

# Remove and rebuild
docker-compose down -v
docker-compose up -d --build
```

**3. Frontend Can't Connect to Backend**

**Symptoms:** API calls fail in browser

**Solutions:**
- Check backend is running: http://localhost:8000/health
- Verify CORS settings in `main.py`
- Check browser console for errors
- Ensure `proxy` in `package.json` is correct

**4. Oracle Connection Failed**

**Symptoms:** "Failed to connect to database"

**Solutions:**
- Verify Oracle is running
- Check hostname, port, service name
- Test with SQL*Plus or SQL Developer first
- Verify firewall rules
- Check TNS listener status

**5. Port Already in Use**

**Symptoms:** "Port 8000/3000 already allocated"

**Solutions:**
```bash
# Find process using port
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend
```

View real-time logs:
```bash
docker-compose logs -f backend
```

---

## Performance Optimization

### For Large Migrations

**1. Increase Resource Limits**

In `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

**2. Enable Parallel Processing**

Future enhancement - configure worker threads

**3. Database Connection Pooling**

Adjust in `oracle_client.py` for production

---

## Security Hardening

### Production Security

**1. Environment Variables**
- Use Azure Key Vault / AWS Secrets Manager
- Never commit `.env` to git
- Rotate credentials regularly

**2. Network Security**
- Enable TLS/SSL
- Use VPN for database connections
- Configure firewall rules
- Implement IP whitelisting

**3. Application Security**
- Enable authentication (JWT, OAuth2)
- Implement rate limiting
- Add input validation
- Use HTTPS only

**4. Database Security**
- Use read-only accounts where possible
- Implement audit logging
- Encrypt connections (Oracle Native Encryption)
- Mask sensitive data in logs

---

## Monitoring

### Health Checks

**Backend:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
```bash
curl http://localhost:3000
```

### Docker Health Status

```bash
docker ps
# Look for "healthy" status
```

### Application Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## Backup and Recovery

### Backup State

```bash
# Export migration data (when using real databases)
docker exec -it oracle-migration-backend python -c "
import json
from api.migration import migrations
print(json.dumps(migrations, indent=2))
" > backup.json
```

### Restore State

Implement state persistence in production using:
- PostgreSQL for relational data
- MongoDB for document store
- Redis for caching

---

## Scaling for Production

### Horizontal Scaling

**Load Balancer Configuration:**
```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐     ┌─────────┐
    │Backend 1│      │Backend 2│     │Backend 3│
    └─────────┘      └─────────┘     └─────────┘
```

**Docker Swarm:**
```bash
docker swarm init
docker stack deploy -c docker-compose.yml migration
docker service scale migration_backend=3
```

**Kubernetes:**
See `k8s/` directory for manifests (to be added)

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose up -d --build
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (data loss!)
docker-compose down -v

# Clean up Docker system
docker system prune -a
```

---

## Support

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review `ARCHITECTURE.md` for design details
3. Check API docs: http://localhost:8000/docs
4. Review this deployment guide

### Reporting Issues

Include:
- Operating system
- Docker version
- Error messages from logs
- Steps to reproduce
- Screenshots if UI-related

---

## Next Steps

After successful deployment:

1. **Explore the UI** - Navigate through database selection and migration dashboard
2. **Review Agent Logs** - See how AI makes decisions
3. **Test Approval Workflow** - Experience human-in-the-loop
4. **Connect Real Oracle** - Switch from mock mode to actual databases
5. **Customize** - Adapt to your specific migration needs

Enjoy your AI-powered Oracle migration! 🚀
