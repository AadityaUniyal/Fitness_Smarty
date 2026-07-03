import pytest
from sqlalchemy import create_model_from_project # not needed, we can use sqlite in-memory
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from app.idempotency import IdempotencyManager
from app.models import EnhancedUser

Base = declarative_base()

class TempUser(Base):
    __tablename__ = "temp_users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(Integer, default=1, nullable=False)
    __mapper_args__ = {
        "version_id_col": version
    }


def test_optimistic_locking_concurrency():
    # Setup in-memory sqlite DB to test optimistic concurrency
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    db1 = Session()
    db2 = Session()
    
    # Create a user
    user = TempUser(id=1, name="Alice")
    db1.add(user)
    db1.commit()
    
    # Read in both sessions
    u1 = db1.query(TempUser).filter_by(id=1).first()
    u2 = db2.query(TempUser).filter_by(id=1).first()
    
    assert u1.version == 1
    assert u2.version == 1
    
    # Update in session 1
    u1.name = "Alice Updated"
    db1.commit()
    assert u1.version == 2
    
    # Update in session 2 (stale data since it still has version=1 in memory)
    u2.name = "Alice Stale Update"
    
    with pytest.raises(StaleDataError):
        db2.commit()


def test_idempotency_keys():
    key = "uniq-uuid-1234"
    resp = {"status": "success", "id": 100}
    
    # First request: not cached
    assert IdempotencyManager.get_cached_response(key) is None
    
    # Save the response
    IdempotencyManager.save_response(key, resp, ttl_seconds=10)
    
    # Second request: returns cached response
    cached = IdempotencyManager.get_cached_response(key)
    assert cached == resp
