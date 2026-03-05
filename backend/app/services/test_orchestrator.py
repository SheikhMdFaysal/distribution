from typing import Dict, List, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.database import (
    SecurityTest, BaselinePrompt, StyleVariant, ModelRun, EvaluationScore,
    TestStatus, AttackScenario, RiskLevel
)
from app.services.variant_generator import VariantGenerator
from app.services.leakage_detector import LeakageDetector
from app.services.risk_scorer import RiskScorer
from app.models.adapters.ollama_adapter import create_adapter


class TestOrchestrator:
    """Orchestrate security test execution"""
    
    @staticmethod
    def create_test(
        db: Session,
        test_name: str,
        attack_scenario_id: int,
        baseline_prompts: List[str],
        techniques: List[str],
        target_models: List[Dict[str, Any]],
        description: str = None
    ) -> SecurityTest:
        """Create a new security test"""
        # Create test record
        test = SecurityTest(
            test_name=test_name,
            description=description,
            attack_scenario_id=attack_scenario_id,
            techniques=techniques,
            target_models=target_models,
            status=TestStatus.QUEUED
        )
        db.add(test)
        db.flush()
        
        # Create baseline prompts
        for prompt_text in baseline_prompts:
            baseline = BaselinePrompt(
                security_test_id=test.id,
                prompt_text=prompt_text
            )
            db.add(baseline)
        
        db.commit()
        return test
    
    @staticmethod
    def generate_variants_for_test(
        db: Session,
        test_id: int,
        count_per_technique: int = 2
    ) -> int:
        """Generate variants for all baseline prompts in a test"""
        test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        # Get attack scenario for context
        scenario = db.query(AttackScenario).filter(
            AttackScenario.id == test.attack_scenario_id
        ).first()
        scenario_id = scenario.scenario_id if scenario else None
        
        total_variants = 0
        
        # Generate variants for each baseline prompt
        for baseline in test.baseline_prompts:
            variants = VariantGenerator.generate_variants(
                baseline_prompt=baseline.prompt_text,
                techniques=test.techniques,
                count_per_technique=count_per_technique,
                scenario_id=scenario_id
            )
            
            for variant_data in variants:
                variant = StyleVariant(
                    baseline_prompt_id=baseline.id,
                    technique=variant_data["technique"],
                    variant_text=variant_data["variant_text"]
                )
                db.add(variant)
                total_variants += 1
        
        test.total_variants = total_variants
        test.total_runs = total_variants * len(test.target_models)
        db.commit()
        
        return total_variants
    
    @staticmethod
    def execute_model_run(
        db: Session,
        variant_id: int,
        model_config: Dict[str, Any]
    ) -> ModelRun:
        """Execute a single model run"""
        variant = db.query(StyleVariant).filter(StyleVariant.id == variant_id).first()
        if not variant:
            raise ValueError(f"Variant {variant_id} not found")
        
        # Create adapter and generate response
        adapter = create_adapter(model_config)
        
        try:
            response = adapter.generate(variant.variant_text)
            
            # Create model run record
            model_run = ModelRun(
                style_variant_id=variant_id,
                model_name=response["model_name"],
                model_type=response["model_type"],
                model_vendor=response["vendor"],
                response_text=response["response_text"],
                response_metadata=response["metadata"],
                status="completed",
                completed_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            # Record failed run
            model_run = ModelRun(
                style_variant_id=variant_id,
                model_name=model_config.get("model", "unknown"),
                model_type=model_config.get("adapter", "unknown"),
                model_vendor=model_config.get("adapter", "unknown"),
                response_text="",
                response_metadata={"error": str(e)},
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(timezone.utc)
            )
        
        db.add(model_run)
        db.commit()
        
        # Evaluate the run
        TestOrchestrator.evaluate_run(db, model_run.id)
        
        return model_run
    
    @staticmethod
    def evaluate_run(db: Session, model_run_id: int) -> EvaluationScore:
        """Evaluate a model run for leakage"""
        model_run = db.query(ModelRun).filter(ModelRun.id == model_run_id).first()
        if not model_run:
            raise ValueError(f"Model run {model_run_id} not found")
        
        # Detect leakage
        detection_result = LeakageDetector.detect_leakage(
            response_text=model_run.response_text,
            variant_text=model_run.style_variant.variant_text if model_run.style_variant else None
        )
        
        # Classify data type
        data_classification = "UNCLASSIFIED"
        if detection_result["evidence"]:
            data_classification = LeakageDetector.classify_data_type(
                detection_result["evidence"][0].get("context", "")
            )
        
        # Calculate risk score
        confidence = max(detection_result["confidence"].values()) if detection_result["confidence"] else 0.5
        risk_result = RiskScorer.calculate_risk_score(
            leakage_categories=detection_result["categories"],
            data_classification=data_classification,
            confidence=confidence,
            model_type=model_run.model_type
        )
        
        # Get compliance violations
        compliance_violations = RiskScorer.get_compliance_violations(
            leakage_categories=detection_result["categories"]
        )
        
        # Evaluate vendor promise
        vendor_evaluation = RiskScorer.evaluate_vendor_promise(
            vendor=model_run.model_vendor,
            model_type=model_run.model_type,
            leakage_detected=detection_result["leakage_detected"]
        )
        
        # Create evaluation score
        evaluation = EvaluationScore(
            model_run_id=model_run_id,
            leakage_detected=detection_result["leakage_detected"],
            leakage_categories=detection_result["categories"],
            confidence_scores=detection_result["confidence"],
            evidence=str(detection_result["evidence"]),
            risk_score=risk_result["risk_score"],
            risk_level=risk_result["risk_level"],
            data_classification=data_classification,
            compliance_violations=compliance_violations,
            vendor_promise=vendor_evaluation["promise"],
            promise_held=vendor_evaluation["promise_held"]
        )
        
        db.add(evaluation)
        db.commit()
        
        return evaluation
    
    @staticmethod
    def update_test_status(db: Session, test_id: int) -> Dict[str, Any]:
        """Update test status and summary metrics"""
        test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        # Count completed runs
        completed_runs = 0
        vulnerabilities_found = 0
        total_risk_score = 0.0
        
        for baseline in test.baseline_prompts:
            for variant in baseline.variants:
                for run in variant.model_runs:
                    if run.status == "completed":
                        completed_runs += 1
                        if run.evaluation and run.evaluation.leakage_detected:
                            vulnerabilities_found += 1
                            total_risk_score += run.evaluation.risk_score
        
        test.runs_completed = completed_runs
        test.vulnerabilities_found = vulnerabilities_found
        
        if completed_runs > 0:
            test.avg_risk_score = total_risk_score / completed_runs
            
            # Determine overall risk level
            if test.avg_risk_score == 0:
                test.risk_level = RiskLevel.LOW
            elif test.avg_risk_score <= 2.0:
                test.risk_level = RiskLevel.LOW
            elif test.avg_risk_score <= 5.0:
                test.risk_level = RiskLevel.MEDIUM
            elif test.avg_risk_score <= 7.5:
                test.risk_level = RiskLevel.HIGH
            else:
                test.risk_level = RiskLevel.CRITICAL
        
        # Update status
        if completed_runs >= test.total_runs:
            test.status = TestStatus.COMPLETED
            test.completed_at = datetime.now(timezone.utc)
        elif completed_runs > 0:
            test.status = TestStatus.RUNNING
            if not test.started_at:
                test.started_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "test_id": test_id,
            "status": test.status.value,
            "runs_completed": completed_runs,
            "total_runs": test.total_runs,
            "vulnerabilities_found": vulnerabilities_found,
            "avg_risk_score": test.avg_risk_score,
            "risk_level": test.risk_level.value if test.risk_level else None
        }
