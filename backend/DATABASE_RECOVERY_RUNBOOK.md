# Smarty AI - Database Backup & Restore Runbook

This document details the step-by-step procedures for database backup creation and disaster recovery.

---

## 1. Backup Schedule Configuration
To schedule automatic daily backups of the SQLite database (`smarty_neural_core.db`), configure a standard Windows Task Scheduler task running the following command every night:

```powershell
copy-item "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\smarty_neural_core.db" "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\backups\smarty_backup_$(Get-Date -f 'yyyyMMdd_HHmmss').db"
```

---

## 2. Manual Backup Creation
Run this command to create a safe copy of the active database before deploying updates or performing migrations:

```powershell
# Create backup directory if missing
mkdir -p "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\backups"

# Run sqlite backup instruction
sqlite3 "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\smarty_neural_core.db" ".backup 'c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\backups\smarty_manual_pre_migration.db'"
```

---

## 3. Disaster Recovery Restore Procedure
If the active database becomes corrupted or encounters schema errors:

1. **Stop active server processes** to release file locks on SQLite.
2. **Move corrupted database to quarantine**:
   ```powershell
   mv "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\smarty_neural_core.db" "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\quarantine_corrupted.db"
   ```
3. **Restore from target backup**:
   ```powershell
   copy-item "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\backups\smarty_manual_pre_migration.db" "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\smarty_neural_core.db"
   ```
4. **Verify database integrity**:
   ```powershell
   sqlite3 "c:\Users\HP\OneDrive\Desktop\Smarty-reco\backend\smarty_neural_core.db" "PRAGMA integrity_check;"
   ```
   *Expected Output: `ok`*
5. **Restart server processes**.
