# Agentic AI-Powered Oracle Database Migration Platform

## Overview

This POC demonstrates an **Agentic AI-based framework** that automates the assessment, planning, and execution of Oracle database migrations using Azure OpenAI and LangGraph orchestration.

### Two-Step Migration Workflow

1. **Step 1**: Oracle 19c standalone (non-CDB) → Oracle 19c CDB/PDB conversion
2. **Step 2**: Oracle 19c CDB/PDB → Oracle 23c CDB/PDB migration

## Architecture

```
┌─────────────────────────────┐
│      React Frontend         │
│ • Migration Dashboard       │
│ • Source/Target Selection   │
│ • Agent Reasoning Display   │
│ • Validation Results        │
└──────────────┬──────────────┘
               │ REST / SSE
               ▼
┌─────────────────────────────┐
│        FastAPI Gateway      │
│ /migration/start            │
│ /migration/status           │
│ /schema                     │
│ /validation                 │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│    LangGraph Orchestrator   │
│                             │
│  Schema → Planner →         │
│  Executor → Validator       │
└──────────────┬──────────────┘
               │
               ▼
        Azure OpenAI API
               │
               ▼
┌──────────────────────────┐
│   Oracle Source/Target   │
└──────────────────────────┘
```

## Features

### Agentic AI Capabilities

- **Intent Analysis**: Natural language understanding of migration requirements
- **Schema Discovery**: Automated analysis of tables, relationships, constraints
- **Migration Planning**: Intelligent dependency ordering and risk assessment
- **Validation & Reconciliation**: Automated verification with self-healing
- **Human-in-the-Loop**: Approval gates at critical decision points

### Security & Compliance

- Metadata-only LLM communication (no sensitive data sent to AI)
- TLS encryption
- Audit logging
- Data masking
- RBAC support

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Agent Orchestration | LangGraph |
| LLM Integration | LangChain + Azure OpenAI |
| Database | Oracle (19c, 23c) |
| Containerization | Docker |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Azure OpenAI API key

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd oracle-migration-poc
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Configure your Azure OpenAI credentials in `.env`:
```
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Running with Docker

```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
oracle-migration-poc/
├── backend/
│   ├── agents/              # LangGraph agent nodes
│   │   ├── discovery.py     # Schema discovery agent
│   │   ├── planner.py       # Migration planning agent
│   │   ├── executor.py      # Migration execution agent
│   │   ├── validator.py     # Validation & reconciliation
│   │   └── orchestrator.py  # Main orchestration graph
│   ├── api/                 # FastAPI routes
│   ├── db/                  # Database utilities
│   ├── models/              # Pydantic models
│   ├── security/            # Security & audit
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API clients
│   │   └── App.tsx          # Main app
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Migration Operations
- `POST /api/migration/start` - Start migration workflow
- `GET /api/migration/{migration_id}/status` - Get migration status
- `POST /api/migration/{migration_id}/approve` - Approve migration step
- `POST /api/migration/{migration_id}/cancel` - Cancel migration

### Schema & Discovery
- `GET /api/schema/source/{db_id}` - Get source schema
- `GET /api/schema/target/{db_id}` - Get target schema
- `GET /api/schema/analyze` - Analyze dependencies

### Validation
- `GET /api/validation/{migration_id}` - Get validation results
- `POST /api/validation/{migration_id}/reconcile` - Trigger reconciliation

## Usage Guide

### 1. Connect Databases

Configure source and target database connections in the UI:
- Oracle 19c standalone (source)
- Oracle 19c CDB/PDB (intermediate)
- Oracle 23c CDB/PDB (target)

### 2. Initiate Migration

Select tables and objects to migrate. The AI agent will:
- Analyze schema and dependencies
- Generate migration plan
- Present for human approval

### 3. Review & Approve

Review the AI-generated migration plan:
- Migration waves
- Dependency order
- Risk assessment
- Estimated downtime

### 4. Execute Migration

Step 1: Convert to 19c PDB
- Pre-migration validation
- Conversion execution
- Post-conversion validation

Step 2: Migrate to 23c
- Pre-migration checks
- Data migration
- Final validation

### 5. Monitor & Validate

Real-time monitoring:
- Migration progress
- Agent reasoning
- Validation results
- Error handling

## Agent Workflow

```
User Request
     ↓
Intent Analyzer (Azure OpenAI)
     ↓
Schema Discovery (Python + Oracle)
     ↓
Dependency Analysis (Azure OpenAI)
     ↓
Migration Planner (Azure OpenAI)
     ↓
Human Approval Gate
     ↓
Migration Executor (Python)
     ↓
Validator (Python + Oracle)
     ↓
Mismatch? → Yes → Repair Agent → Retry
     ↓ No
Complete
```

## Security Considerations

### Data Privacy
- **Metadata Only**: Only table structures, column names, and counts sent to Azure OpenAI
- **No Sensitive Data**: Actual data records never leave your environment
- **Data Masking**: PII fields masked in logs and reports

### Network Security
- TLS/SSL for all connections
- Firewall rules configured
- VPC/VNet isolation recommended

### Access Control
- JWT-based authentication
- Role-based permissions
- Audit trail for all operations

## Mock Data for Testing

### Option 1: Mock Mode (Default)
The POC includes simulated Oracle schemas:
- CUSTOMER table (100K rows)
- ORDERS table (250K rows)
- PAYMENTS table (500K rows)
- Foreign key relationships
- Indexes and constraints

### Option 2: Real Oracle Databases

For testing with actual Oracle databases, we provide Docker setup:

```bash
cd docker
./start-oracle.bat    # Windows
./start-oracle.sh     # Linux/macOS
```

This starts:
- **Source**: Oracle Free (as 19c) with 1.65M rows of sample data
- **Target**: Oracle Free (as 23c) empty and ready

See `docker/ORACLE_SETUP.md` for detailed instructions.

## Troubleshooting

### Common Issues

**Azure OpenAI Connection Failed**
- Verify API key and endpoint in `.env`
- Check network connectivity
- Ensure deployment name matches

**Oracle Connection Failed**
- Verify Oracle container is running: `docker ps`
- Check connection string format
- Ensure listener is configured

**Migration Validation Failed**
- Review agent logs in UI
- Check validation report
- Use repair agent for reconciliation

## Success Criteria

This POC demonstrates:
- ✅ Automated source database discovery
- ✅ Schema and dependency analysis
- ✅ Intelligent migration planning
- ✅ Two-step migration orchestration
- ✅ Automated validation and reconciliation
- ✅ Human-in-the-loop approvals
- ✅ Executive reporting

## Future Enhancements

- Additional database platforms (PostgreSQL, SQL Server)
- Advanced performance optimization
- HA/DR migration strategies
- Multi-region deployment
- CMDB integration
- Real-time replication

## License

This is a POC/MVP demonstration project.

## Support

For issues or questions, contact the development team.
