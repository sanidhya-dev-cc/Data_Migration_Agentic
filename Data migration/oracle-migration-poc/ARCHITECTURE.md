# Oracle Migration POC - Architecture Documentation

## System Architecture

### Overview

This is an **Agentic AI-powered Oracle Database Migration Platform** that demonstrates intelligent, automated database migration with human-in-the-loop decision making.

### What Makes This "Agentic AI"?

This is **not** simple automation. The system exhibits true agentic behavior:

1. **Autonomous Decision Making**: The AI analyzes schemas, dependencies, and risks to generate migration plans
2. **Reasoning & Planning**: Uses Azure OpenAI to understand relationships and create optimal execution strategies
3. **Self-Correction**: Validation agents can detect issues and trigger reconciliation workflows
4. **Human Collaboration**: Presents plans for approval with detailed reasoning
5. **Context Awareness**: Maintains state across multi-step workflows using LangGraph

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Database    │  │  Migration   │  │   Agent Logs &     │   │
│  │   Selector    │  │  Dashboard   │  │   Reasoning View   │   │
│  └───────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API + SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Discovery   │  │   Schema     │  │    Validation        │   │
│  │    API      │  │     API      │  │       API            │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Migration API                               │   │
│  │  • Start Migration  • Get Status  • Approve  • Cancel   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Orchestrator                        │
│                                                                  │
│  ┌────────────────┐     ┌────────────────────┐                 │
│  │ Intent Analyzer│ ──> │ Schema Discovery   │                 │
│  │  (Azure OpenAI)│     │   (Python + SQL)   │                 │
│  └────────────────┘     └────────┬───────────┘                 │
│                                  │                              │
│                                  ▼                              │
│                    ┌──────────────────────────┐                 │
│                    │  Dependency Analyzer     │                 │
│                    │    (Azure OpenAI)        │                 │
│                    └──────────┬───────────────┘                 │
│                               │                                 │
│                               ▼                                 │
│                  ┌────────────────────────────┐                 │
│                  │   Migration Planner        │                 │
│                  │    (Azure OpenAI)          │                 │
│                  └──────────┬─────────────────┘                 │
│                             │                                   │
│                             ▼                                   │
│                  ┌──────────────────────┐                       │
│                  │  Human Approval Gate │                       │
│                  └──────────┬───────────┘                       │
│                             │                                   │
│                             ▼                                   │
│                  ┌──────────────────────┐                       │
│                  │  Migration Executor  │                       │
│                  │    (Python Engine)   │                       │
│                  └──────────┬───────────┘                       │
│                             │                                   │
│                             ▼                                   │
│                  ┌──────────────────────┐                       │
│                  │     Validator        │                       │
│                  │  (Python + SQL)      │                       │
│                  └──────────┬───────────┘                       │
│                             │                                   │
│                    ┌────────┴────────┐                          │
│                    │                 │                          │
│                  PASS              FAIL                         │
│                    │                 │                          │
│                    ▼                 ▼                          │
│                Complete      Reconciliation Agent              │
│                                      │                          │
│                                      └──> Retry                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Azure OpenAI    │
                    │   GPT-4 / GPT-4o │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Oracle Databases                           │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Source     │ ──> │ Intermediate │ ──> │   Target     │    │
│  │              │     │              │     │              │    │
│  │  19c Non-CDB │     │  19c CDB/PDB │     │  23c CDB/PDB │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend (React + TypeScript)

**Purpose**: Professional UI for migration control and monitoring

**Key Components**:
- `DatabaseSelector`: Configure source, intermediate, and target databases
- `MigrationDashboard`: Central control panel for migration operations
- `TableSelector`: Select tables for migration with metadata display
- `MigrationProgress`: Real-time progress tracking with visual feedback
- `MigrationPlanView`: Display AI-generated plan with approval workflow
- `AgentLogs`: Show AI reasoning and decision-making process

**Design Principles**:
- Clean, modern gradient design
- Real-time updates via polling
- Responsive for all screen sizes
- Clear status indicators and progress bars

### Backend (FastAPI + Python)

**Purpose**: API gateway and business logic orchestration

**API Routes**:

1. **Discovery API** (`/api/discovery`)
   - `POST /test-connection`: Verify database connectivity
   - `GET /databases`: List configured databases

2. **Schema API** (`/api/schema`)
   - `POST /analyze`: Analyze database schema
   - `GET /source/{db_id}`: Get source schema
   - `GET /target/{db_id}`: Get target schema
   - `POST /compare`: Compare source and target

3. **Migration API** (`/api/migration`)
   - `POST /start`: Initiate migration
   - `GET /{migration_id}/status`: Get current status
   - `POST /{migration_id}/approve`: Approve/reject plan
   - `POST /{migration_id}/cancel`: Cancel migration

4. **Validation API** (`/api/validation`)
   - `GET /{migration_id}`: Get validation results
   - `POST /{migration_id}/reconcile`: Trigger reconciliation

### LangGraph Orchestrator

**Purpose**: Stateful, multi-step agent workflow management

**Agent Nodes**:

1. **Intent Analyzer**
   - Uses: Azure OpenAI
   - Function: Understand migration requirements
   - Output: Structured intent object

2. **Schema Discovery**
   - Uses: Python + Oracle SQL
   - Function: Extract metadata (NOT sensitive data)
   - Output: Tables, columns, relationships

3. **Dependency Analyzer**
   - Uses: Azure OpenAI + Oracle SQL
   - Function: Map foreign keys, views, triggers
   - Output: Dependency graph with risk levels

4. **Migration Planner**
   - Uses: Azure OpenAI
   - Function: Generate optimal two-step migration plan
   - Output: Execution order, pre-checks, rollback strategy

5. **Human Approval Gate**
   - Uses: External API call
   - Function: Wait for human decision
   - Output: Approved/rejected status

6. **Migration Executor**
   - Uses: **Controlled Python** (NOT LLM-generated SQL)
   - Function: Execute migration safely
   - Output: Migration results

7. **Validator**
   - Uses: Python + Oracle SQL
   - Function: Verify row counts, schemas, constraints
   - Output: Validation report

8. **Reconciliation Agent**
   - Uses: Azure OpenAI + Python
   - Function: Analyze and repair validation failures
   - Output: Repair plan and retry decision

### Database Layer (Oracle)

**Oracle Client** (`oracle_client.py`):
- Connection management
- Metadata extraction
- Schema validation
- Row count verification
- **Security**: Only metadata sent to AI, never actual data

**Mock Mode**:
- For POC demonstrations without real Oracle databases
- Generates realistic schemas with dependencies
- Simulates migration workflows

## Security Architecture

### Data Privacy

```
┌─────────────────────────────────────────────────────────┐
│              WHAT GOES TO AZURE OPENAI?                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ ALLOWED (Metadata Only):                           │
│     • Table names                                       │
│     • Column names and data types                       │
│     • Row counts (aggregated)                          │
│     • Constraint definitions                            │
│     • Index structures                                  │
│     • Dependency relationships                          │
│                                                         │
│  ❌ FORBIDDEN (Sensitive Data):                        │
│     • Actual table data                                │
│     • Customer records                                  │
│     • PII (names, addresses, SSN, etc.)                │
│     • Financial data                                    │
│     • Authentication credentials                        │
│     • Business-critical values                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Security Controls

1. **TLS/SSL**: All connections encrypted
2. **Environment Variables**: Secrets in `.env`
3. **RBAC**: Role-based access control ready
4. **Audit Logs**: All operations logged
5. **Data Masking**: PII masked in logs
6. **Least Privilege**: Minimal database permissions

## Two-Step Migration Process

### Step 1: Oracle 19c Non-CDB → 19c CDB/PDB

**Method**: Oracle DBMS_PDB package
**Duration**: ~30 minutes (for POC dataset)
**Risk**: Medium (well-tested conversion path)

**Process**:
1. Create PDB from non-CDB
2. Validate plug compatibility
3. Test connectivity
4. Verify objects

### Step 2: Oracle 19c PDB → 23c CDB/PDB

**Method**: Unplug/plug methodology
**Duration**: ~45 minutes (for POC dataset)
**Risk**: Low (forward compatible)

**Process**:
1. Unplug 19c PDB
2. Plug into 23c CDB
3. Upgrade if needed
4. Validate and open

## Key Design Decisions

### Why LangGraph?

- **Stateful workflows**: Maintains context across steps
- **Conditional routing**: Different paths based on validation
- **Human-in-the-loop**: Built-in approval gates
- **Persistence**: Can resume after failures
- **Streaming**: Real-time progress updates

### Why NOT LLM-Generated SQL?

**Security Risk**: LLMs can generate destructive queries

**Our Approach**:
- LLM decides **WHAT** to do (planning)
- Python decides **HOW** to do it safely (execution)
- Pre-defined, tested migration patterns
- Controlled execution with transaction management

### Mock Mode for POC

Enables demonstration without Oracle infrastructure:
- Realistic table structures
- Dependency relationships
- Simulated execution timing
- Validation scenarios

## Scalability Considerations

### Current POC Limitations

- In-memory state storage
- Single-threaded execution
- Polling for updates

### Production Enhancements

- PostgreSQL/MongoDB for state
- Celery for async task execution
- WebSocket for real-time updates
- Horizontal scaling with load balancers
- Redis for caching

## Monitoring & Observability

### Agent Logs

Real-time visibility into AI decision-making:
- Agent name and timestamp
- Action performed
- Reasoning behind decisions
- Metadata for debugging

### Migration Progress

- Current status and step
- Tables completed vs total
- Progress percentage
- Start/completion times
- Error messages

### Validation Reports

- Row count comparison
- Schema matching
- Constraint verification
- Index validation
- Issue identification

## Technology Choices

| Layer | Technology | Why? |
|-------|-----------|------|
| Frontend | React + TypeScript | Modern, type-safe, component-based |
| Backend | FastAPI | High performance, async, auto docs |
| AI Orchestration | LangGraph | Stateful agent workflows |
| LLM | Azure OpenAI | Enterprise-grade, GPT-4 access |
| Database | Oracle | Target platform for POC |
| Containerization | Docker | Consistent environments |
| Styling | CSS3 + Gradients | Modern, attractive UI |

## Future Enhancements

1. **Additional Platforms**: PostgreSQL, SQL Server, MySQL
2. **Advanced Optimization**: Parallel DML, compression
3. **HA/DR**: Multi-region, failover strategies
4. **CMDB Integration**: Automatic inventory updates
5. **Cost Estimation**: Pre-migration cost analysis
6. **Rollback Automation**: One-click rollback capability
7. **Compliance Reporting**: Audit trails, compliance checks
8. **Multi-tenancy**: Support for multiple simultaneous migrations

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Oracle Multitenant Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
