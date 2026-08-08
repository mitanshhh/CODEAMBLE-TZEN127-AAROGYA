import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.models.health_centre import HealthCentre

TEST_PASSWORD_HASH = get_password_hash("testpassword")

# Use SQLite in-memory for fast, isolated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

@pytest.fixture
def test_hospital(db_session):
    hc = HealthCentre(name="Test Hospital", type="PHC", district="Test District", state="Test State", total_beds=10)
    db_session.add(hc)
    db_session.commit()
    db_session.refresh(hc)
    return hc

@pytest.fixture
def doc_user(db_session, test_hospital):
    user = User(
        username="testdoc",
        email="testdoc@example.com",
        hashed_password=TEST_PASSWORD_HASH,
        role=UserRole.DOCTOR,
        hospital_id=test_hospital.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session):
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=TEST_PASSWORD_HASH,
        role=UserRole.DISTRICT_ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def data_entry_user(db_session, test_hospital):
    user = User(
        username="testdata",
        email="testdata@example.com",
        hashed_password=TEST_PASSWORD_HASH,
        role=UserRole.DATA_ENTRY,
        hospital_id=test_hospital.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def doc_token(doc_user):
    return create_access_token(doc_user.id)

@pytest.fixture
def admin_token(admin_user):
    return create_access_token(admin_user.id)

@pytest.fixture
def data_entry_token(data_entry_user):
    return create_access_token(data_entry_user.id)
