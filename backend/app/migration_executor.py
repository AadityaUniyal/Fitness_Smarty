"""
MigrationExecutor class for safe file move operations with rollback capability.
Validates Requirements 1.3
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

from .file_analyzer import FileInfo, FileType
from .path_resolver import PathResolver, ImportUpdate


class MigrationStatus(Enum):
    """Status of a migration operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class FileOperation:
    """Represents a single file operation in a migration"""
    operation_id: str
    operation_type: str  # 'move', 'copy', 'create_dir', 'update_content'
    source_path: Optional[Path]
    target_path: Path
    backup_path: Optional[Path] = None
    completed: bool = False
    error: Optional[str] = None


@dataclass
class MigrationPlan:
    """Complete migration plan with all operations"""
    migration_id: str
    description: str
    operations: List[FileOperation]
    import_updates: List[ImportUpdate]
    created_at: datetime
    status: MigrationStatus = MigrationStatus.PENDING


@dataclass
class MigrationResult:
    """Result of a migration execution"""
    migration_id: str
    status: MigrationStatus
    completed_operations: int
    total_operations: int
    failed_operations: List[str]
    execution_time_seconds: float
    rollback_available: bool
    error_message: Optional[str] = None


class MigrationExecutor:
    """Executes file reorganization migrations with transaction-like behavior and rollback capability"""
    
    def __init__(self, project_root: Path, backup_dir: Optional[Path] = None):
        """Initialize MigrationExecutor with project root and backup directory"""
        self.project_root = Path(project_root)
        self.backup_dir = backup_dir or (self.project_root / ".migration_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}_{id(self)}")  # Unique logger per instance
        self._setup_logging()
        
        # Migration state
        self.active_migrations: Dict[str, MigrationPlan] = {}
        self.migration_history: List[MigrationResult] = []
        
        # Load existing migration state
        self._load_migration_state()

    def cleanup(self):
        """Cleanup resources and close file handles"""
        try:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
        except:
            pass

    def __del__(self):
        """Cleanup logger handlers on destruction"""
        self.cleanup()

    def _setup_logging(self):
        """Setup comprehensive logging for migration operations"""
        log_file = self.backup_dir / "migration.log"
        
        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

    def create_migration_plan(
        self, 
        file_infos: List[FileInfo], 
        target_structure: Dict[str, Path],
        description: str = "File reorganization migration"
    ) -> MigrationPlan:
        """Create a comprehensive migration plan"""
        migration_id = str(uuid.uuid4())
        operations = []
        
        self.logger.info(f"Creating migration plan {migration_id}: {description}")
        
        # Create directory operations first
        directories_to_create = set()
        for file_info in file_infos:
            if file_info.path in target_structure:
                target_path = target_structure[file_info.path]
                directories_to_create.add(target_path.parent)
        
        # Add directory creation operations
        for directory in sorted(directories_to_create):
            if not directory.exists():
                operations.append(FileOperation(
                    operation_id=str(uuid.uuid4()),
                    operation_type="create_dir",
                    source_path=None,
                    target_path=directory
                ))
        
        # Add file move operations
        for file_info in file_infos:
            if file_info.path in target_structure:
                target_path = target_structure[file_info.path]
                backup_path = self._get_backup_path(migration_id, file_info.path)
                
                operations.append(FileOperation(
                    operation_id=str(uuid.uuid4()),
                    operation_type="move",
                    source_path=file_info.path,
                    target_path=target_path,
                    backup_path=backup_path
                ))
        
        # Create path resolver for import updates
        path_resolver = PathResolver(self.project_root)
        import_updates = []
        
        # Calculate import updates for moved files
        for file_info in file_infos:
            if file_info.path in target_structure:
                old_path = file_info.path
                new_path = target_structure[file_info.path]
                path_resolver.add_path_mapping(old_path, new_path, file_info.file_type)
        
        # Generate import updates for all affected files
        import_updates = path_resolver.generate_import_updates(file_infos)
        
        migration_plan = MigrationPlan(
            migration_id=migration_id,
            description=description,
            operations=operations,
            import_updates=import_updates,
            created_at=datetime.now(),
            status=MigrationStatus.PENDING
        )
        
        self.active_migrations[migration_id] = migration_plan
        self._save_migration_state()
        
        self.logger.info(f"Migration plan {migration_id} created with {len(operations)} operations")
        return migration_plan

    def execute_migration(self, migration_plan: MigrationPlan) -> MigrationResult:
        """Execute a migration plan with transaction-like behavior"""
        start_time = datetime.now()
        migration_id = migration_plan.migration_id
        
        self.logger.info(f"Starting migration execution: {migration_id}")
        
        # Update status
        migration_plan.status = MigrationStatus.IN_PROGRESS
        self._save_migration_state()
        
        completed_operations = 0
        failed_operations = []
        rollback_available = True
        
        try:
            # Execute directory creation operations first
            for operation in migration_plan.operations:
                if operation.operation_type == "create_dir":
                    success = self._execute_directory_operation(operation)
                    if success:
                        completed_operations += 1
                        operation.completed = True
                    else:
                        failed_operations.append(operation.operation_id)
                        rollback_available = False
                        break
            
            # Execute file move operations
            if not failed_operations:
                for operation in migration_plan.operations:
                    if operation.operation_type == "move":
                        success = self._execute_move_operation(operation)
                        if success:
                            completed_operations += 1
                            operation.completed = True
                        else:
                            failed_operations.append(operation.operation_id)
                            break
            
            # Execute import updates
            if not failed_operations:
                for import_update in migration_plan.import_updates:
                    success = self._execute_import_update(import_update)
                    if not success:
                        failed_operations.append(f"import_update_{import_update.file_path}")
                        break
            
            # Determine final status
            if failed_operations:
                migration_plan.status = MigrationStatus.FAILED
                self.logger.error(f"Migration {migration_id} failed with {len(failed_operations)} failed operations")
            else:
                migration_plan.status = MigrationStatus.COMPLETED
                self.logger.info(f"Migration {migration_id} completed successfully")
                
        except Exception as e:
            migration_plan.status = MigrationStatus.FAILED
            failed_operations.append(f"exception: {str(e)}")
            rollback_available = False
            self.logger.error(f"Migration {migration_id} failed with exception: {e}")
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Create result
        result = MigrationResult(
            migration_id=migration_id,
            status=migration_plan.status,
            completed_operations=completed_operations,
            total_operations=len(migration_plan.operations),
            failed_operations=failed_operations,
            execution_time_seconds=execution_time,
            rollback_available=rollback_available,
            error_message="; ".join(failed_operations) if failed_operations else None
        )
        
        # Save state and add to history
        self.migration_history.append(result)
        self._save_migration_state()
        
        return result

    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration to its previous state"""
        self.logger.info(f"Starting rollback for migration: {migration_id}")
        
        if migration_id not in self.active_migrations:
            self.logger.error(f"Migration {migration_id} not found in active migrations")
            return False
        
        migration_plan = self.active_migrations[migration_id]
        
        if migration_plan.status not in [MigrationStatus.COMPLETED, MigrationStatus.FAILED]:
            self.logger.error(f"Cannot rollback migration {migration_id} with status {migration_plan.status}")
            return False
        
        try:
            # Rollback in reverse order
            rollback_success = True
            
            # Rollback import updates first
            for import_update in reversed(migration_plan.import_updates):
                success = self._rollback_import_update(import_update)
                if not success:
                    rollback_success = False
                    self.logger.error(f"Failed to rollback import update for {import_update.file_path}")
            
            # Rollback file operations
            for operation in reversed(migration_plan.operations):
                if operation.completed:
                    success = self._rollback_operation(operation)
                    if not success:
                        rollback_success = False
                        self.logger.error(f"Failed to rollback operation {operation.operation_id}")
            
            if rollback_success:
                migration_plan.status = MigrationStatus.ROLLED_BACK
                self.logger.info(f"Migration {migration_id} rolled back successfully")
            else:
                self.logger.error(f"Migration {migration_id} rollback completed with errors")
            
            self._save_migration_state()
            return rollback_success
            
        except Exception as e:
            self.logger.error(f"Rollback failed for migration {migration_id}: {e}")
            return False

    def _execute_directory_operation(self, operation: FileOperation) -> bool:
        """Execute a directory creation operation"""
        try:
            operation.target_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {operation.target_path}")
            return True
        except Exception as e:
            operation.error = str(e)
            self.logger.error(f"Failed to create directory {operation.target_path}: {e}")
            return False

    def _execute_move_operation(self, operation: FileOperation) -> bool:
        """Execute a file move operation with backup"""
        try:
            # Create backup first
            if operation.backup_path:
                operation.backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(operation.source_path, operation.backup_path)
                self.logger.debug(f"Created backup: {operation.source_path} -> {operation.backup_path}")
            
            # Ensure target directory exists
            operation.target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(operation.source_path), str(operation.target_path))
            self.logger.debug(f"Moved file: {operation.source_path} -> {operation.target_path}")
            return True
            
        except Exception as e:
            operation.error = str(e)
            self.logger.error(f"Failed to move file {operation.source_path} -> {operation.target_path}: {e}")
            return False

    def _execute_import_update(self, import_update: ImportUpdate) -> bool:
        """Execute an import path update"""
        try:
            file_path = import_update.file_path
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply the import update
            updated_content = content.replace(import_update.old_import, import_update.new_import)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.debug(f"Updated import in {file_path}: {import_update.old_import} -> {import_update.new_import}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update import in {file_path}: {e}")
            return False

    def _rollback_operation(self, operation: FileOperation) -> bool:
        """Rollback a single operation"""
        try:
            if operation.operation_type == "move" and operation.backup_path:
                # Restore from backup
                if operation.backup_path.exists():
                    # Remove the moved file if it exists
                    if operation.target_path.exists():
                        operation.target_path.unlink()
                    
                    # Restore original file
                    operation.source_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(operation.backup_path), str(operation.source_path))
                    self.logger.debug(f"Restored file: {operation.backup_path} -> {operation.source_path}")
                    return True
                    
            elif operation.operation_type == "create_dir":
                # Remove created directory if empty
                if operation.target_path.exists() and operation.target_path.is_dir():
                    try:
                        operation.target_path.rmdir()  # Only removes if empty
                        self.logger.debug(f"Removed directory: {operation.target_path}")
                    except OSError:
                        # Directory not empty, leave it
                        pass
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to rollback operation {operation.operation_id}: {e}")
            return False

    def _rollback_import_update(self, import_update: ImportUpdate) -> bool:
        """Rollback an import update"""
        try:
            file_path = import_update.file_path
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reverse the import update
            updated_content = content.replace(import_update.new_import, import_update.old_import)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.debug(f"Rolled back import in {file_path}: {import_update.new_import} -> {import_update.old_import}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback import in {file_path}: {e}")
            return False

    def _get_backup_path(self, migration_id: str, original_path: Path) -> Path:
        """Generate backup path for a file"""
        relative_path = original_path.relative_to(self.project_root)
        backup_path = self.backup_dir / migration_id / relative_path
        return backup_path

    def _save_migration_state(self):
        """Save migration state to disk"""
        try:
            state_file = self.backup_dir / "migration_state.json"
            
            # Convert to serializable format
            state = {
                "active_migrations": {
                    mid: {
                        **asdict(plan),
                        "created_at": plan.created_at.isoformat(),
                        "status": plan.status.value,
                        "operations": [
                            {
                                **asdict(op),
                                "source_path": str(op.source_path) if op.source_path else None,
                                "target_path": str(op.target_path),
                                "backup_path": str(op.backup_path) if op.backup_path else None
                            }
                            for op in plan.operations
                        ],
                        "import_updates": [
                            {
                                **asdict(update),
                                "file_path": str(update.file_path)
                            }
                            for update in plan.import_updates
                        ]
                    }
                    for mid, plan in self.active_migrations.items()
                },
                "migration_history": [
                    {
                        **asdict(result),
                        "status": result.status.value
                    }
                    for result in self.migration_history
                ]
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save migration state: {e}")

    def _load_migration_state(self):
        """Load migration state from disk"""
        try:
            state_file = self.backup_dir / "migration_state.json"
            
            if not state_file.exists():
                return
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Load active migrations
            for mid, plan_data in state.get("active_migrations", {}).items():
                operations = []
                for op_data in plan_data["operations"]:
                    operations.append(FileOperation(
                        operation_id=op_data["operation_id"],
                        operation_type=op_data["operation_type"],
                        source_path=Path(op_data["source_path"]) if op_data["source_path"] else None,
                        target_path=Path(op_data["target_path"]),
                        backup_path=Path(op_data["backup_path"]) if op_data["backup_path"] else None,
                        completed=op_data["completed"],
                        error=op_data["error"]
                    ))
                
                import_updates = []
                for update_data in plan_data["import_updates"]:
                    import_updates.append(ImportUpdate(
                        file_path=Path(update_data["file_path"]),
                        old_import=update_data["old_import"],
                        new_import=update_data["new_import"],
                        line_number=update_data["line_number"]
                    ))
                
                plan = MigrationPlan(
                    migration_id=plan_data["migration_id"],
                    description=plan_data["description"],
                    operations=operations,
                    import_updates=import_updates,
                    created_at=datetime.fromisoformat(plan_data["created_at"]),
                    status=MigrationStatus(plan_data["status"])
                )
                
                self.active_migrations[mid] = plan
            
            # Load migration history
            for result_data in state.get("migration_history", []):
                result = MigrationResult(
                    migration_id=result_data["migration_id"],
                    status=MigrationStatus(result_data["status"]),
                    completed_operations=result_data["completed_operations"],
                    total_operations=result_data["total_operations"],
                    failed_operations=result_data["failed_operations"],
                    execution_time_seconds=result_data["execution_time_seconds"],
                    rollback_available=result_data["rollback_available"],
                    error_message=result_data.get("error_message")
                )
                
                self.migration_history.append(result)
                
        except Exception as e:
            self.logger.error(f"Failed to load migration state: {e}")

    def get_migration_status(self, migration_id: str) -> Optional[MigrationStatus]:
        """Get the status of a migration"""
        if migration_id in self.active_migrations:
            return self.active_migrations[migration_id].status
        
        # Check history
        for result in self.migration_history:
            if result.migration_id == migration_id:
                return result.status
        
        return None

    def list_active_migrations(self) -> List[str]:
        """List all active migration IDs"""
        return list(self.active_migrations.keys())

    def cleanup_completed_migrations(self, keep_days: int = 30):
        """Clean up old completed migrations and their backups"""
        cutoff_date = datetime.now() - datetime.timedelta(days=keep_days)
        
        migrations_to_remove = []
        for migration_id, plan in self.active_migrations.items():
            if (plan.status in [MigrationStatus.COMPLETED, MigrationStatus.ROLLED_BACK] and 
                plan.created_at < cutoff_date):
                migrations_to_remove.append(migration_id)
        
        for migration_id in migrations_to_remove:
            # Remove backup directory
            backup_path = self.backup_dir / migration_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # Remove from active migrations
            del self.active_migrations[migration_id]
            
            self.logger.info(f"Cleaned up migration {migration_id}")
        
        if migrations_to_remove:
            self._save_migration_state()