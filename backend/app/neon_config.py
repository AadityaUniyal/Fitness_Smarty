"""
Neon PostgreSQL Configuration and Connection Management
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class NeonConfig:
    """Configuration class for Neon PostgreSQL connections"""
    
    # Connection parameters
    host: str
    port: int
    database: str
    username: str
    password: str
    
    # SSL configuration
    ssl_mode: str = "require"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    
    # Connection pooling parameters
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    
    # Connection retry parameters
    connect_timeout: int = 10
    command_timeout: int = 60
    
    # Application parameters
    application_name: str = "fitness-smarty-ai"
    
    @classmethod
    def from_database_url(cls, database_url: str) -> 'NeonConfig':
        """Create NeonConfig from DATABASE_URL string"""
        parsed = urlparse(database_url)
        
        if not parsed.hostname:
            raise ValueError("Invalid database URL: missing hostname")
        
        return cls(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') if parsed.path else 'postgres',
            username=parsed.username or '',
            password=parsed.password or '',
            ssl_mode="require" if "sslmode=require" in database_url else "prefer"
        )
    
    @classmethod
    def from_environment(cls) -> 'NeonConfig':
        """Create NeonConfig from environment variables"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        config = cls.from_database_url(database_url)
        
        # Override with specific environment variables if present
        config.pool_size = int(os.getenv('DB_POOL_SIZE', config.pool_size))
        config.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', config.max_overflow))
        config.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', config.pool_timeout))
        config.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', config.pool_recycle))
        config.connect_timeout = int(os.getenv('DB_CONNECT_TIMEOUT', config.connect_timeout))
        config.command_timeout = int(os.getenv('DB_COMMAND_TIMEOUT', config.command_timeout))
        config.application_name = os.getenv('DB_APPLICATION_NAME', config.application_name)
        
        return config
    
    def to_sqlalchemy_url(self) -> str:
        """Convert to SQLAlchemy connection URL"""
        url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # Add SSL parameters
        params = []
        if self.ssl_mode:
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            params.append(f"sslrootcert={self.ssl_ca}")
        
        # Add application name
        params.append(f"application_name={self.application_name}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration parameters"""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'connect_args': {
                'connect_timeout': self.connect_timeout,
                'application_name': self.application_name
                # Note: command_timeout is not a valid psycopg2 parameter
            },
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',  # SQL logging
            'echo_pool': os.getenv('DB_ECHO_POOL', 'false').lower() == 'true',  # Pool logging
        }
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        if not self.host:
            raise ValueError("Database host is required")
        if not self.database:
            raise ValueError("Database name is required")
        if not self.username:
            raise ValueError("Database username is required")
        if not self.password:
            raise ValueError("Database password is required")
        
        if self.pool_size < 1:
            raise ValueError("Pool size must be at least 1")
        if self.max_overflow < 0:
            raise ValueError("Max overflow must be non-negative")
        if self.pool_timeout < 1:
            raise ValueError("Pool timeout must be at least 1 second")
        
        return True
    
    def __repr__(self) -> str:
        """String representation (without password)"""
        return (f"NeonConfig(host='{self.host}', port={self.port}, "
                f"database='{self.database}', username='{self.username}', "
                f"pool_size={self.pool_size}, ssl_mode='{self.ssl_mode}')")

class ConnectionManager:
    """Enhanced database connection manager for Neon PostgreSQL"""
    
    def __init__(self, config: NeonConfig):
        self.config = config
        self.config.validate()
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create SQLAlchemy engine"""
        if self._engine is None:
            from sqlalchemy import create_engine
            
            url = self.config.to_sqlalchemy_url()
            engine_kwargs = self.config.get_engine_kwargs()
            
            logger.info(f"Creating database engine for {self.config.host}:{self.config.port}/{self.config.database}")
            self._engine = create_engine(url, **engine_kwargs)
        
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            from sqlalchemy.orm import sessionmaker
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        
        return self._session_factory
    
    def get_session(self):
        """Get a new database session"""
        return self.session_factory()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                # Get PostgreSQL version
                version_result = connection.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                # Get current database and user
                info_result = connection.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
                db_info = info_result.fetchone()
                
                return {
                    'postgresql_version': version,
                    'database': db_info[0],
                    'user': db_info[1],
                    'server_address': db_info[2],
                    'server_port': db_info[3],
                    'pool_size': self.config.pool_size,
                    'max_overflow': self.config.max_overflow,
                    'ssl_mode': self.config.ssl_mode
                }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close all connections and dispose of the engine"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")

# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        config = NeonConfig.from_environment()
        _connection_manager = ConnectionManager(config)
    return _connection_manager

def get_database_session():
    """Get a database session (for dependency injection)"""
    manager = get_connection_manager()
    session = manager.get_session()
    try:
        yield session
    finally:
        session.close()