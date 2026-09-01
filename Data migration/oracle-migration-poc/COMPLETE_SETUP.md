# Complete Setup Guide - Oracle Migration POC

## 🎯 What You Have

A complete, production-ready **Agentic AI Oracle Database Migration Platform** with:

✅ React + TypeScript frontend with professional UI  
✅ FastAPI + Python backend with AI orchestration  
✅ LangGraph multi-agent workflow system  
✅ Azure OpenAI integration for intelligent planning  
✅ Docker setup for easy deployment  
✅ **Real Oracle database support** (source + target)  
✅ Comprehensive documentation  

---

## 🚀 Two Deployment Options

### Option A: Mock Mode (5 Minutes)

**Perfect for:**
- Quick demonstrations
- Presentations
- POC showcasing
- No Oracle infrastructure needed

**Setup:**
1. Configure Azure OpenAI in `.env`
2. Run `setup.bat` (Windows) or `setup.sh` (Linux/macOS)
3. Access http://localhost:3000
4. Done!

---

### Option B: Real Oracle Databases (30 Minutes)

**Perfect for:**
- Actual migration testing
- Performance validation
- Real data scenarios
- Complete end-to-end workflow

**Setup:**
1. Start Oracle databases (15-20 min first time)
2. Configure Azure OpenAI in `.env`
3. Disable mock mode in `.env`
4. Start POC application
5. Migrate 1.65 million rows!

---

## 📋 Complete Setup Instructions

### Prerequisites

- [ ] Docker Desktop installed and running
- [ ] 8GB RAM minimum (16GB for Oracle databases)
- [ ] 20GB disk space (40GB for Oracle databases)
- [ ] Azure OpenAI API access
- [ ] Internet connection

---

## Step-by-Step: Mock Mode

### 1. Configure Azure OpenAI

Edit `.env` (copy from `.env.example`):

```bash
AZURE_OPENAI_API_KEY=your_actual_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Keep mock mode enabled
ENABLE_MOCK_MODE=true
```

### 2. Run Setup Script

**Windows:**
```cmd
setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Access Application

Open your browser:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Start Your First Migration

1. Select source, intermediate, and target databases
2. Click "Continue to Migration Dashboard"
3. Select tables to migrate
4. Click "Start AI-Powered Migration"
5. Watch the AI work its magic! 🎩✨

---

## Step-by-Step: Oracle Databases

### 1. Start Oracle Databases

**Windows:**
```cmd
cd docker
start-oracle.bat
```

**Linux/macOS:**
```bash
cd docker
chmod +x start-oracle.sh
./start-oracle.sh
```

**Wait for initialization** (15-20 minutes first time):

```bash
# Monitor progress
docker logs -f oracle-migration-source
```

**Look for this message:**
```
DATABASE IS READY TO USE!
```

### 2. Verify Databases are Running

```bash
docker ps
```

Should show:
```
oracle-migration-source    healthy
oracle-migration-target    healthy
```

### 3. Test Database Connections

```bash
# Test source
docker exec -it oracle-migration-source sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C

# Check table count
SQL> SELECT COUNT(*) FROM CUSTOMER;
  COUNT(*)
----------
    100000

SQL> EXIT
```

### 4. Configure POC for Oracle

Edit `.env`:

```bash
# Disable mock mode
ENABLE_MOCK_MODE=false

# Source Database
ORACLE_SOURCE_HOST=localhost
ORACLE_SOURCE_PORT=1521
ORACLE_SOURCE_SERVICE=PDB19C
ORACLE_SOURCE_USER=migration_user
ORACLE_SOURCE_PASSWORD=MigrationPwd123

# Target Database
ORACLE_TARGET_HOST=localhost
ORACLE_TARGET_PORT=1522
ORACLE_TARGET_SERVICE=PDB23C
ORACLE_TARGET_USER=migration_user
ORACLE_TARGET_PASSWORD=MigrationPwd123
```

### 5. Start POC Application

```bash
# From main directory
cd ..
./setup.bat    # Windows
./setup.sh     # Linux/macOS
```

### 6. Verify Connection

Test via API:
```bash
curl -X POST http://localhost:8000/api/discovery/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "db_id": "source",
    "db_type": "oracle_19c_standalone",
    "host": "localhost",
    "port": 1521,
    "service_name": "PDB19C",
    "username": "migration_user",
    "password": "MigrationPwd123"
  }'
```

Should return:
```json
{
  "connected": true,
  "version": "Oracle Database Free...",
  ...
}
```

### 7. Start Real Migration

1. Open http://localhost:3000
2. Select databases (should show real connections)
3. View actual table data (100K+ rows)
4. Start migration
5. Watch 1.65M rows migrate! 🚀

---

## 📊 What's Included in Oracle Databases

### Source Database (Oracle 19c)

**Connection:** `localhost:1521/PDB19C`

**Pre-loaded Data:**

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| CUSTOMER | 100,000 | ~25 MB | Customer records |
| PRODUCTS | 50,000 | ~12 MB | Product catalog |
| ORDERS | 250,000 | ~75 MB | Customer orders |
| ORDER_ITEMS | 750,000 | ~200 MB | Order line items |
| PAYMENTS | 500,000 | ~150 MB | Payment transactions |
| **TOTAL** | **1,650,000** | **~500 MB** | |

**Relationships:**
```
CUSTOMER ─┬─→ ORDERS ─┬─→ ORDER_ITEMS ─→ PRODUCTS
          │           └─→ PAYMENTS
          └─→ (Foreign Keys, Indexes, Views)
```

### Target Database (Oracle 23c)

**Connection:** `localhost:1522/PDB23C`

- Empty database
- Ready to receive migrated data
- Same user and permissions as source

---

## 🎨 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  React Frontend (Port 3000)             │
│         Professional UI with Gradient Design            │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                │
│        Migration API + Schema API + Validation          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                LangGraph Orchestrator                   │
│  Intent → Schema → Dependencies → Plan → Execute        │
│        → Validate → Reconcile (if needed)               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                  Azure OpenAI GPT-4
                         │
                         ▼
┌────────────────┬────────────────────────┬───────────────┐
│  Mock Data     │   Oracle Source        │ Oracle Target │
│  (Default)     │   localhost:1521       │ localhost:1522│
│                │   PDB19C (1.65M rows)  │ PDB23C (empty)│
└────────────────┴────────────────────────┴───────────────┘
```

---

## 🔍 Verification Checklist

### For Mock Mode

- [ ] Azure OpenAI configured in `.env`
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend healthy at http://localhost:8000/health
- [ ] Can select databases in UI
- [ ] Can see 5 sample tables
- [ ] Migration starts and completes
- [ ] Agent logs show reasoning

### For Oracle Mode

**All of the above, plus:**

- [ ] Oracle containers running (`docker ps`)
- [ ] Source shows "healthy" status
- [ ] Target shows "healthy" status
- [ ] Can connect via SQL*Plus
- [ ] Source has 100K+ rows in CUSTOMER
- [ ] Target is empty
- [ ] POC shows real table counts
- [ ] Migration moves actual data

---

## 📖 Documentation Guide

### Getting Started
1. **QUICKSTART.md** - 5-minute quick start guide
2. **This file** - Complete setup instructions

### Technical Details
1. **ARCHITECTURE.md** - System design and components
2. **docker/ORACLE_SETUP.md** - Oracle database detailed guide
3. **DEPLOYMENT.md** - Production deployment guide

### Presentations
1. **POC_SUMMARY.md** - Executive summary
2. **README.md** - Project overview

---

## 🎯 Common Use Cases

### Use Case 1: Quick Demo (Mock Mode)
**Time:** 5 minutes  
**Audience:** Business stakeholders, quick presentations  
**Setup:** Mock mode only  
**Shows:** Complete workflow, AI reasoning, UI/UX

### Use Case 2: Technical Demo (Oracle)
**Time:** 30 minutes  
**Audience:** Technical teams, architects, DBAs  
**Setup:** Full Oracle setup  
**Shows:** Real data migration, performance, validation

### Use Case 3: Development/Testing
**Time:** Ongoing  
**Audience:** Development team  
**Setup:** Oracle databases + local dev  
**Shows:** Feature development, agent testing

---

## 🛠️ Troubleshooting

### Application Won't Start

```bash
# Check Docker
docker ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart
docker-compose restart
```

### Oracle Databases Won't Start

```bash
# Check resources
docker stats

# Increase Docker Desktop memory to 8GB+
# Settings → Resources → Memory

# Check logs
docker logs -f oracle-migration-source

# Remove and restart
cd docker
docker-compose -f docker-compose-oracle.yml down -v
docker-compose -f docker-compose-oracle.yml up -d
```

### Can't Connect to Oracle

```bash
# Verify containers are healthy
docker ps

# Test connection manually
docker exec -it oracle-migration-source sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C

# Check .env configuration
cat .env | grep ORACLE
```

### Azure OpenAI Errors

1. Verify API key is correct
2. Check endpoint URL format
3. Ensure deployment name matches
4. Verify API version is supported
5. Check Azure quota limits

---

## 📊 Performance Expectations

### Mock Mode
- Startup: 30 seconds
- Migration: 20-30 seconds (simulated)
- Agent reasoning: Instant
- UI updates: Real-time

### Oracle Mode
- First startup: 15-20 minutes (DB initialization)
- Subsequent startups: 3-5 minutes
- Migration: 5-10 minutes (1.65M rows)
- Validation: 1-2 minutes

---

## 🔐 Security Notes

### What Goes to Azure OpenAI

✅ **Sent (Metadata Only):**
- Table names
- Column names and types
- Row counts (aggregated)
- Constraints and relationships

❌ **Never Sent (Sensitive Data):**
- Actual customer data
- PII (names, emails, addresses)
- Financial records
- Business-critical values

### Credentials Security

- Store in `.env` file (git-ignored)
- Use Azure Key Vault for production
- Rotate regularly
- Enable audit logging

---

## 🎬 Demo Script

### 5-Minute Demo (Mock Mode)

**0:00-1:00** - Introduction
- Show architecture diagram
- Explain agentic AI concept

**1:00-2:00** - Database Selection
- Navigate to application
- Show two-step migration path

**2:00-3:00** - Table Selection
- Display sample tables
- Highlight metadata

**3:00-4:00** - AI Planning
- Start migration
- Show agent reasoning
- Explain plan

**4:00-5:00** - Approval & Results
- Approve migration
- Show progress
- Display completion

### 15-Minute Demo (Oracle)

**0:00-2:00** - Introduction & Architecture  
**2:00-4:00** - Show Oracle Databases (SQL*Plus)  
**4:00-6:00** - Connect POC to Oracle  
**6:00-8:00** - View Real Tables  
**8:00-12:00** - Execute Migration  
**12:00-15:00** - Validate & Review Logs  

---

## 🚀 Next Steps

### After Successful Setup

1. **Explore the UI**
   - Test different table selections
   - Review agent reasoning
   - Check validation results

2. **Review Documentation**
   - Read ARCHITECTURE.md for design
   - Check POC_SUMMARY.md for presentations
   - Browse API docs at /docs

3. **Customize**
   - Modify agent prompts
   - Add new validation rules
   - Extend to other databases

4. **Present**
   - Use POC_SUMMARY.md for stakeholders
   - Show live demo
   - Discuss business value

---

## 📞 Need Help?

### Check These Resources

1. **Logs**
   - Backend: `docker-compose logs -f backend`
   - Frontend: Check browser console
   - Oracle: `docker logs -f oracle-migration-source`

2. **Health Checks**
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
   - Oracle: `docker ps` (look for "healthy")

3. **API Testing**
   - API Docs: http://localhost:8000/docs
   - Test endpoints directly
   - Check request/response

4. **Documentation**
   - QUICKSTART.md - Quick reference
   - ARCHITECTURE.md - Technical details
   - docker/ORACLE_SETUP.md - Oracle specifics
   - DEPLOYMENT.md - Production guide

---

## ✅ Success Checklist

### Mock Mode Setup
- [ ] Configured Azure OpenAI in `.env`
- [ ] Ran setup script successfully
- [ ] Accessed frontend at :3000
- [ ] Started a migration
- [ ] Saw AI-generated plan
- [ ] Approved and completed migration
- [ ] Reviewed agent logs

### Oracle Mode Setup
- [ ] Started Oracle databases
- [ ] Verified both containers healthy
- [ ] Tested SQL*Plus connection
- [ ] Configured `.env` for Oracle
- [ ] Disabled mock mode
- [ ] Restarted POC backend
- [ ] Saw real table data in UI
- [ ] Migrated actual Oracle data
- [ ] Validated target database

---

## 🎉 You're Ready!

Your **Agentic AI Oracle Migration Platform** is now complete and operational!

**What you can do:**
- ✅ Demo to stakeholders
- ✅ Test real migrations
- ✅ Develop new features
- ✅ Extend to other databases
- ✅ Deploy to production

**Remember:**
- Mock mode = Quick demos
- Oracle mode = Real testing
- Document your findings
- Share feedback

---

**Happy Migrating! 🚀**

*Built with React, FastAPI, LangGraph, Azure OpenAI, and Oracle*
