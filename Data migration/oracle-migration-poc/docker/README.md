# Oracle Docker Setup - Quick Reference

## Overview

This directory contains Docker configurations for running real Oracle databases for the migration POC.

---

## Two Setup Options

### Option 1: Mock Mode (Default - No Oracle Needed)

Perfect for demos and presentations without Oracle databases.

```bash
# In main directory
cd oracle-migration-poc
./setup.bat    # Windows
./setup.sh     # Linux/macOS
```

Access at: http://localhost:3000

### Option 2: Real Oracle Databases

For testing with actual Oracle databases and real data.

---

## Quick Start with Oracle

### Step 1: Start Oracle Databases

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

### Step 2: Wait for Initialization

**First time:** 15-20 minutes  
**Subsequent starts:** 3-5 minutes

**Monitor progress:**
```bash
docker logs -f oracle-migration-source
```

**Look for:**
```
DATABASE IS READY TO USE!
```

### Step 3: Verify Databases

```bash
docker ps
```

Should show both as `healthy`:
```
oracle-migration-source    healthy
oracle-migration-target    healthy
```

### Step 4: Connect POC to Oracle

Edit `../env`:
```bash
ENABLE_MOCK_MODE=false

ORACLE_SOURCE_HOST=localhost
ORACLE_SOURCE_PORT=1521
ORACLE_SOURCE_SERVICE=PDB19C
ORACLE_SOURCE_USER=migration_user
ORACLE_SOURCE_PASSWORD=MigrationPwd123

ORACLE_TARGET_HOST=localhost
ORACLE_TARGET_PORT=1522
ORACLE_TARGET_SERVICE=PDB23C
ORACLE_TARGET_USER=migration_user
ORACLE_TARGET_PASSWORD=MigrationPwd123
```

### Step 5: Restart POC Backend

```bash
cd ..
docker-compose restart backend
```

### Step 6: Test Migration

Open http://localhost:3000 and start migrating!

---

## What You Get

### Source Database (localhost:1521/PDB19C)

**Pre-loaded with 1.65 million rows:**

| Table | Rows | Size |
|-------|------|------|
| CUSTOMER | 100,000 | ~25 MB |
| PRODUCTS | 50,000 | ~12 MB |
| ORDERS | 250,000 | ~75 MB |
| ORDER_ITEMS | 750,000 | ~200 MB |
| PAYMENTS | 500,000 | ~150 MB |

**Total:** 1,650,000 rows (~500 MB)

### Target Database (localhost:1522/PDB23C)

Empty and ready to receive migrated data.

---

## Connection Details

### Source (Oracle 19c)
```
Host: localhost
Port: 1521
Service: PDB19C
User: migration_user
Password: MigrationPwd123
```

### Target (Oracle 23c)
```
Host: localhost
Port: 1522
Service: PDB23C
User: migration_user
Password: MigrationPwd123
```

---

## Common Commands

### Start Databases
```bash
docker-compose -f docker-compose-oracle.yml start
```

### Stop Databases
```bash
docker-compose -f docker-compose-oracle.yml stop
```

### View Logs
```bash
docker logs -f oracle-migration-source
docker logs -f oracle-migration-target
```

### Check Status
```bash
docker ps
```

### Connect with SQL*Plus
```bash
# Source
docker exec -it oracle-migration-source sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C

# Target
docker exec -it oracle-migration-target sqlplus migration_user/MigrationPwd123@localhost:1522/PDB23C
```

### Test Connection from POC
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

### Remove All Data (Fresh Start)
```bash
docker-compose -f docker-compose-oracle.yml down -v
```

---

## Files in This Directory

```
docker/
├── docker-compose-oracle.yml       # Oracle database configuration
├── start-oracle.bat                # Windows startup script
├── start-oracle.sh                 # Linux/macOS startup script
├── ORACLE_SETUP.md                 # Comprehensive setup guide
├── README.md                       # This file
└── init-scripts/                   # Database initialization
    ├── source/                     # Source DB scripts
    │   ├── 01_create_user.sql     # Create migration user
    │   ├── 02_create_schema.sql   # Create tables
    │   └── 03_populate_data.sql   # Insert sample data
    ├── target/                     # Target DB scripts
    │   └── 01_create_user.sql     # Create migration user
    └── startup/                    # Startup scripts
        └── run_init.sh            # Auto-run on container start
```

---

## System Requirements

### Minimum
- RAM: 8GB
- Disk: 20GB free
- Docker Desktop

### Recommended
- RAM: 16GB
- Disk: 40GB free
- SSD
- 4 CPU cores

---

## Troubleshooting

### Database Won't Start

**Increase Docker resources:**

Docker Desktop → Settings → Resources:
- Memory: 8GB+
- Disk: 60GB+

### Slow Performance

```bash
# Check resource usage
docker stats

# Increase shared memory in docker-compose-oracle.yml
shm_size: 2gb
```

### Connection Refused

```bash
# Check if databases are ready
docker ps

# Should show 'healthy' status
# Wait if status is 'starting' or 'unhealthy'
```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a --volumes
```

### Reset to Fresh State

```bash
# Warning: Deletes all data!
docker-compose -f docker-compose-oracle.yml down -v
docker-compose -f docker-compose-oracle.yml up -d
```

---

## Enterprise Manager

Access Oracle Enterprise Manager web console:

**Source:** https://localhost:5500/em  
**Target:** https://localhost:5501/em

**Login:**
- User: `sys`
- Password: `OraclePwd123`
- Connect as: `SYSDBA`

*(Self-signed certificate warning is expected)*

---

## Need Help?

1. **Read:** `ORACLE_SETUP.md` for detailed guide
2. **Check logs:** `docker logs -f oracle-migration-source`
3. **Verify health:** `docker ps`
4. **Test connection:** Use SQL*Plus or POC API

---

## Next Steps

1. ✅ Start Oracle databases
2. ✅ Wait for "DATABASE IS READY TO USE!"
3. ✅ Update `.env` to disable mock mode
4. ✅ Restart POC backend
5. ✅ Open http://localhost:3000
6. ✅ Start your first real Oracle migration!

---

**Enjoy migrating with real Oracle databases! 🚀**
