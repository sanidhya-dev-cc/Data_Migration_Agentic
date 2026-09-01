@echo off
REM Start Oracle Databases for Migration POC

echo ==========================================
echo Oracle Database Setup
echo ==========================================
echo.
echo Starting Oracle source and target databases...
echo This may take 10-20 minutes on first run.
echo.

cd %~dp0

REM Start databases
docker-compose -f docker-compose-oracle.yml up -d

echo.
echo ==========================================
echo Databases are starting up...
echo ==========================================
echo.
echo Source Database: localhost:1521 (PDB19C)
echo Target Database: localhost:1522 (PDB23C)
echo.
echo To monitor startup progress:
echo   docker logs -f oracle-migration-source
echo   docker logs -f oracle-migration-target
echo.
echo Wait for "DATABASE IS READY TO USE!" message
echo Then check with: docker ps
echo.

pause
