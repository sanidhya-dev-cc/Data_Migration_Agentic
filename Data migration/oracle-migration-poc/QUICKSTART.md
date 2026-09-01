# Quick Start Guide - Oracle Migration POC

## Get Started in 5 Minutes! 🚀

This guide will get you up and running with the Agentic AI Oracle Migration Platform in minutes.

---

## Step 1: Prerequisites ✅

Make sure you have:

- [ ] **Docker Desktop** installed and running
  - Windows/Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Linux: Install Docker Engine + Docker Compose
  
- [ ] **Azure OpenAI API Access**
  - API Key
  - Endpoint URL
  - Deployment name (GPT-4 recommended)

- [ ] **4GB RAM** available on your machine

---

## Step 2: Configure Azure OpenAI 🔑

1. Open the `.env.example` file

2. Copy it to `.env`:
   ```bash
   # Windows (Command Prompt)
   copy .env.example .env
   
   # Linux/macOS (Terminal)
   cp .env.example .env
   ```

3. Edit `.env` and add your Azure OpenAI credentials:
   ```bash
   AZURE_OPENAI_API_KEY=your_actual_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

4. Save the file

**⚠️ Important:** Keep `ENABLE_MOCK_MODE=true` for the demo (no real Oracle needed)

---

## Step 3: Launch the Application 🚀

### Windows Users:

1. Double-click `setup.bat`
2. Wait for containers to build (first time: 5-10 minutes)
3. Look for "Setup Complete!" message

### Linux/macOS Users:

1. Open Terminal
2. Navigate to project folder:
   ```bash
   cd oracle-migration-poc
   ```
3. Make script executable and run:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
4. Wait for "Setup Complete!" message

---

## Step 4: Access the Application 🌐

Open your browser and visit:

- **🎨 Migration Dashboard**: http://localhost:3000
- **📡 API Backend**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs

---

## Step 5: Try Your First Migration 🎯

### 5.1 Select Databases

1. On the landing page, you'll see three database selections
2. They should be pre-selected:
   - **Source**: Oracle 19c Standalone
   - **Intermediate**: Oracle 19c CDB/PDB
   - **Target**: Oracle 23c CDB/PDB
3. Click **"Continue to Migration Dashboard"**

### 5.2 Select Tables

1. You'll see 5 sample tables with metadata:
   - CUSTOMER (100K rows, 25.5 MB)
   - ORDERS (250K rows, 75.2 MB)
   - PAYMENTS (500K rows, 150.8 MB)
   - PRODUCTS (50K rows, 12.3 MB)
   - ORDER_ITEMS (750K rows, 200.5 MB)

2. All tables are selected by default
3. You can deselect any table by clicking on it

### 5.3 Start Migration

1. Click **"Start AI-Powered Migration"**
2. Watch the AI agent work:
   - ✅ Analyzing schema
   - ✅ Discovering dependencies
   - ✅ Creating migration plan

### 5.4 Review AI-Generated Plan

After ~15 seconds, you'll see:

1. **AI Reasoning**: Detailed explanation of the migration strategy
2. **Step 1 & 2 Details**: Execution order, duration, risk levels
3. **Pre-checks**: What will be validated before migration
4. **Post-checks**: What will be validated after migration
5. **Rollback Strategy**: How to recover if something fails

### 5.5 Approve and Execute

1. Review the plan carefully
2. (Optional) Add comments
3. Click **"✓ Approve and Execute Migration"**
4. Watch real-time progress:
   - Progress bar updates
   - Agent reasoning displayed
   - Status changes (Executing → Validating → Completed)

### 5.6 View Results

Once complete:
- ✅ All tables migrated
- ✅ Validation passed
- ✅ Success message displayed
- 📊 Agent logs showing decision-making process

---

## What You Just Experienced 🎓

### True Agentic AI Capabilities:

1. **Intent Analysis**: AI understood your migration goals
2. **Schema Discovery**: Automatically analyzed table structures
3. **Dependency Analysis**: Identified foreign keys and relationships
4. **Migration Planning**: Generated optimal two-step strategy
5. **Human-in-the-Loop**: Presented plan for your approval
6. **Execution**: Safely migrated databases
7. **Validation**: Verified data integrity
8. **Self-Healing**: Can detect and repair issues automatically

### Why This is Agentic (Not Just Automation):

| Traditional Automation | This Agentic AI System |
|----------------------|----------------------|
| Follows fixed scripts | Makes intelligent decisions |
| No reasoning | Explains its choices |
| Fails on unexpected issues | Adapts and finds solutions |
| No human collaboration | Seeks approval at critical points |
| Black box | Transparent reasoning |

---

## Explore Further 🔍

### View Agent Reasoning

Scroll down to **"Agent Reasoning & Logs"** to see:
- What each agent did
- Why it made specific decisions
- Metadata about operations

### Try Different Scenarios

1. **Deselect tables**: See how the plan changes
2. **Review risk assessment**: Understand dependency impacts
3. **Add comments**: Practice approval workflow

---

## Understanding the UI 🎨

### Color Coding:

- **🟣 Purple/Gradient**: Primary actions and branding
- **🟢 Green**: Success, Step 1, completed states
- **🔵 Blue**: In-progress, Step 2, info
- **🟡 Yellow**: Warnings, awaiting approval
- **🔴 Red**: Errors, critical actions

### Real-Time Updates:

- Progress bar animates with shimmer effect
- Status badges update automatically
- Agent logs appear in real-time
- Polling every 3 seconds for status

---

## Common Questions ❓

### Q: Do I need real Oracle databases?

**A:** No! Mock mode simulates everything. Perfect for demos.

### Q: Can I connect real Oracle databases?

**A:** Yes! Set `ENABLE_MOCK_MODE=false` in `.env` and add connection details.

### Q: Is my data sent to Azure OpenAI?

**A:** No! Only metadata (table names, column types, row counts). Never actual data.

### Q: How long does a real migration take?

**A:** Depends on data size. POC dataset (~500 MB): 75 minutes total.

### Q: Can I cancel a migration?

**A:** Yes, before execution completes. Click "Cancel Migration" button.

### Q: What if validation fails?

**A:** The AI reconciliation agent analyzes issues and attempts repairs.

---

## Troubleshooting 🔧

### Containers Won't Start

```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs -f

# Restart
docker-compose restart
```

### Can't Connect to Backend

1. Check backend health: http://localhost:8000/health
2. Should show: `{"status": "healthy", ...}`

### Azure OpenAI Errors

1. Verify API key in `.env`
2. Check endpoint URL format
3. Ensure deployment exists
4. Check Azure quota limits

---

## Stopping the Application 🛑

```bash
# Stop all services
docker-compose down

# Stop and remove data volumes
docker-compose down -v
```

---

## Next Steps 📚

1. **Read Architecture**: See `ARCHITECTURE.md` for system design
2. **Deployment Guide**: See `DEPLOYMENT.md` for production setup
3. **Customize**: Modify agents in `backend/agents/`
4. **Extend**: Add new database platforms

---

## Demo Tips for Presentations 🎤

### Prepare Your Demo:

1. **Start services 10 min early**: Ensure everything is running
2. **Test the workflow once**: Make sure Azure OpenAI is working
3. **Open all tabs**: Dashboard, API Docs, Agent Logs
4. **Clear browser cache**: Fresh, fast loading

### During Demo:

1. **Show the architecture diagram** (in ARCHITECTURE.md)
2. **Emphasize AI reasoning**: Expand agent logs
3. **Highlight human-in-the-loop**: Explain approval workflow
4. **Show metadata-only approach**: Security advantage
5. **Demonstrate two-step process**: 19c → 19c PDB → 23c

### Talking Points:

- ✅ "This is true agentic AI, not simple automation"
- ✅ "The AI generates plans, not SQL" (security!)
- ✅ "Human oversight at every critical decision"
- ✅ "Transparent reasoning - you see what it's thinking"
- ✅ "Self-healing with validation and reconciliation"

---

## Getting Help 🆘

### Check These First:

1. Logs: `docker-compose logs -f backend`
2. Health check: http://localhost:8000/health
3. API docs: http://localhost:8000/docs

### Common Fixes:

- **Port in use**: Change ports in `docker-compose.yml`
- **Out of memory**: Increase Docker Desktop RAM limit
- **Slow performance**: Close unnecessary applications

---

## Success! 🎉

You now have a working Agentic AI Oracle Migration Platform!

**What makes this special:**
- Real AI decision-making with Azure OpenAI
- Professional, production-ready UI
- Two-step migration strategy
- Human-in-the-loop approvals
- Complete transparency and auditability

**Share your experience:**
- Screenshot the success screen
- Show the agent reasoning logs
- Demonstrate the migration flow

---

## Quick Reference 📝

| Action | Command |
|--------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Restart backend | `docker-compose restart backend` |
| Rebuild | `docker-compose up -d --build` |
| Check health | `curl http://localhost:8000/health` |

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend Dashboard |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API Documentation |
| http://localhost:8000/health | Health Check |

---

**Enjoy your AI-powered migration journey! 🚀**
