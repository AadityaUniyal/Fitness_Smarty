"""
PathResolver class for updating import paths after file reorganization.
Validates Requirements 1.3
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from .file_analyzer import FileInfo, FileType


@dataclass
class PathMapping:
    """Mapping from old path to new path"""
    old_path: Path
    new_path: Path
    file_type: FileType


@dataclass
class ImportUpdate:
    """Information about an import statement that needs updating"""
    file_path: Path
    line_number: int
    old_import: str
    new_import: str
    import_type: str  # 'relative' or 'absolute'


class PathResolver:
    """Resolves and updates import paths after file reorganization"""
    
    def __init__(self, project_root: Path):
        """Initialize PathResolver with project root directory"""
        self.project_root = Path(project_root)
        self.path_mappings: Dict[Path, PathMapping] = {}
        self.import_updates: List[ImportUpdate] = []

    def add_path_mapping(self, old_path: Path, new_path: Path, file_type: FileType):
        """Add a path mapping for file reorganization"""
        mapping = PathMapping(old_path, new_path, file_type)
        self.path_mappings[old_path] = mapping

    def generate_import_updates(self, file_infos: List[FileInfo]) -> List[ImportUpdate]:
        """Generate list of import updates needed for all files"""
        self.import_updates.clear()
        
        for file_info in file_infos:
            updates = self._analyze_file_imports(file_info)
            self.import_updates.extend(updates)
        
        return self.import_updates

    def _analyze_file_imports(self, file_info: FileInfo) -> List[ImportUpdate]:
        """Analyze imports in a single file and generate updates"""
        updates = []
        
        try:
            with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            return updates
        
        # Get the new location of this file
        new_file_path = self._get_new_path(file_info.path)
        if not new_file_path:
            return updates
        
        # Analyze each line for import statements
        for line_num, line in enumerate(lines, 1):
            import_updates = self._analyze_import_line(
                line, line_num, file_info.path, new_file_path, file_info.file_type
            )
            updates.extend(import_updates)
        
        return updates

    def _analyze_import_line(
        self, 
        line: str, 
        line_num: int, 
        current_file: Path, 
        new_file_path: Path, 
        file_type: FileType
    ) -> List[ImportUpdate]:
        """Analyze a single line for import statements that need updating"""
        updates = []
        
        # Get language-specific import patterns
        language = self._get_language_from_file_type(file_type)
        if not language:
            return updates
        
        # Python imports
        if language == 'python':
            updates.extend(self._analyze_python_imports(line, line_num, current_file, new_file_path))
        
        # TypeScript/JavaScript imports
        elif language in ['typescript', 'javascript']:
            updates.extend(self._analyze_js_imports(line, line_num, current_file, new_file_path))
        
        return updates

    def _analyze_python_imports(
        self, 
        line: str, 
        line_num: int, 
        current_file: Path, 
        new_file_path: Path
    ) -> List[ImportUpdate]:
        """Analyze Python import statements"""
        updates = []
        
        # Pattern for "import module" statements
        import_match = re.match(r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', line)
        if import_match:
            module_name = import_match.group(1)
            new_import = self._resolve_python_import(module_name, current_file, new_file_path)
            if new_import != module_name:
                updates.append(ImportUpdate(
                    file_path=current_file,
                    line_number=line_num,
                    old_import=module_name,
                    new_import=new_import,
                    import_type='absolute'
                ))
        
        # Pattern for "from module import ..." statements
        from_match = re.match(r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import', line)
        if from_match:
            module_name = from_match.group(1)
            new_import = self._resolve_python_import(module_name, current_file, new_file_path)
            if new_import != module_name:
                updates.append(ImportUpdate(
                    file_path=current_file,
                    line_number=line_num,
                    old_import=module_name,
                    new_import=new_import,
                    import_type='absolute'
                ))
        
        return updates

    def _analyze_js_imports(
        self, 
        line: str, 
        line_num: int, 
        current_file: Path, 
        new_file_path: Path
    ) -> List[ImportUpdate]:
        """Analyze JavaScript/TypeScript import statements"""
        updates = []
        
        # Pattern for import statements with from clause
        import_match = re.search(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', line)
        if import_match:
            import_path = import_match.group(1)
            new_import = self._resolve_js_import(import_path, current_file, new_file_path)
            if new_import != import_path:
                import_type = 'relative' if import_path.startswith('.') else 'absolute'
                updates.append(ImportUpdate(
                    file_path=current_file,
                    line_number=line_num,
                    old_import=import_path,
                    new_import=new_import,
                    import_type=import_type
                ))
        
        # Pattern for direct import statements
        direct_match = re.search(r'import\s+[\'"]([^\'"]+)[\'"]', line)
        if direct_match and not import_match:  # Avoid double-matching
            import_path = direct_match.group(1)
            new_import = self._resolve_js_import(import_path, current_file, new_file_path)
            if new_import != import_path:
                import_type = 'relative' if import_path.startswith('.') else 'absolute'
                updates.append(ImportUpdate(
                    file_path=current_file,
                    line_number=line_num,
                    old_import=import_path,
                    new_import=new_import,
                    import_type=import_type
                ))
        
        return updates

    def _resolve_python_import(self, module_name: str, current_file: Path, new_file_path: Path) -> str:
        """Resolve Python import path after reorganization"""
        # Handle relative imports (starting with .)
        if module_name.startswith('.'):
            return module_name  # Relative imports should still work
        
        # Check if this is a local module that's being moved
        potential_file = self.project_root / f"{module_name.replace('.', '/')}.py"
        if potential_file in self.path_mappings:
            # Calculate new relative path
            new_target = self.path_mappings[potential_file].new_path
            return self._calculate_python_relative_import(new_file_path, new_target)
        
        # Check for __init__.py files
        potential_init = self.project_root / f"{module_name.replace('.', '/')}/__init__.py"
        if potential_init in self.path_mappings:
            new_target = self.path_mappings[potential_init].new_path.parent
            return self._calculate_python_relative_import(new_file_path, new_target / "__init__.py")
        
        return module_name  # No change needed

    def _resolve_js_import(self, import_path: str, current_file: Path, new_file_path: Path) -> str:
        """Resolve JavaScript/TypeScript import path after reorganization"""
        # Handle absolute imports (node_modules, etc.)
        if not import_path.startswith('.'):
            return import_path  # No change needed for absolute imports
        
        # Resolve relative import
        current_dir = current_file.parent
        target_path = (current_dir / import_path).resolve()
        
        # Try different extensions if the exact path doesn't exist
        possible_extensions = ['.ts', '.tsx', '.js', '.jsx']
        if not target_path.exists():
            for ext in possible_extensions:
                if (target_path.parent / f"{target_path.name}{ext}").exists():
                    target_path = target_path.parent / f"{target_path.name}{ext}"
                    break
        
        # Check if target file is being moved
        if target_path in self.path_mappings:
            new_target = self.path_mappings[target_path].new_path
            return self._calculate_js_relative_import(new_file_path, new_target)
        
        return import_path  # No change needed

    def _calculate_python_relative_import(self, from_file: Path, to_file: Path) -> str:
        """Calculate relative Python import path"""
        try:
            # Get relative path
            rel_path = to_file.relative_to(from_file.parent)
            # Convert to module notation
            module_path = str(rel_path.with_suffix('')).replace('/', '.').replace('\\', '.')
            return f".{module_path}"
        except ValueError:
            # Files are not in relative paths, use absolute import
            try:
                rel_to_root = to_file.relative_to(self.project_root)
                return str(rel_to_root.with_suffix('')).replace('/', '.').replace('\\', '.')
            except ValueError:
                return to_file.stem

    def _calculate_js_relative_import(self, from_file: Path, to_file: Path) -> str:
        """Calculate relative JavaScript/TypeScript import path"""
        try:
            from_dir = from_file.parent
            rel_path = to_file.relative_to(from_dir)
            
            # Convert to forward slashes and remove extension
            import_path = str(rel_path).replace('\\', '/')
            if import_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                import_path = import_path.rsplit('.', 1)[0]
            
            # Ensure it starts with ./
            if not import_path.startswith('./'):
                import_path = f"./{import_path}"
            
            return import_path
        except ValueError:
            # Files are not in relative paths, calculate with ../
            try:
                common_parent = Path(*os.path.commonpath([from_file.parent, to_file.parent]).split(os.sep))
                from_rel = from_file.parent.relative_to(common_parent)
                to_rel = to_file.relative_to(common_parent)
                
                # Calculate how many levels up we need to go
                levels_up = len(from_rel.parts)
                up_path = '../' * levels_up
                
                # Add the path to target
                target_path = str(to_rel).replace('\\', '/')
                if target_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    target_path = target_path.rsplit('.', 1)[0]
                
                return f"{up_path}{target_path}"
            except (ValueError, OSError):
                return str(to_file.name).rsplit('.', 1)[0]

    def _get_new_path(self, old_path: Path) -> Optional[Path]:
        """Get the new path for a file after reorganization"""
        if old_path in self.path_mappings:
            return self.path_mappings[old_path].new_path
        return None

    def _get_language_from_file_type(self, file_type: FileType) -> Optional[str]:
        """Map file type to language for import analysis"""
        mapping = {
            FileType.BACKEND_PYTHON: 'python',
            FileType.FRONTEND_REACT: 'typescript',
            FileType.FRONTEND_TYPESCRIPT: 'typescript',
            FileType.FRONTEND_JAVASCRIPT: 'javascript',
        }
        return mapping.get(file_type)

    def apply_import_updates(self, dry_run: bool = True) -> Dict[Path, List[str]]:
        """Apply import updates to files"""
        results = {}
        
        # Group updates by file
        updates_by_file = {}
        for update in self.import_updates:
            if update.file_path not in updates_by_file:
                updates_by_file[update.file_path] = []
            updates_by_file[update.file_path].append(update)
        
        # Apply updates to each file
        for file_path, file_updates in updates_by_file.items():
            try:
                updated_lines = self._apply_file_updates(file_path, file_updates, dry_run)
                results[file_path] = updated_lines
            except Exception as e:
                results[file_path] = [f"Error updating {file_path}: {e}"]
        
        return results

    def _apply_file_updates(self, file_path: Path, updates: List[ImportUpdate], dry_run: bool) -> List[str]:
        """Apply updates to a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError) as e:
            return [f"Could not read file: {e}"]
        
        # Sort updates by line number in reverse order to avoid line number shifts
        updates.sort(key=lambda u: u.line_number, reverse=True)
        
        changes = []
        for update in updates:
            if 1 <= update.line_number <= len(lines):
                old_line = lines[update.line_number - 1]
                new_line = old_line.replace(update.old_import, update.new_import)
                
                if old_line != new_line:
                    lines[update.line_number - 1] = new_line
                    changes.append(f"Line {update.line_number}: {update.old_import} -> {update.new_import}")
        
        # Write back to file if not dry run
        if not dry_run and changes:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            except OSError as e:
                changes.append(f"Error writing file: {e}")
        
        return changes if changes else ["No changes needed"]