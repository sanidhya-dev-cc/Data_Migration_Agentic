<#
PowerShell helper to create migration_user and run repo schema on gvenzl Oracle containers.
Usage: Run from this folder in PowerShell: `.
un .\setup_oracle_poc.ps1` or dot-source it.
#>

param(
    [string]$SourceContainer = 'oracle-source',
    [string]$TargetContainer = 'oracle-target',
    [string]$PdbName = 'XEPDB1',
    [string]$SysPassword = 'Oracle123',
    [string]$MigrationUser = 'migration_user',
    [string]$MigrationPwd = 'MigrationPwd123'
)

Write-Host "Creating $MigrationUser in containers: $SourceContainer and $TargetContainer"

$sql = @"
ALTER SESSION SET CONTAINER = $PdbName;
CREATE USER $MigrationUser IDENTIFIED BY $MigrationPwd DEFAULT TABLESPACE USERS TEMPORARY TABLESPACE TEMP QUOTA UNLIMITED ON USERS;
GRANT CONNECT, RESOURCE, CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE SEQUENCE, CREATE PROCEDURE, SELECT ANY TABLE, SELECT ANY DICTIONARY TO $MigrationUser;
EXIT;
"@

$localSqlPath = Join-Path $PSScriptRoot 'create_user.sql'
$sql | Out-File -FilePath $localSqlPath -Encoding ASCII

Write-Host "Copying and executing on $SourceContainer..."
docker cp $localSqlPath "${SourceContainer}:/tmp/create_user.sql" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to copy SQL to $SourceContainer"; exit 1 }

docker exec -i $SourceContainer bash -c "sqlplus sys/$SysPassword@localhost:1521/$PdbName as sysdba @/tmp/create_user.sql"
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to execute SQL in $SourceContainer"; exit 1 }

Write-Host "Copying and executing on $TargetContainer..."
docker cp $localSqlPath "${TargetContainer}:/tmp/create_user.sql" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to copy SQL to $TargetContainer"; exit 1 }

docker exec -i $TargetContainer bash -c "sqlplus sys/$SysPassword@localhost:1521/$PdbName as sysdba @/tmp/create_user.sql"
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to execute SQL in $TargetContainer"; exit 1 }

Write-Host "Done. You can now test connectivity with the migration user ($MigrationUser/$MigrationPwd)."
