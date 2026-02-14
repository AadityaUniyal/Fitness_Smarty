#!/usr/bin/env python3
"""
Project File Reorganization Script
Executes the file reorganization migration on the existing fitness app codebase.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.file_organizer.file_analyzer import FileAnalyzer, FileType
from backend.file_organizer.migration_executor import MigrationExecutor
from backend.file_organizer.path_resolver import PathResolver


def create_target_structure(file_infos, project_root):
    """Create target directory structure mapping"""
    target_structure = {}
    
    frontend_dir = project_root / "frontend"
    backend_dir = project_root / "backend"
    
    for file_info in file_infos:
        current_path = file_info.path
        relative_path = current_path.relative_to(project_root)
        
        # Skip files already in backend directory (file organizer components)
        if str(relative_path).startswith("backend/"):
            continue
            
        # Skip files that should stay in root
        if file_info.file_type in [FileType.CONFIG_SHARED, FileType.DOCUMENTATION]:
            continue
            
        # Skip node_modules and other ignored directories
        if any(ignore in str(relative_path) for ignore in [
            "node_modules", "__pycache__", ".git", ".pytest_cache", 
            ".hypothesis", "dist", "build", ".venv", "venv"
        ]):
            continue
        
        # Determine target location
        if file_info.file_type in [
            FileType.FRONTEND_REACT, FileType.FRONTEND_TYPESCRIPT, 
            FileType.FRONTEND_JAVASCRIPT, FileType.FRONTEND_CSS, 
            FileType.FRONTEND_HTML, FileType.CONFIG_FRONTEND
        ]:
            # Frontend files
            if file_info.file_type == FileType.CONFIG_FRONTEND:
                # Config files go to frontend root
                target_structure[current_path] = frontend_dir / current_path.name
            else:
                # Source files go to frontend/src
                if current_path.name in ["index.html"]:
                    target_structure[current_path] = frontend_dir / "public" / current_path.name
                elif current_path.suffix in [".ts", ".tsx", ".js", ".jsx"]:
                    if str(relative_path).startswith("components/"):
                        target_structure[current_path] = frontend_dir / "src" / relative_path
                    elif str(relative_path).startswith("services/"):
                        target_structure[current_path] = frontend_dir / "src" / relative_path
                    else:
                        target_structure[current_path] = frontend_dir / "src" / current_path.name
                else:
                    target_structure[current_path] = frontend_dir / "src" / current_path.name
                    
        elif file_info.file_type in [FileType.BACKEND_PYTHON, FileType.CONFIG_BACKEND]:
            # Backend files
            if file_info.file_type == FileType.CONFIG_BACKEND:
                # Config files go to backend root
                target_structure[current_path] = backend_dir / current_path.name
            else:
                # Python source files go to backend/app
                if current_path.name in ["main.py", "server.py"]:
                    # Main entry points stay in backend root
                    target_structure[current_path] = backend_dir / current_path.name
                elif current_path.name.startswith("test_"):
                    # Test files go to backend/tests
                    target_structure[current_path] = backend_dir / "tests" / current_path.name
                else:
                    # Other Python files go to backend/app
                    target_structure[current_path] = backend_dir / "app" / current_path.name
    
    return target_structure


def main():
    """Execute the file reorganization"""
    project_root = Path(__file__).parent
    print(f"Starting file reorganization for project: {project_root}")
    
    # Initialize components
    analyzer = FileAnalyzer(project_root)
    executor = MigrationExecutor(project_root)
    
    try:
        # Analyze current project structure
        print("Analyzing current project structure...")
        file_infos = analyzer.analyze_directory(project_root)
        
        print(f"Found {len(file_infos)} files to analyze")
        
        # Filter out files that should be reorganized
        files_to_move = []
        for file_info in file_infos:
            # Skip files already in backend/file_organizer
            if "backend/file_organizer" in str(file_info.path):
                continue
            # Skip files that should stay in root
            if file_info.file_type in [FileType.CONFIG_SHARED, FileType.DOCUMENTATION, FileType.UNKNOWN]:
                continue
            # Skip ignored directories
            if any(ignore in str(file_info.path) for ignore in [
                "node_modules", "__pycache__", ".git", ".pytest_cache", 
                ".hypothesis", "dist", "build", ".venv", "venv"
            ]):
                continue
            files_to_move.append(file_info)
        
        print(f"Files to reorganize: {len(files_to_move)}")
        
        # Create target structure
        target_structure = create_target_structure(files_to_move, project_root)
        
        print(f"Target mappings created: {len(target_structure)}")
        
        # Show what will be moved
        print("\nPlanned file moves:")
        for old_path, new_path in target_structure.items():
            rel_old = old_path.relative_to(project_root)
            rel_new = new_path.relative_to(project_root)
            print(f"  {rel_old} -> {rel_new}")
        
        # Create migration plan
        print("\nCreating migration plan...")
        migration_plan = executor.create_migration_plan(
            files_to_move, 
            target_structure,
            "Reorganize fitness app into frontend/backend structure"
        )
        
        print(f"Migration plan created with {len(migration_plan.operations)} operations")
        
        # Execute migration
        print("\nExecuting migration...")
        result = executor.execute_migration(migration_plan)
        
        # Report results
        print(f"\nMigration completed!")
        print(f"Status: {result.status.value}")
        print(f"Completed operations: {result.completed_operations}/{result.total_operations}")
        print(f"Execution time: {result.execution_time_seconds:.2f} seconds")
        
        if result.failed_operations:
            print(f"Failed operations: {len(result.failed_operations)}")
            for failed in result.failed_operations:
                print(f"  - {failed}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Verify structure
        print("\nVerifying new structure...")
        frontend_dir = project_root / "frontend"
        backend_dir = project_root / "backend"
        
        if frontend_dir.exists():
            print(f"✓ Frontend directory created")
            frontend_files = list(frontend_dir.rglob("*"))
            print(f"  - {len([f for f in frontend_files if f.is_file()])} files moved to frontend")
        
        if backend_dir.exists():
            print(f"✓ Backend directory exists")
            backend_files = list(backend_dir.rglob("*"))
            print(f"  - {len([f for f in backend_files if f.is_file()])} files in backend")
        
        print("\nFile reorganization completed successfully!")
        
        # Check if package.json and requirements.txt are in correct locations
        frontend_package = frontend_dir / "package.json"
        backend_requirements = backend_dir / "requirements.txt"
        
        if frontend_package.exists():
            print("✓ package.json moved to frontend directory")
        else:
            print("⚠ package.json not found in frontend directory")
            
        if backend_requirements.exists():
            print("✓ requirements.txt moved to backend directory")
        else:
            print("⚠ requirements.txt not found in backend directory")
        
    except Exception as e:
        print(f"Error during reorganization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup executor resources
        executor.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())