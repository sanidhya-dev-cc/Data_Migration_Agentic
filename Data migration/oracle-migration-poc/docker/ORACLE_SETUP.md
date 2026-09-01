# Oracle Database Setup Guide

## Overview

This guide explains how to set up real Oracle databases for the migration POC using Docker containers.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Oracle Database Setup                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Source Database              Target Database      │
│  ┌──────────────────┐        ┌──────────────────┐  │
│  │  Oracle Free     │        │  Oracle Free     │  │
│  │  (as 19c)        │   →    │  (as 23c)        │  │
│  │                  │        │                  │  │
│  │  Port: 1521      │        │  Port: 1522      │  │
│  │  SID: ORCL19C    │        │  SID: ORCL23C    │  │
│  │  PDB: PDB19C     │        │  PDB: PDB23C     │  │
│  │                  │        │                  │  │
│  │  📊 Sample Data  │        │  📭 Empty        │  │
│  │  1.65M rows      │        │  Ready for data  │  │
│  └──────────────────┘        └──────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Prerequisites

### System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 20GB free space
- **Docker Desktop**: Latest version
- **CPU**: 2+ cores recommended

### Important Notes

⚠️ **Oracle Free Edition Limitations**:
- 2 CPUs
- 2 GB RAM per instance
- 12 GB user data per instance

⚠️ **First-Time Download**:
- Oracle image is ~2GB
- Download may take 10-30 minutes depending on connection
- Be patient!

---

## Quick Start

### Step 1: Navigate to Docker Directory

```bash
cd oracle-migration-poc/docker
```

### Step 2: Start Oracle Databases

```bash
docker-compose -f docker-compose-oracle.yml up -d
```

### Step 3: Monitor Startup

**View logs:**
```bash
# Source database
docker logs -f oracle-migration-source

# Target database
docker logs -f oracle-migration-target
```

**Wait for this message:**
```
DATABASE IS READY TO USE!
```

**Typical startup time**: 5-10 minutes (first time: 15-20 minutes)

### Step 4: Verify Databases are Running

```bash
docker ps
```

You should see:
```
oracle-migration-source    healthy
oracle-migration-target    healthy
```

---

## Sample Data

### What's Included

The **source database** is automatically populated with:

| Table | Rows | Description |
|-------|------|-------------|
| CUSTOMER | 100,000 | Customer records |
| PRODUCTS | 50,000 | Product catalog |
| ORDERS | 250,000 | Customer orders |
| ORDER_ITEMS | 750,000 | Order line items |
| PAYMENTS | 500,000 | Payment transactions |
| **TOTAL** | **1,650,000** | **~500 MB** |

### Relationships

```
CUSTOMER ─┐
          ↓
        ORDERS ─┬─→ ORDER_ITEMS ─→ PRODUCTS
                └─→ PAYMENTS
```

### Foreign Keys

- `ORDERS.CUSTOMER_ID` → `CUSTOMER.CUSTOMER_ID`
- `ORDER_ITEMS.ORDER_ID` → `ORDERS.ORDER_ID`
- `ORDER_ITEMS.PRODUCT_ID` → `PRODUCTS.PRODUCT_ID`
- `PAYMENTS.ORDER_ID` → `ORDERS.ORDER_ID`

---

## Connection Details

### Source Database (Oracle 19c)

```
Host: localhost
Port: 1521
SID: ORCL19C
PDB: PDB19C
User: migration_user
Password: MigrationPwd123
Connection String: localhost:1521/PDB19C
```

**SQL*Plus:**
```bash
sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C
```

**JDBC:**
```
jdbc:oracle:thin:@localhost:1521/PDB19C
```

### Target Database (Oracle 23c)

```
Host: localhost
Port: 1522
SID: ORCL23C
PDB: PDB23C
User: migration_user
Password: MigrationPwd123
Connection String: localhost:1522/PDB23C
```

**SQL*Plus:**
```bash
sqlplus migration_user/MigrationPwd123@localhost:1522/PDB23C
```

**JDBC:**
```
jdbc:oracle:thin:@localhost:1522/PDB23C
```

### SYS User (Admin)

**Source:**
```bash
sqlplus sys/OraclePwd123@localhost:1521/ORCL19C as sysdba
```

**Target:**
```bash
sqlplus sys/OraclePwd123@localhost:1522/ORCL23C as sysdba
```

---

## Testing Connections

### Using SQL*Plus

```bash
# Test source
docker exec -it oracle-migration-source sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C

# Test target
docker exec -it oracle-migration-target sqlplus migration_user/MigrationPwd123@localhost:1522/PDB23C
```

### Using Python

```python
import oracledb

# Source
connection = oracledb.connect(
    user="migration_user",
    password="MigrationPwd123",
    dsn="localhost:1521/PDB19C"
)

# Test query
cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM CUSTOMER")
print(f"Customers: {cursor.fetchone()[0]}")
connection.close()
```

### Using the API

```bash
curl -X POST http://localhost:8000/api/discovery/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "db_id": "source_19c",
    "db_type": "oracle_19c_standalone",
    "host": "localhost",
    "port": 1521,
    "service_name": "PDB19C",
    "username": "migration_user",
    "password": "MigrationPwd123"
  }'
```

---

## Connecting the POC to Real Databases

### Step 1: Update Environment Variables

Edit `oracle-migration-poc/.env`:

```bash
# Disable mock mode
ENABLE_MOCK_MODE=false

# Source Database (Oracle 19c)
ORACLE_SOURCE_HOST=localhost
ORACLE_SOURCE_PORT=1521
ORACLE_SOURCE_SERVICE=PDB19C
ORACLE_SOURCE_USER=migration_user
ORACLE_SOURCE_PASSWORD=MigrationPwd123

# Target Database (Oracle 23c)
ORACLE_TARGET_HOST=localhost
ORACLE_TARGET_PORT=1522
ORACLE_TARGET_SERVICE=PDB23C
ORACLE_TARGET_USER=migration_user
ORACLE_TARGET_PASSWORD=MigrationPwd123
```

### Step 2: Restart POC Backend

```bash
cd oracle-migration-poc
docker-compose restart backend
```

### Step 3: Test in UI

1. Open http://localhost:3000
2. Select databases
3. Tables should now show real data from Oracle

---

## Database Management

### Start Databases

```bash
docker-compose -f docker-compose-oracle.yml start
```

### Stop Databases

```bash
docker-compose -f docker-compose-oracle.yml stop
```

### Restart Databases

```bash
docker-compose -f docker-compose-oracle.yml restart
```

### View Logs

```bash
# All databases
docker-compose -f docker-compose-oracle.yml logs -f

# Source only
docker logs -f oracle-migration-source

# Target only
docker logs -f oracle-migration-target
```

### Remove Everything

**⚠️ WARNING: This deletes all data!**

```bash
docker-compose -f docker-compose-oracle.yml down -v
```

---

## Troubleshooting

### Database Won't Start

**Check Docker resources:**
```bash
docker stats
```

Ensure you have:
- At least 6GB RAM available
- At least 10GB disk space

**Increase Docker Desktop limits:**
- Settings → Resources
- Set Memory to 8GB or higher
- Set Disk to 60GB or higher

### "No space left on device"

```bash
# Clean up Docker
docker system prune -a --volumes

# Remove stopped containers
docker container prune
```

### Database is Slow

**Increase shared memory:**

In `docker-compose-oracle.yml`:
```yaml
shm_size: 2gb  # Increase from 1gb
```

### Connection Refused

**Check if database is ready:**
```bash
docker exec -it oracle-migration-source sqlplus -s sys/OraclePwd123@localhost:1521/ORCL19C as sysdba <<< "SELECT 1 FROM DUAL;"
```

**Check health status:**
```bash
docker ps
```

Look for `healthy` status.

### Initialization Scripts Didn't Run

**Manually run scripts:**

```bash
# Enter container
docker exec -it oracle-migration-source bash

# Run scripts manually
cd /opt/oracle/scripts/setup
for f in *.sql; do
  sqlplus /nolog @$f
done
```

### Reset Database to Initial State

```bash
# Stop and remove
docker-compose -f docker-compose-oracle.yml down -v

# Start fresh
docker-compose -f docker-compose-oracle.yml up -d

# Wait for initialization (10-15 minutes)
```

---

## Performance Tuning

### Increase Memory

Edit `docker-compose-oracle.yml`:

```yaml
environment:
  - ORACLE_PWD=OraclePwd123
  - ORACLE_SID=ORCL19C
  - ORACLE_PDB=PDB19C
  - INIT_SGA_SIZE=1G      # Add this
  - INIT_PGA_SIZE=512M     # Add this
```

### Optimize for SSD

If running on SSD, disable some write operations:

```sql
ALTER SYSTEM SET filesystemio_options=SETALL SCOPE=SPFILE;
```

---

## Monitoring

### Check Database Size

```sql
SELECT 
  TABLESPACE_NAME,
  ROUND(SUM(BYTES)/1024/1024, 2) AS SIZE_MB
FROM DBA_DATA_FILES
GROUP BY TABLESPACE_NAME;
```

### Check Table Sizes

```sql
SELECT 
  table_name,
  num_rows,
  ROUND(blocks * 8 / 1024, 2) AS size_mb
FROM user_tables
ORDER BY num_rows DESC;
```

### Monitor Performance

```sql
-- Session activity
SELECT * FROM v$session WHERE username = 'MIGRATION_USER';

-- Wait events
SELECT event, total_waits, time_waited
FROM v$system_event
WHERE wait_class != 'Idle'
ORDER BY time_waited DESC;
```

---

## Enterprise Manager

### Access Web Console

**Source:**
- URL: https://localhost:5500/em
- User: sys
- Password: OraclePwd123
- Container: PDB19C

**Target:**
- URL: https://localhost:5501/em
- User: sys
- Password: OraclePwd123
- Container: PDB23C

⚠️ Note: Self-signed certificate warning is expected

---

## Backup & Restore

### Backup Source Database

```bash
# Create backup directory
mkdir -p ./backups

# Export schema
docker exec oracle-migration-source expdp migration_user/MigrationPwd123@PDB19C \
  directory=DATA_PUMP_DIR \
  dumpfile=migration_backup.dmp \
  logfile=migration_backup.log \
  schemas=migration_user
```

### Restore to Target

```bash
# Import to target
docker exec oracle-migration-target impdp migration_user/MigrationPwd123@PDB23C \
  directory=DATA_PUMP_DIR \
  dumpfile=migration_backup.dmp \
  logfile=migration_restore.log \
  schemas=migration_user
```

---

## Network Configuration

### Connect from Other Docker Containers

Both databases are on the `oracle-migration-network` bridge.

**From POC backend:**
```
Host: oracle-source
Port: 1521
Service: PDB19C

Host: oracle-target
Port: 1521  # Note: internal port, not 1522
Service: PDB23C
```

### Connect from Host Machine

Use `localhost` with mapped ports:
- Source: `localhost:1521`
- Target: `localhost:1522`

---

## Security Notes

### Production Checklist

For production use, change:

- [ ] Default passwords
- [ ] Enable TLS/SSL
- [ ] Configure proper user permissions
- [ ] Set up network encryption
- [ ] Enable audit logging
- [ ] Configure backup schedule
- [ ] Implement proper firewall rules

### Changing Passwords

```sql
-- As SYS
ALTER USER migration_user IDENTIFIED BY NewSecurePassword123;

-- As migration_user
ALTER USER migration_user IDENTIFIED BY NewSecurePassword123;
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start databases | `docker-compose -f docker-compose-oracle.yml up -d` |
| Stop databases | `docker-compose -f docker-compose-oracle.yml stop` |
| View logs | `docker logs -f oracle-migration-source` |
| Connect (source) | `sqlplus migration_user/MigrationPwd123@localhost:1521/PDB19C` |
| Connect (target) | `sqlplus migration_user/MigrationPwd123@localhost:1522/PDB23C` |
| Check status | `docker ps` |
| Remove all | `docker-compose -f docker-compose-oracle.yml down -v` |

---

## Support

For Oracle-specific issues:
- [Oracle Documentation](https://docs.oracle.com/en/database/)
- [Oracle Container Registry](https://container-registry.oracle.com/)
- [Oracle Forums](https://community.oracle.com/)

For POC-specific issues:
- Check backend logs: `docker-compose logs -f backend`
- Review API docs: http://localhost:8000/docs
- Test connections via API

---

**Your Oracle databases are now ready for migration testing! 🚀**
