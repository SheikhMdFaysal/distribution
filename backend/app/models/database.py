from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, Text as TextType
from datetime import datetime, timezone
import enum
import json

from app.core.config import settings

# Custom JSON type that works with both PostgreSQL and SQLite
class JSON(TypeDecorator):
    impl = TextType
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        return json.loads(value)

Base = declarative_base()

# Enums
class ModelType(str, enum.Enum):
    ENTERPRISE = "enterprise"
    PUBLIC = "public"
    LOCAL = "local"

class TestStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DataClassification(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

# Models
class AttackScenario(Base):
    __tablename__ = "attack_scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(100), unique=True, index=True)
    scenario_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_model_type = Column(Enum(ModelType), default=ModelType.ENTERPRISE)
    data_classification = Column(Enum(DataClassification), default=DataClassification.CONFIDENTIAL)
    compliance_frameworks = Column(JSON, default=list)
    severity_threshold = Column(String(50), default="high")
    attack_techniques = Column(JSON, default=list)
    vendor_promise_tested = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    security_tests = relationship("SecurityTest", back_populates="attack_scenario")

class SecurityTest(Base):
    __tablename__ = "security_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(200), nullable=False)
    description = Column(Text)
    attack_scenario_id = Column(Integer, ForeignKey("attack_scenarios.id"))
    status = Column(Enum(TestStatus), default=TestStatus.QUEUED)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Configuration
    techniques = Column(JSON, default=list)
    target_models = Column(JSON, default=list)
    variants_per_technique = Column(Integer, default=2)
    
    # Results Summary
    total_variants = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    runs_completed = Column(Integer, default=0)
    vulnerabilities_found = Column(Integer, default=0)
    avg_risk_score = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    
    # Relationships
    attack_scenario = relationship("AttackScenario", back_populates="security_tests")
    baseline_prompts = relationship("BaselinePrompt", back_populates="security_test")

class BaselinePrompt(Base):
    __tablename__ = "baseline_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    security_test_id = Column(Integer, ForeignKey("security_tests.id"))
    prompt_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    security_test = relationship("SecurityTest", back_populates="baseline_prompts")
    variants = relationship("StyleVariant", back_populates="baseline_prompt")

class StyleVariant(Base):
    __tablename__ = "style_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    baseline_prompt_id = Column(Integer, ForeignKey("baseline_prompts.id"))
    technique = Column(String(50), nullable=False)  # poetry, narrative, metaphor, euphemism
    variant_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    baseline_prompt = relationship("BaselinePrompt", back_populates="variants")
    model_runs = relationship("ModelRun", back_populates="style_variant")

class ModelRun(Base):
    __tablename__ = "model_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    style_variant_id = Column(Integer, ForeignKey("style_variants.id"))
    model_name = Column(String(100), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    model_vendor = Column(String(50), nullable=False)
    
    # Response
    response_text = Column(Text)
    response_metadata = Column(JSON, default=dict)
    
    # Status
    status = Column(String(50), default="completed")  # completed, failed, timeout
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Relationships
    style_variant = relationship("StyleVariant", back_populates="model_runs")
    evaluation = relationship("EvaluationScore", back_populates="model_run", uselist=False)

class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"))
    
    # Leakage Detection
    leakage_detected = Column(Boolean, default=False)
    leakage_categories = Column(JSON, default=list)  # cross_user, training_data, context_boundary, system_prompt
    confidence_scores = Column(JSON, default=dict)
    evidence = Column(Text)
    
    # Risk Scoring
    risk_score = Column(Float, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    data_classification = Column(String(50))
    
    # Compliance
    compliance_violations = Column(JSON, default=list)
    
    # Vendor Promise
    vendor_promise = Column(Text)
    promise_held = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    model_run = relationship("ModelRun", back_populates="evaluation")

# Database setup
def get_engine():
    # Handle SQLite special requirements
    if settings.DATABASE_URL.startswith('sqlite'):
        return create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

def get_session_local():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
