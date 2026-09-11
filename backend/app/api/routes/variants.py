from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.models.database import get_session_local, StyleVariant, BaselinePrompt, AttackScenario

router = APIRouter()

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class VariantGenerateRequest(BaseModel):
    baseline_prompt_id: int
    attack_scenario_id: int
    techniques: List[str]
    count_per_technique: int = 2


@router.post("/variants/generate")
def generate_variants(request: VariantGenerateRequest, db: Session = Depends(get_db)):
    """Generate style variants for a baseline prompt"""
    from app.services.variant_generator import VariantGenerator
    
    # Get baseline prompt
    baseline = db.query(BaselinePrompt).filter(
        BaselinePrompt.id == request.baseline_prompt_id
    ).first()
    
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline prompt {request.baseline_prompt_id} not found"
        )
    
    # Get attack scenario for proper scenario_id
    scenario = db.query(AttackScenario).filter(
        AttackScenario.id == request.attack_scenario_id
    ).first()
    
    scenario_id = scenario.scenario_id if scenario else None
    
    # Generate variants
    variants = VariantGenerator.generate_variants(
        baseline_prompt=baseline.prompt_text,
        techniques=request.techniques,
        count_per_technique=request.count_per_technique,
        scenario_id=scenario_id
    )
    
    # Store variants
    created_variants = []
    for variant_data in variants:
        variant = StyleVariant(
            baseline_prompt_id=request.baseline_prompt_id,
            technique=variant_data["technique"],
            variant_text=variant_data["variant_text"]
        )
        db.add(variant)
        created_variants.append(variant)
    
    db.commit()
    
    return {
        "baseline_prompt_id": request.baseline_prompt_id,
        "variants_generated": len(variants),
        "variants": [
            {
                "id": v.id,
                "technique": v.technique,
                "variant_text": v.variant_text,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in created_variants
        ]
    }


@router.get("/variants/by-prompt/{baseline_prompt_id}")
def get_variants_by_prompt(baseline_prompt_id: int, db: Session = Depends(get_db)):
    """Get all variants for a baseline prompt"""
    baseline = db.query(BaselinePrompt).filter(
        BaselinePrompt.id == baseline_prompt_id
    ).first()
    
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline prompt {baseline_prompt_id} not found"
        )
    
    variants = db.query(StyleVariant).filter(
        StyleVariant.baseline_prompt_id == baseline_prompt_id
    ).all()
    
    return {
        "baseline_prompt_id": baseline_prompt_id,
        "baseline_text": baseline.prompt_text,
        "variants": [
            {
                "id": v.id,
                "technique": v.technique,
                "variant_text": v.variant_text,
                "model_runs_count": len(v.model_runs),
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in variants
        ]
    }


@router.get("/variants/{variant_id}")
def get_variant(variant_id: int, db: Session = Depends(get_db)):
    """Get a specific variant with its model runs"""
    variant = db.query(StyleVariant).filter(StyleVariant.id == variant_id).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant {variant_id} not found"
        )
    
    return {
        "id": variant.id,
        "baseline_prompt_id": variant.baseline_prompt_id,
        "baseline_text": variant.baseline_prompt.prompt_text if variant.baseline_prompt else None,
        "technique": variant.technique,
        "variant_text": variant.variant_text,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "model_runs": [
            {
                "id": run.id,
                "model_name": run.model_name,
                "model_vendor": run.model_vendor,
                "status": run.status,
                "has_evaluation": run.evaluation is not None
            }
            for run in variant.model_runs
        ]
    }
