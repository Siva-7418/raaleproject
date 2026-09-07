import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.database import init_db, get_connection
from scripts.seed_data import generate_seed_data
from backend.app.services.rules_engine import RulesEngine
from backend.app.services.review_service import ReviewService

@pytest.fixture
def temp_db():
    # Create temporary database file for test isolation
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_file = Path(path)

    generate_seed_data(db_file=db_file)

    yield db_file

    if db_file.exists():
        os.remove(db_file)

@pytest.fixture
def db_conn(temp_db):
    conn = get_connection(db_file=temp_db)
    yield conn
    conn.close()

@pytest.fixture
def rules_engine(temp_db):
    return RulesEngine()

@pytest.fixture
def review_service(rules_engine):
    return ReviewService(rules_engine=rules_engine)
