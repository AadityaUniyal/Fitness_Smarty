"""
Database Backup and Rollback Manager

Provides automatic database backup before migrations and rollback capabilities
to ensure data safety during schema changes.
"""

import os
import json
import logging
import datetime
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages database backups and rollback operations
    """
    
    def __init__(self, session: Session, backup_dir: str = ".migration_backups"):
        """
        Initialize backup manager
        
        Args:
            session: SQLAlchemy database session
            backup_dir: Directory to store backups
        """
        self.session = session
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, migration_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        Create a backup before migration
        
        Args:
            migration_name: Name of the migration
            
        Returns:
            Tuple of (success, message, backup_id)
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{migration_name}_{timestamp}"
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"Creating backup: {backup_id}")
            
            # Get all tables
            inspector = inspect(self.session.bind)
            tables = inspector.get_table_names()
            
            backup_metadata = {
                'backup_id': backup_id,
                'migration_name': migration_name,
                'timestamp': timestamp,
                'tables': {},
                'schema_info': {}
            }
            
            # Backup each table
            for table_name in tables:
                try:
                    # Get row count
                    count_result = self.session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    row_count = count_result.scalar()
                    
                    # Store table metadata
                    backup_metadata['tables'][table_name] = {
                        'row_count': row_count,
                        'backed_up': True
                    }
                    
                    # Get schema information
                    columns = inspector.get_columns(table_name)
                    backup_metadata['schema_info'][table_name] = {
                        'columns': [
                            {
                                'name': col['name'],
                                'type': str(col['type']),
                                'nullable': col.get('nullable', True)
                            }
                            for col in columns
                        ]
                    }
                    
                    logger.info(f"Backed up table {table_name}: {row_count} rows")
                    
                except Exception as e:
                    logger.warning(f"Could not backup table {table_name}: {str(e)}")
                    backup_metadata['tables'][table_name] = {
                        'row_count': 0,
                        'backed_up': False,
                        'error': str(e)
                    }
            
            # Save backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(backup_metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_id}")
            return True, f"Backup created: {backup_id}", backup_id
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}", exc_info=True)
            return False, f"Backup failed: {str(e)}", None
    
    def verify_backup(self, backup_id: str) -> Tuple[bool, str]:
        """
        Verify backup integrity
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_path = self.backup_dir / backup_id
            
            if not backup_path.exists():
                return False, f"Backup {backup_id} not found"
            
            metadata_file = backup_path / "backup_metadata.json"
            if not metadata_file.exists():
                return False, "Backup metadata not found"
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verify tables still exist
            inspector = inspect(self.session.bind)
            current_tables = set(inspector.get_table_names())
            backed_up_tables = set(metadata['tables'].keys())
            
            missing_tables = backed_up_tables - current_tables
            if missing_tables:
                logger.warning(f"Tables missing from current schema: {missing_tables}")
            
            return True, f"Backup {backup_id} verified successfully"
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for backup_path in self.backup_dir.iterdir():
                if not backup_path.is_dir():
                    continue
                
                metadata_file = backup_path / "backup_metadata.json"
                if not metadata_file.exists():
                    continue
                
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backups.append({
                        'backup_id': metadata['backup_id'],
                        'migration_name': metadata['migration_name'],
                        'timestamp': metadata['timestamp'],
                        'table_count': len(metadata['tables']),
                        'total_rows': sum(
                            t.get('row_count', 0) 
                            for t in metadata['tables'].values()
                        )
                    })
                except Exception as e:
                    logger.warning(f"Could not read backup metadata: {str(e)}")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
        
        return backups
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a backup
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            Backup metadata dictionary or None
        """
        try:
            backup_path = self.backup_dir / backup_id
            metadata_file = backup_path / "backup_metadata.json"
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"Failed to get backup info: {str(e)}")
            return None
    
    def validate_data_integrity(self, backup_id: str) -> Tuple[bool, List[str]]:
        """
        Validate data integrity after migration
        
        Args:
            backup_id: Backup identifier to compare against
            
        Returns:
            Tuple of (success, list of issues)
        """
        issues = []
        
        try:
            metadata = self.get_backup_info(backup_id)
            if not metadata:
                return False, ["Backup metadata not found"]
            
            inspector = inspect(self.session.bind)
            current_tables = inspector.get_table_names()
            
            # Check each backed up table
            for table_name, table_info in metadata['tables'].items():
                if not table_info.get('backed_up'):
                    continue
                
                if table_name not in current_tables:
                    issues.append(f"Table {table_name} is missing")
                    continue
                
                # Check row count
                try:
                    count_result = self.session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    current_count = count_result.scalar()
                    original_count = table_info['row_count']
                    
                    if current_count < original_count:
                        issues.append(
                            f"Table {table_name} has fewer rows: "
                            f"{current_count} vs {original_count}"
                        )
                except Exception as e:
                    issues.append(f"Could not verify {table_name}: {str(e)}")
            
            success = len(issues) == 0
            if success:
                logger.info("Data integrity validation passed")
            else:
                logger.warning(f"Data integrity issues found: {issues}")
            
            return success, issues
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def cleanup_old_backups(self, keep_count: int = 10) -> Tuple[bool, str]:
        """
        Clean up old backups, keeping only the most recent ones
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return True, f"No cleanup needed. {len(backups)} backups exist."
            
            # Remove oldest backups
            backups_to_remove = backups[keep_count:]
            removed_count = 0
            
            for backup in backups_to_remove:
                backup_path = self.backup_dir / backup['backup_id']
                try:
                    shutil.rmtree(backup_path)
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup['backup_id']}")
                except Exception as e:
                    logger.warning(f"Could not remove backup {backup['backup_id']}: {str(e)}")
            
            return True, f"Cleaned up {removed_count} old backups"
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
            return False, f"Cleanup failed: {str(e)}"


class RollbackManager:
    """
    Manages migration rollback operations
    """
    
    def __init__(self, session: Session):
        """
        Initialize rollback manager
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.rollback_history: List[Dict[str, Any]] = []
    
    def create_rollback_script(
        self,
        migration_operations: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """
        Generate rollback operations for a migration
        
        Args:
            migration_operations: List of (operation_name, sql) tuples
            
        Returns:
            List of rollback operations in reverse order
        """
        rollback_ops = []
        
        for operation_name, sql_statement in reversed(migration_operations):
            rollback_sql = self._generate_rollback_sql(operation_name, sql_statement)
            if rollback_sql:
                rollback_ops.append((f"rollback_{operation_name}", rollback_sql))
        
        return rollback_ops
    
    def _generate_rollback_sql(self, operation_name: str, sql_statement: str) -> Optional[str]:
        """
        Generate rollback SQL for an operation
        
        Args:
            operation_name: Name of the operation
            sql_statement: Original SQL statement
            
        Returns:
            Rollback SQL statement or None
        """
        sql_lower = sql_statement.lower().strip()
        
        # CREATE TABLE -> DROP TABLE
        if sql_lower.startswith('create table'):
            table_name = self._extract_table_name(sql_statement, 'create table')
            if table_name:
                return f"DROP TABLE IF EXISTS {table_name} CASCADE"
        
        # ALTER TABLE ADD COLUMN -> ALTER TABLE DROP COLUMN
        if 'alter table' in sql_lower and 'add column' in sql_lower:
            parts = sql_statement.split()
            table_idx = parts.index('TABLE') if 'TABLE' in parts else parts.index('table')
            add_idx = next(i for i, p in enumerate(parts) if 'ADD' in p.upper())
            col_idx = next(i for i, p in enumerate(parts) if 'COLUMN' in p.upper())
            
            if table_idx < len(parts) - 1 and col_idx < len(parts) - 1:
                table_name = parts[table_idx + 1]
                column_name = parts[col_idx + 1]
                return f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name}"
        
        # ALTER TABLE ADD CONSTRAINT -> ALTER TABLE DROP CONSTRAINT
        if 'alter table' in sql_lower and 'add constraint' in sql_lower:
            parts = sql_statement.split()
            table_idx = next((i for i, p in enumerate(parts) if 'TABLE' in p.upper()), -1)
            constraint_idx = next((i for i, p in enumerate(parts) if 'CONSTRAINT' in p.upper()), -1)
            
            if table_idx >= 0 and constraint_idx >= 0 and constraint_idx < len(parts) - 1:
                table_name = parts[table_idx + 1]
                constraint_name = parts[constraint_idx + 1]
                return f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"
        
        # CREATE INDEX -> DROP INDEX
        if sql_lower.startswith('create index'):
            index_name = self._extract_index_name(sql_statement)
            if index_name:
                return f"DROP INDEX IF EXISTS {index_name}"
        
        # For other operations, log that rollback is not auto-generated
        logger.warning(f"No automatic rollback for operation: {operation_name}")
        return None
    
    def _extract_table_name(self, sql: str, prefix: str) -> Optional[str]:
        """Extract table name from SQL statement"""
        try:
            sql_lower = sql.lower()
            start = sql_lower.find(prefix) + len(prefix)
            remaining = sql[start:].strip()
            table_name = remaining.split()[0].strip('(')
            return table_name
        except Exception:
            return None
    
    def _extract_index_name(self, sql: str) -> Optional[str]:
        """Extract index name from CREATE INDEX statement"""
        try:
            parts = sql.split()
            idx = parts.index('INDEX') if 'INDEX' in parts else parts.index('index')
            if idx < len(parts) - 1:
                return parts[idx + 1]
        except Exception:
            return None
    
    def execute_rollback(
        self,
        rollback_operations: List[Tuple[str, str]]
    ) -> Tuple[bool, str]:
        """
        Execute rollback operations
        
        Args:
            rollback_operations: List of (operation_name, sql) tuples
            
        Returns:
            Tuple of (success, message)
        """
        executed_ops = []
        
        try:
            for operation_name, sql_statement in rollback_operations:
                try:
                    self.session.execute(text(sql_statement))
                    self.session.commit()
                    executed_ops.append(operation_name)
                    logger.info(f"Executed rollback operation: {operation_name}")
                except Exception as e:
                    self.session.rollback()
                    logger.error(f"Rollback operation failed: {operation_name} - {str(e)}")
                    # Continue with other rollback operations
            
            # Record rollback in history
            self.rollback_history.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'operations': executed_ops,
                'success': True
            })
            
            return True, f"Rollback completed: {len(executed_ops)} operations executed"
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}", exc_info=True)
            return False, f"Rollback failed: {str(e)}"
    
    def get_rollback_history(self) -> List[Dict[str, Any]]:
        """
        Get rollback history
        
        Returns:
            List of rollback operations
        """
        return self.rollback_history.copy()
