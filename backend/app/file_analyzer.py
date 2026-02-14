"""
FileAnalyzer class for file type identification and dependency analysis.
Validates Requirements 1.1, 1.2, 1.5
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FileType(Enum):
    """File type classifications for organization"""
    FRONTEND_REACT = "frontend_react"
    FRONTEND_TYPESCRIPT = "frontend_typescript"
    FRONTEND_JAVASCRIPT = "frontend_javascript"
    FRONTEND_CSS = "frontend_css"
    FRONTEND_HTML = "frontend_html"
    BACKEND_PYTHON = "backend_python"
    CONFIG_FRONTEND = "config_frontend"
    CONFIG_BACKEND = "config_backend"
    CONFIG_SHARED = "config_shared"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """Information about a file including its type and dependencies"""
    path: Path
    file_type: FileType
    imports: List[str]
    exports: List[str]
    dependencies: Set[str]
    size_bytes: int
    is_config: bool = False
    is_test: bool = False


class FileAnalyzer:
    """Analyzes files to determine their type and extract dependency information"""
    
    # File extension mappings
    FRONTEND_EXTENSIONS = {
        '.tsx': FileType.FRONTEND_REACT,
        '.jsx': FileType.FRONTEND_REACT,
        '.ts': FileType.FRONTEND_TYPESCRIPT,
        '.js': FileType.FRONTEND_JAVASCRIPT,
        '.css': FileType.FRONTEND_CSS,
        '.scss': FileType.FRONTEND_CSS,
        '.html': FileType.FRONTEND_HTML,
    }
    
    BACKEND_EXTENSIONS = {
        '.py': FileType.BACKEND_PYTHON,
    }
    
    # Configuration file patterns
    FRONTEND_CONFIG_PATTERNS = [
        'package.json', 'tsconfig.json', 'vite.config.*', 'webpack.config.*',
        '.eslintrc.*', '.prettierrc.*', 'tailwind.config.*'
    ]
    
    BACKEND_CONFIG_PATTERNS = [
        'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile',
        '.env', '.env.*', 'alembic.ini'
    ]
    
    SHARED_CONFIG_PATTERNS = [
        '.gitignore', 'README.md', 'LICENSE', 'docker-compose.*', 'Dockerfile'
    ]
    
    # Import/export patterns
    IMPORT_PATTERNS = {
        'python': [
            r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
        ],
        'typescript': [
            r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*import\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*export\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
        ],
        'javascript': [
            r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*import\s+[\'"]([^\'"]+)[\'"]',
            r'^\s*const\s+.*?\s*=\s*require\([\'"]([^\'"]+)[\'"]\)',
            r'^\s*export\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
        ]
    }
    
    EXPORT_PATTERNS = {
        'python': [
            r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
        ],
        'typescript': [
            r'^\s*export\s+(?:default\s+)?(?:function|class|const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^\s*export\s+\{\s*([^}]+)\s*\}',
        ],
        'javascript': [
            r'^\s*export\s+(?:default\s+)?(?:function|class|const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^\s*module\.exports\s*=',
            r'^\s*exports\.([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
    }

    def __init__(self, project_root: Path):
        """Initialize FileAnalyzer with project root directory"""
        self.project_root = Path(project_root)
        self._file_cache: Dict[Path, FileInfo] = {}

    def analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single file and return FileInfo"""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        # Get file stats
        try:
            stat = file_path.stat()
            size_bytes = stat.st_size
        except (OSError, FileNotFoundError):
            size_bytes = 0
        
        # Determine file type
        file_type = self._classify_file_type(file_path)
        
        # Check if it's a test file
        is_test = self._is_test_file(file_path)
        
        # Check if it's a config file
        is_config = self._is_config_file(file_path)
        
        # Extract imports and exports
        imports, exports = self._extract_dependencies(file_path, file_type)
        
        # Build dependency set
        dependencies = set(imports)
        
        file_info = FileInfo(
            path=file_path,
            file_type=file_type,
            imports=imports,
            exports=exports,
            dependencies=dependencies,
            size_bytes=size_bytes,
            is_config=is_config,
            is_test=is_test
        )
        
        self._file_cache[file_path] = file_info
        return file_info

    def analyze_directory(self, directory: Path) -> List[FileInfo]:
        """Analyze all files in a directory recursively"""
        file_infos = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    file_info = self.analyze_file(file_path)
                    file_infos.append(file_info)
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Warning: Could not analyze {file_path}: {e}")
        
        return file_infos

    def _classify_file_type(self, file_path: Path) -> FileType:
        """Classify file type based on extension and content"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Check configuration files first
        if self._is_config_file(file_path):
            if any(pattern in name for pattern in ['package.json', 'tsconfig', 'vite', 'webpack']):
                return FileType.CONFIG_FRONTEND
            elif any(pattern in name for pattern in ['requirements.txt', 'setup.py', '.env']):
                return FileType.CONFIG_BACKEND
            else:
                return FileType.CONFIG_SHARED
        
        # Check documentation
        if suffix in ['.md', '.rst', '.txt'] and name in ['readme.md', 'license', 'changelog.md']:
            return FileType.DOCUMENTATION
        
        # Check frontend files
        if suffix in self.FRONTEND_EXTENSIONS:
            return self.FRONTEND_EXTENSIONS[suffix]
        
        # Check backend files
        if suffix in self.BACKEND_EXTENSIONS:
            return self.BACKEND_EXTENSIONS[suffix]
        
        return FileType.UNKNOWN

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file"""
        name = file_path.name.lower()
        
        # Check exact matches and patterns
        all_patterns = (
            self.FRONTEND_CONFIG_PATTERNS + 
            self.BACKEND_CONFIG_PATTERNS + 
            self.SHARED_CONFIG_PATTERNS
        )
        
        for pattern in all_patterns:
            if '*' in pattern:
                # Handle wildcard patterns
                pattern_regex = pattern.replace('*', '.*')
                if re.match(pattern_regex, name):
                    return True
            else:
                # Exact match
                if name == pattern.lower():
                    return True
        
        return False

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file"""
        name = file_path.name.lower()
        path_str = str(file_path).lower()
        
        test_indicators = [
            '.test.', '.spec.', '_test.', '_spec.',
            '/test/', '/tests/', '\\test\\', '\\tests\\',
            'test_', 'spec_'
        ]
        
        return any(indicator in name or indicator in path_str for indicator in test_indicators)

    def _extract_dependencies(self, file_path: Path, file_type: FileType) -> Tuple[List[str], List[str]]:
        """Extract import and export statements from file"""
        imports = []
        exports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return imports, exports
        
        # Determine language for pattern matching
        language = self._get_language_from_file_type(file_type)
        if not language:
            return imports, exports
        
        # Extract imports
        if language in self.IMPORT_PATTERNS:
            for pattern in self.IMPORT_PATTERNS[language]:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)
        
        # Extract exports
        if language in self.EXPORT_PATTERNS:
            for pattern in self.EXPORT_PATTERNS[language]:
                matches = re.findall(pattern, content, re.MULTILINE)
                exports.extend(matches)
        
        return imports, exports

    def _get_language_from_file_type(self, file_type: FileType) -> Optional[str]:
        """Map file type to language for pattern matching"""
        mapping = {
            FileType.BACKEND_PYTHON: 'python',
            FileType.FRONTEND_REACT: 'typescript',
            FileType.FRONTEND_TYPESCRIPT: 'typescript',
            FileType.FRONTEND_JAVASCRIPT: 'javascript',
        }
        return mapping.get(file_type)

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during analysis"""
        ignore_patterns = [
            'node_modules', '__pycache__', '.git', '.pytest_cache',
            '.hypothesis', 'dist', 'build', '.venv', 'venv',
            '.DS_Store', 'Thumbs.db'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)

    def get_frontend_files(self, file_infos: List[FileInfo]) -> List[FileInfo]:
        """Filter files that should go to frontend directory"""
        frontend_types = {
            FileType.FRONTEND_REACT,
            FileType.FRONTEND_TYPESCRIPT,
            FileType.FRONTEND_JAVASCRIPT,
            FileType.FRONTEND_CSS,
            FileType.FRONTEND_HTML,
            FileType.CONFIG_FRONTEND
        }
        return [f for f in file_infos if f.file_type in frontend_types]

    def get_backend_files(self, file_infos: List[FileInfo]) -> List[FileInfo]:
        """Filter files that should go to backend directory"""
        backend_types = {
            FileType.BACKEND_PYTHON,
            FileType.CONFIG_BACKEND
        }
        return [f for f in file_infos if f.file_type in backend_types]

    def get_shared_files(self, file_infos: List[FileInfo]) -> List[FileInfo]:
        """Filter files that should remain in root or shared directory"""
        shared_types = {
            FileType.CONFIG_SHARED,
            FileType.DOCUMENTATION
        }
        return [f for f in file_infos if f.file_type in shared_types]