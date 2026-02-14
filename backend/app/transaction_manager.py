"""
Transaction Management System for ACID Compliance
"""
import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional, Any, Dict, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import uuid

logger = logging.getLogger(__name__)

class TransactionState(Enum):
    """Transaction states"""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

class IsolationLevel(Enum):
    """SQL isolation levels"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"

@dataclass
class TransactionInfo:
    """Information about a transaction"""
    transaction_id: str
    session_id: str
    thread_id: int
    start_time: float
    state: TransactionState = TransactionState.ACTIVE
    isolation_level: Optional[IsolationLevel] = None
    operations: List[str] = field(default_factory=list)
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get transaction duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

class TransactionManager:
    """
    ACID-compliant transaction manager with concurrent access handling
    """
    
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory
        self._active_transactions: Dict[str, TransactionInfo] = {}
        self._lock = threading.RLock()
        self._transaction_timeout = 300  # 5 minutes default timeout
    
    def set_transaction_timeout(self, timeout_seconds: int):
        """Set transaction timeout in seconds"""
        self._transaction_timeout = timeout_seconds
    
    @contextmanager
    def transaction(
        self, 
        isolation_level: Optional[IsolationLevel] = None,
        readonly: bool = False,
        timeout: Optional[int] = None
    ):
        """
        Context manager for ACID-compliant transactions
        
        Args:
            isolation_level: SQL isolation level
            readonly: Whether this is a read-only transaction
            timeout: Transaction timeout in seconds
        """
        transaction_id = str(uuid.uuid4())
        session = self.session_factory()
        transaction_info = None
        
        try:
            # Register transaction
            transaction_info = self._register_transaction(
                transaction_id, session, isolation_level
            )
            
            # Set isolation level if specified
            if isolation_level:
                session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level.value}"))
            
            # Set read-only mode if specified
            if readonly:
                session.execute(text("SET TRANSACTION READ ONLY"))
            
            # Set transaction timeout
            actual_timeout = timeout or self._transaction_timeout
            if actual_timeout:
                session.execute(text(f"SET statement_timeout = {actual_timeout * 1000}"))  # PostgreSQL uses milliseconds
            
            logger.debug(f"Started transaction {transaction_id}")
            yield session
            
            # Commit transaction
            session.commit()
            self._mark_transaction_committed(transaction_id)
            logger.debug(f"Committed transaction {transaction_id}")
            
        except Exception as e:
            # Rollback transaction
            try:
                session.rollback()
                self._mark_transaction_rolled_back(transaction_id, str(e))
                logger.warning(f"Rolled back transaction {transaction_id}: {e}")
            except Exception as rollback_error:
                self._mark_transaction_failed(transaction_id, f"Rollback failed: {rollback_error}")
                logger.error(f"Failed to rollback transaction {transaction_id}: {rollback_error}")
            
            raise
        
        finally:
            # Clean up
            session.close()
            if transaction_info:
                self._unregister_transaction(transaction_id)
    
    @contextmanager
    def savepoint(self, session: Session, name: Optional[str] = None):
        """
        Context manager for savepoints (nested transactions)
        
        Args:
            session: Active database session
            name: Optional savepoint name
        """
        savepoint_name = name or f"sp_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create savepoint
            session.execute(text(f"SAVEPOINT {savepoint_name}"))
            logger.debug(f"Created savepoint {savepoint_name}")
            
            yield savepoint_name
            
            # Release savepoint (implicit commit)
            session.execute(text(f"RELEASE SAVEPOINT {savepoint_name}"))
            logger.debug(f"Released savepoint {savepoint_name}")
            
        except Exception as e:
            # Rollback to savepoint
            try:
                session.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
                logger.warning(f"Rolled back to savepoint {savepoint_name}: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback to savepoint {savepoint_name}: {rollback_error}")
            
            raise
    
    def execute_in_transaction(
        self, 
        operation: Callable[[Session], Any],
        isolation_level: Optional[IsolationLevel] = None,
        readonly: bool = False,
        max_retries: int = 3
    ) -> Any:
        """
        Execute an operation within a transaction with retry logic
        
        Args:
            operation: Function that takes a session and returns a result
            isolation_level: SQL isolation level
            readonly: Whether this is a read-only transaction
            max_retries: Maximum number of retry attempts
        
        Returns:
            Result of the operation
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                with self.transaction(isolation_level=isolation_level, readonly=readonly) as session:
                    return operation(session)
            
            except SQLAlchemyError as e:
                last_exception = e
                if attempt < max_retries and self._is_retryable_error(e):
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Transaction failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    break
        
        # All retries exhausted
        raise last_exception
    
    def get_active_transactions(self) -> List[TransactionInfo]:
        """Get list of currently active transactions"""
        with self._lock:
            return list(self._active_transactions.values())
    
    def get_transaction_info(self, transaction_id: str) -> Optional[TransactionInfo]:
        """Get information about a specific transaction"""
        with self._lock:
            return self._active_transactions.get(transaction_id)
    
    def cleanup_stale_transactions(self, max_age_seconds: int = 3600):
        """Clean up transactions that have been active too long"""
        current_time = time.time()
        stale_transactions = []
        
        with self._lock:
            for tx_id, tx_info in self._active_transactions.items():
                if current_time - tx_info.start_time > max_age_seconds:
                    stale_transactions.append(tx_id)
        
        for tx_id in stale_transactions:
            logger.warning(f"Cleaning up stale transaction {tx_id}")
            self._unregister_transaction(tx_id)
    
    def _register_transaction(
        self, 
        transaction_id: str, 
        session: Session, 
        isolation_level: Optional[IsolationLevel]
    ) -> TransactionInfo:
        """Register a new transaction"""
        transaction_info = TransactionInfo(
            transaction_id=transaction_id,
            session_id=str(id(session)),
            thread_id=threading.get_ident(),
            start_time=time.time(),
            isolation_level=isolation_level
        )
        
        with self._lock:
            self._active_transactions[transaction_id] = transaction_info
        
        return transaction_info
    
    def _mark_transaction_committed(self, transaction_id: str):
        """Mark transaction as committed"""
        with self._lock:
            if transaction_id in self._active_transactions:
                tx_info = self._active_transactions[transaction_id]
                tx_info.state = TransactionState.COMMITTED
                tx_info.end_time = time.time()
    
    def _mark_transaction_rolled_back(self, transaction_id: str, error_message: str):
        """Mark transaction as rolled back"""
        with self._lock:
            if transaction_id in self._active_transactions:
                tx_info = self._active_transactions[transaction_id]
                tx_info.state = TransactionState.ROLLED_BACK
                tx_info.end_time = time.time()
                tx_info.error_message = error_message
    
    def _mark_transaction_failed(self, transaction_id: str, error_message: str):
        """Mark transaction as failed"""
        with self._lock:
            if transaction_id in self._active_transactions:
                tx_info = self._active_transactions[transaction_id]
                tx_info.state = TransactionState.FAILED
                tx_info.end_time = time.time()
                tx_info.error_message = error_message
    
    def _unregister_transaction(self, transaction_id: str):
        """Unregister a transaction"""
        with self._lock:
            self._active_transactions.pop(transaction_id, None)
    
    def _is_retryable_error(self, error: SQLAlchemyError) -> bool:
        """Determine if an error is retryable"""
        error_str = str(error).lower()
        
        # Common retryable errors
        retryable_patterns = [
            'deadlock detected',
            'could not serialize access',
            'connection reset',
            'connection lost',
            'server closed the connection',
            'timeout expired'
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)

class ConcurrentAccessManager:
    """
    Manager for handling concurrent access to shared resources
    """
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
        self._locks: Dict[str, threading.RLock] = {}
        self._locks_lock = threading.RLock()
    
    @contextmanager
    def resource_lock(self, resource_id: str):
        """
        Context manager for locking access to a specific resource
        
        Args:
            resource_id: Unique identifier for the resource
        """
        # Get or create lock for this resource
        with self._locks_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = threading.RLock()
            resource_lock = self._locks[resource_id]
        
        # Acquire the resource lock
        with resource_lock:
            logger.debug(f"Acquired lock for resource {resource_id}")
            try:
                yield
            finally:
                logger.debug(f"Released lock for resource {resource_id}")
    
    def execute_with_lock(
        self, 
        resource_id: str, 
        operation: Callable[[Session], Any],
        isolation_level: Optional[IsolationLevel] = None
    ) -> Any:
        """
        Execute an operation with both resource locking and transaction management
        
        Args:
            resource_id: Unique identifier for the resource to lock
            operation: Function that takes a session and returns a result
            isolation_level: SQL isolation level
        
        Returns:
            Result of the operation
        """
        with self.resource_lock(resource_id):
            return self.transaction_manager.execute_in_transaction(
                operation, 
                isolation_level=isolation_level
            )

# Global transaction manager instance
_transaction_manager: Optional[TransactionManager] = None

def get_transaction_manager() -> TransactionManager:
    """Get the global transaction manager instance"""
    global _transaction_manager
    if _transaction_manager is None:
        from .neon_config import get_connection_manager
        connection_manager = get_connection_manager()
        _transaction_manager = TransactionManager(connection_manager.get_session)
    return _transaction_manager

def get_concurrent_access_manager() -> ConcurrentAccessManager:
    """Get a concurrent access manager instance"""
    return ConcurrentAccessManager(get_transaction_manager())