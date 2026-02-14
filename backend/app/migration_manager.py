"""
Database Migration Manager for safe schema changes with data preservation.

This module provides a robust migration system that ensures data safety during
database schema changes, supporting rollback and transaction management.
"""

from typing import List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
import logging
from .backup_manager import BackupManager, RollbackManager

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database schema migrations with data safety guarantees.
    
    Ensures that all migrations preserve existing data and can be rolled back
    if errors occur during the migration process.
    """
    
    def __init__(self, session: Session, backup_dir: str = ".migration_backups"):
        """
        Initialize the migration manager with a database session.
        
        Args:
            session: SQLAlchemy database session
            backup_dir: Directory for backups
        """
        self.session = session
        self.applied_operations: List[str] = []
        self.backup_manager = BackupManager(session, backup_dir)
        self.rollback_manager = RollbackManager(session)
    
    def execute_migration(
        self,
        migration_name: str,
        operations: List[Tuple[str, str]],
        create_backup: bool = True
    ) -> Tuple[bool, str]:
        """
        Execute a list of migration operations safely with automatic backup.
        
        Each operation is executed in its own transaction to prevent
        transaction abort issues in PostgreSQL.
        
        Args:
            migration_name: Name of the migration
            operations: List of (operation_name, sql_statement) tuples
            create_backup: Whether to create a backup before migration
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        backup_id = None
        
        # Create backup before migration
        if create_backup:
            success, message, backup_id = self.backup_manager.create_backup(migration_name)
            if not success:
                logger.error(f"Backup failed: {message}")
                return False, f"Migration aborted: {message}"
            logger.info(f"Backup created: {backup_id}")
        
        # Generate rollback script
        rollback_ops = self.rollback_manager.create_rollback_script(operations)
        
        # Execute migration operations
        for operation_name, sql_statement in operations:
            success, message = self._execute_single_operation(operation_name, sql_statement)
            if not success:
                logger.error(f"Migration failed at {operation_name}: {message}")
                
                # Attempt rollback
                if rollback_ops:
                    logger.info("Attempting automatic rollback...")
                    rollback_success, rollback_msg = self.rollback_manager.execute_rollback(rollback_ops)
                    if rollback_success:
                        return False, f"Migration failed at {operation_name}: {message}. Rollback successful."
                    else:
                        return False, f"Migration failed at {operation_name}: {message}. Rollback also failed: {rollback_msg}"
                
                return False, f"Migration failed at {operation_name}: {message}"
            
            self.applied_operations.append(operation_name)
        
        # Validate data integrity after migration
        if backup_id:
            integrity_ok, issues = self.backup_manager.validate_data_integrity(backup_id)
            if not integrity_ok:
                logger.warning(f"Data integrity issues detected: {issues}")
                return True, f"Migration completed with warnings: {'; '.join(issues)}"
        
        return True, f"Migration completed successfully. Applied {len(self.applied_operations)} operations."
    
    def _execute_single_operation(self, operation_name: str, sql_statement: str) -> Tuple[bool, str]:
        """
        Execute a single migration operation in its own transaction.
        
        Args:
            operation_name: Name of the operation for logging
            sql_statement: SQL statement to execute
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.session.execute(text(sql_statement))
            self.session.commit()
            logger.info(f"Successfully executed migration operation: {operation_name}")
            return True, f"Operation {operation_name} completed"
            
        except IntegrityError as e:
            self.session.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Check if this is a benign error (object already exists)
            if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate']):
                logger.warning(f"Operation {operation_name} skipped: object already exists")
                return True, f"Operation {operation_name} skipped (already exists)"
            
            logger.error(f"Integrity error in {operation_name}: {error_msg}")
            return False, f"Integrity error: {error_msg}"
            
        except OperationalError as e:
            self.session.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Check if this is a benign error (object already exists)
            if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate']):
                logger.warning(f"Operation {operation_name} skipped: object already exists")
                return True, f"Operation {operation_name} skipped (already exists)"
            
            logger.error(f"Operational error in {operation_name}: {error_msg}")
            return False, f"Operational error: {error_msg}"
            
        except Exception as e:
            self.session.rollback()
            error_msg = str(e)
            
            # Check if this is a benign error (object already exists)
            if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate']):
                logger.warning(f"Operation {operation_name} skipped: object already exists")
                return True, f"Operation {operation_name} skipped (already exists)"
            
            logger.error(f"Unexpected error in {operation_name}: {error_msg}")
            return False, f"Unexpected error: {error_msg}"
    
    def add_index(self, table_name: str, column_name: str, index_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Add an index to a table column safely.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to index
            index_name: Optional custom index name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if index_name is None:
            index_name = f"idx_{table_name}_{column_name}"
        
        sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
        return self._execute_single_operation(f"add_index_{index_name}", sql)
    
    def add_constraint(self, table_name: str, constraint_name: str, constraint_definition: str) -> Tuple[bool, str]:
        """
        Add a constraint to a table safely.
        
        Args:
            table_name: Name of the table
            constraint_name: Name of the constraint
            constraint_definition: SQL constraint definition (e.g., "CHECK (level > 0)")
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        sql = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} {constraint_definition}"
        return self._execute_single_operation(f"add_constraint_{constraint_name}", sql)
    
    def drop_index(self, index_name: str) -> Tuple[bool, str]:
        """
        Drop an index safely.
        
        Args:
            index_name: Name of the index to drop
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        sql = f"DROP INDEX IF EXISTS {index_name}"
        return self._execute_single_operation(f"drop_index_{index_name}", sql)
    
    def drop_constraint(self, table_name: str, constraint_name: str) -> Tuple[bool, str]:
        """
        Drop a constraint safely.
        
        Args:
            table_name: Name of the table
            constraint_name: Name of the constraint to drop
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        sql = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"
        return self._execute_single_operation(f"drop_constraint_{constraint_name}", sql)
    
    def verify_data_integrity(self, table_name: str, expected_count: Optional[int] = None) -> Tuple[bool, str]:
        """
        Verify that data exists in a table after migration.
        
        Args:
            table_name: Name of the table to verify
            expected_count: Optional expected row count
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            result = self.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            actual_count = result.scalar()
            
            if expected_count is not None:
                if actual_count == expected_count:
                    return True, f"Data integrity verified: {actual_count} rows in {table_name}"
                else:
                    return False, f"Data count mismatch: expected {expected_count}, found {actual_count}"
            else:
                return True, f"Data integrity verified: {actual_count} rows in {table_name}"
                
        except Exception as e:
            logger.error(f"Data integrity verification failed for {table_name}: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    def get_applied_operations(self) -> List[str]:
        """
        Get the list of successfully applied operations.
        
        Returns:
            List of operation names
        """
        return self.applied_operations.copy()
