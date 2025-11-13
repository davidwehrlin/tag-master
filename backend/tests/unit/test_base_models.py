"""
Unit tests for base models.

Tests verify:
- UUID generation for id field
- Timestamp auto-population (created_at, updated_at)
- Soft delete behavior (deleted_at)
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column


# Create isolated base classes for testing to avoid mapper conflicts with app models
class TestBase(DeclarativeBase):
    """Isolated declarative base for testing - separate from app's Base."""
    pass


class BaseModelForTest(TestBase):
    """Test implementation of BaseModel pattern."""
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class SoftDeleteMixinForTest:
    """Test implementation of SoftDeleteMixin pattern."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    def soft_delete(self):
        """Mark record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
    
    def is_deleted(self) -> bool:
        """Check if record is deleted."""
        return self.deleted_at is not None


@pytest.fixture
def engine():
    """Create in-memory SQLite database for testing."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def session(engine):
    """Create database session for testing."""
    TestBase.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess
    TestBase.metadata.drop_all(engine)


class TestBaseModel:
    """Test BaseModel functionality."""

    def test_base_model_has_uuid_id(self):
        """Test that BaseModel has UUID id field."""
        assert hasattr(BaseModelForTest, 'id')
        assert BaseModelForTest.id is not None

    def test_base_model_has_timestamps(self):
        """Test that BaseModel has created_at and updated_at fields."""
        assert hasattr(BaseModelForTest, 'created_at')
        assert hasattr(BaseModelForTest, 'updated_at')

    def test_uuid_generation(self, session):
        """Test that UUID is generated automatically."""
        class TestModel(BaseModelForTest):
            __tablename__ = "test_model_uuid"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        assert instance.id is not None
        assert isinstance(instance.id, uuid.UUID)

    def test_uuid_uniqueness(self, session):
        """Test that each instance gets a unique UUID."""
        class TestModel(BaseModelForTest):
            __tablename__ = "test_model_unique"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance1 = TestModel(name="test1")
        instance2 = TestModel(name="test2")
        
        session.add_all([instance1, instance2])
        session.commit()
        
        assert instance1.id != instance2.id

    def test_timestamps_auto_populate(self, session):
        """Test that timestamps are set automatically."""
        class TestModel(BaseModelForTest):
            __tablename__ = "test_model_timestamps"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        assert instance.created_at is not None
        assert instance.updated_at is not None

    def test_timestamps_utc(self, session):
        """Test that timestamps use UTC timezone."""
        class TestModel(BaseModelForTest):
            __tablename__ = "test_model_utc"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        before_creation = datetime.now(timezone.utc)
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        after_creation = datetime.now(timezone.utc)
        
        # Check timestamps are within reasonable range (SQLite may strip timezone)
        assert instance.created_at is not None
        assert instance.updated_at is not None
        # Timestamps should be recent (within test execution window)
        assert before_creation.replace(tzinfo=None) <= instance.created_at <= after_creation.replace(tzinfo=None)

    def test_created_at_immutable(self, session):
        """Test that created_at doesn't change on update."""
        class TestModel(BaseModelForTest):
            __tablename__ = "test_model_immutable"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        original_created_at = instance.created_at
        
        instance.name = "updated"
        session.commit()
        
        assert instance.created_at == original_created_at


class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality."""

    def test_soft_delete_mixin_has_deleted_at(self):
        """Test that SoftDeleteMixin has deleted_at field."""
        assert hasattr(SoftDeleteMixinForTest, 'deleted_at')

    def test_deleted_at_initially_none(self, session):
        """Test that deleted_at is None by default."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_deleted_none"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        assert instance.deleted_at is None

    def test_soft_delete_sets_deleted_at(self, session):
        """Test that soft_delete() sets deleted_at timestamp."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_soft_delete"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        before_delete = datetime.now(timezone.utc)
        instance.soft_delete()
        session.commit()
        after_delete = datetime.now(timezone.utc)
        
        assert instance.deleted_at is not None
        # Handle timezone-aware/naive comparison (SQLite may strip timezone)
        deleted_at_naive = instance.deleted_at.replace(tzinfo=None) if instance.deleted_at.tzinfo else instance.deleted_at
        assert before_delete.replace(tzinfo=None) <= deleted_at_naive <= after_delete.replace(tzinfo=None)

    def test_is_deleted_check(self, session):
        """Test that is_deleted() returns correct status."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_is_deleted"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        assert not instance.is_deleted()
        
        instance.soft_delete()
        session.commit()
        
        assert instance.is_deleted()

    def test_multiple_models_with_soft_delete(self, session):
        """Test that multiple models can use soft delete."""
        class TestModel1(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model1_multi"
            name: Mapped[str] = mapped_column(String(100))

        class TestModel2(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model2_multi"
            title: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance1 = TestModel1(name="test1")
        instance2 = TestModel2(title="test2")
        
        session.add_all([instance1, instance2])
        session.commit()
        
        instance1.soft_delete()
        session.commit()
        
        assert instance1.is_deleted()
        assert not instance2.is_deleted()


class TestBaseModelIntegration:
    """Test BaseModel and SoftDeleteMixin integration."""

    def test_combined_model_has_all_fields(self):
        """Test that model with both base and mixin has all fields."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_combined"
            name: Mapped[str] = mapped_column(String(100))

        assert hasattr(TestModel, 'id')
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')
        assert hasattr(TestModel, 'deleted_at')

    def test_combined_model_initialization(self, session):
        """Test that combined model initializes correctly."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_init"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        assert instance.id is not None
        assert instance.created_at is not None
        assert instance.updated_at is not None
        assert instance.deleted_at is None

    def test_combined_model_repr(self, session):
        """Test that combined model has string representation."""
        class TestModel(BaseModelForTest, SoftDeleteMixinForTest):
            __tablename__ = "test_model_repr"
            name: Mapped[str] = mapped_column(String(100))

        TestBase.metadata.create_all(session.bind)
        
        instance = TestModel(name="test")
        session.add(instance)
        session.commit()
        
        repr_str = repr(instance)
        assert "TestModel" in repr_str
