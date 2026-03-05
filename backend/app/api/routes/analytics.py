from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from typing import List, Dict, Any

from app.models.database import (
    get_session_local, SecurityTest, ModelRun, EvaluationScore,
    RiskLevel, StyleVariant, BaselinePrompt
)

router = APIRouter()

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/analytics/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Get dashboard summary analytics"""
    # Overall metrics
    total_tests = db.query(SecurityTest).count()
    completed_tests = db.query(SecurityTest).filter(
        SecurityTest.status == SecurityTest.status.COMPLETED
    ).count()
    
    # Vulnerability metrics
    total_vulnerabilities = db.query(func.sum(SecurityTest.vulnerabilities_found)).scalar() or 0
    
    # Risk score metrics
    avg_risk = db.query(func.avg(SecurityTest.avg_risk_score)).scalar() or 0
    
    # Vendor comparison
    vendor_stats = db.query(
        ModelRun.model_vendor,
        func.count(ModelRun.id).label("total_runs"),
        func.sum(EvaluationScore.leakage_detected.cast(Integer)).label("leakage_count")
    ).join(
        EvaluationScore, ModelRun.id == EvaluationScore.model_run_id
    ).group_by(ModelRun.model_vendor).all()
    
    vendor_comparison = []
    for vendor, total, leakage in vendor_stats:
        leakage_rate = (leakage / total * 100) if total > 0 else 0
        vendor_comparison.append({
            "vendor": vendor,
            "total_runs": total,
            "leakage_incidents": leakage,
            "leakage_rate": round(leakage_rate, 1)
        })
    
    # Risk distribution
    risk_distribution = db.query(
        EvaluationScore.risk_level,
        func.count(EvaluationScore.id).label("count")
    ).group_by(EvaluationScore.risk_level).all()
    
    return {
        "summary": {
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "total_vulnerabilities": int(total_vulnerabilities),
            "avg_risk_score": round(avg_risk, 2)
        },
        "vendor_comparison": vendor_comparison,
        "risk_distribution": [
            {"level": level.value if level else "unknown", "count": count}
            for level, count in risk_distribution
        ]
    }


@router.get("/analytics/test/{test_id}/summary")
def get_test_analytics(test_id: int, db: Session = Depends(get_db)):
    """Get detailed analytics for a specific test"""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    
    # Get all evaluations for this test
    evaluations = db.query(EvaluationScore).join(
        ModelRun, EvaluationScore.model_run_id == ModelRun.id
    ).join(
        StyleVariant, ModelRun.style_variant_id == StyleVariant.id
    ).join(
        BaselinePrompt, StyleVariant.baseline_prompt_id == BaselinePrompt.id
    ).filter(
        BaselinePrompt.security_test_id == test_id
    ).all()
    
    # Attack success rate by technique
    technique_stats = {}
    for eval in evaluations:
        technique = eval.model_run.style_variant.technique
        if technique not in technique_stats:
            technique_stats[technique] = {"total": 0, "leakage": 0}
        technique_stats[technique]["total"] += 1
        if eval.leakage_detected:
            technique_stats[technique]["leakage"] += 1
    
    technique_asr = {
        technique: {
            "success_rate": round((stats["leakage"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0,
            "total_runs": stats["total"],
            "leakage_runs": stats["leakage"]
        }
        for technique, stats in technique_stats.items()
    }
    
    # Vendor stats for this test
    vendor_stats = db.query(
        ModelRun.model_vendor,
        func.count(ModelRun.id).label("total"),
        func.sum(EvaluationScore.leakage_detected.cast(Integer)).label("leakage"),
        func.avg(EvaluationScore.risk_score).label("avg_risk")
    ).join(
        EvaluationScore, ModelRun.id == EvaluationScore.model_run_id
    ).join(
        StyleVariant, ModelRun.style_variant_id == StyleVariant.id
    ).join(
        BaselinePrompt, StyleVariant.baseline_prompt_id == BaselinePrompt.id
    ).filter(
        BaselinePrompt.security_test_id == test_id
    ).group_by(ModelRun.model_vendor).all()
    
    vendor_comparison = [
        {
            "vendor": vendor,
            "total_runs": total,
            "leakage_incidents": leakage or 0,
            "leakage_rate": round((leakage or 0) / total * 100, 1) if total > 0 else 0,
            "avg_risk_score": round(avg_risk or 0, 2)
        }
        for vendor, total, leakage, avg_risk in vendor_stats
    ]
    
    return {
        "test_id": test_id,
        "test_name": test.test_name,
        "total_runs": test.total_runs,
        "vulnerabilities_found": test.vulnerabilities_found,
        "avg_risk_score": test.avg_risk_score,
        "risk_level": test.risk_level.value if test.risk_level else None,
        "technique_effectiveness": technique_asr,
        "vendor_comparison": vendor_comparison
    }


@router.get("/analytics/vendor-comparison")
def get_vendor_comparison(db: Session = Depends(get_db)):
    """Get vendor comparison across all tests"""
    vendor_stats = db.query(
        ModelRun.model_vendor,
        ModelRun.model_name,
        func.count(ModelRun.id).label("total_runs"),
        func.sum(EvaluationScore.leakage_detected.cast(Integer)).label("leakage"),
        func.avg(EvaluationScore.risk_score).label("avg_risk"),
        func.max(EvaluationScore.risk_score).label("max_risk")
    ).join(
        EvaluationScore, ModelRun.id == EvaluationScore.model_run_id
    ).group_by(ModelRun.model_vendor, ModelRun.model_name).all()
    
    return {
        "vendors": [
            {
                "vendor": vendor,
                "model": model,
                "runs": total,
                "leakage_incidents": leakage or 0,
                "leakage_rate": round((leakage or 0) / total * 100, 1) if total > 0 else 0,
                "avg_risk_score": round(avg_risk or 0, 2),
                "highest_risk_score": round(max_risk or 0, 2),
                "promise_compliance_rate": round((1 - (leakage or 0) / total) * 100, 1) if total > 0 else 100
            }
            for vendor, model, total, leakage, avg_risk, max_risk in vendor_stats
        ]
    }

