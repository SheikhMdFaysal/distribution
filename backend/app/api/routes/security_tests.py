from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from app.models.database import get_session_local, SecurityTest, AttackScenario, TestStatus
from app.services.test_orchestrator import TestOrchestrator

router = APIRouter()

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SecurityTestCreate(BaseModel):
    test_name: str
    description: Optional[str] = None
    attack_scenario_id: int
    baseline_prompts: List[str]
    techniques: List[str]
    target_models: List[dict]
    variants_per_technique: int = 2


class SecurityTestResponse(BaseModel):
    id: int
    test_name: str
    status: str
    total_runs: int
    runs_completed: int
    vulnerabilities_found: int
    avg_risk_score: Optional[float]
    risk_level: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/security-tests/run", response_model=dict)
def run_security_test(test_data: SecurityTestCreate, db: Session = Depends(get_db)):
    """Create and run a new security test (synchronous execution)"""
    try:
        # Create test
        test = TestOrchestrator.create_test(
            db=db,
            test_name=test_data.test_name,
            attack_scenario_id=test_data.attack_scenario_id,
            baseline_prompts=test_data.baseline_prompts,
            techniques=test_data.techniques,
            target_models=test_data.target_models,
            description=test_data.description or ""
        )
        
        # Generate variants synchronously
        TestOrchestrator.generate_variants_for_test(
            db=db,
            test_id=test.id,
            count_per_technique=test_data.variants_per_technique
        )
        
        # Update test status to running
        test.status = TestStatus.RUNNING
        test.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Execute model runs synchronously
        test = db.query(SecurityTest).filter(SecurityTest.id == test.id).first()
        total_completed = 0
        vulnerabilities_found = 0
        
        for baseline in test.baseline_prompts:
            for variant in baseline.variants:
                for model_config in test.target_models:
                    try:
                        TestOrchestrator.execute_model_run(
                            db=db,
                            variant_id=variant.id,
                            model_config=model_config
                        )
                        total_completed += 1
                        
                        # Check if vulnerability found
                        if variant.model_runs:
                            for run in variant.model_runs:
                                if run.evaluation and run.evaluation.leakage_detected:
                                    vulnerabilities_found += 1
                    except Exception as e:
                        print(f"Error running model: {e}")
        
        # Update test completion
        TestOrchestrator.update_test_status(db, test.id)
        
        return {
            "test_id": test.id,
            "status": "completed",
            "message": "Test completed successfully",
            "runs_completed": total_completed,
            "vulnerabilities_found": vulnerabilities_found
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test: {str(e)}"
        )


@router.get("/security-tests")
def list_security_tests(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status")
):
    """List all security tests with pagination"""
    query = db.query(SecurityTest).order_by(SecurityTest.created_at.desc())
    
    if status_filter:
        try:
            status_enum = TestStatus(status_filter)
            query = query.filter(SecurityTest.status == status_enum)
        except ValueError:
            pass  # Ignore invalid status values
    
    total = query.count()
    tests = query.offset(offset).limit(limit).all()
    
    return {
        "tests": tests,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.delete("/security-tests/{test_id}")
def delete_security_test(test_id: int, db: Session = Depends(get_db)):
    """Delete a security test and all associated data"""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Delete associated data (cascades should handle this, but explicit is safer)
    from app.models.database import BaselinePrompt, StyleVariant, ModelRun, EvaluationScore
    
    for baseline in test.baseline_prompts:
        for variant in baseline.variants:
            for run in variant.model_runs:
                if run.evaluation:
                    db.delete(run.evaluation)
                db.delete(run)
            db.delete(variant)
        db.delete(baseline)
    
    db.delete(test)
    db.commit()
    
    return {
        "message": f"Test {test_id} deleted successfully",
        "test_id": test_id
    }


@router.post("/security-tests/{test_id}/cancel")
def cancel_security_test(test_id: int, db: Session = Depends(get_db)):
    """Cancel a running security test"""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    if test.status == TestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed test"
        )
    
    if test.status == TestStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has already failed"
        )
    
    test.status = TestStatus.FAILED
    test.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "message": f"Test {test_id} cancelled",
        "test_id": test_id,
        "status": test.status.value
    }


@router.get("/models")
def list_available_models():
    """List available models for testing"""
    return {
        "models": [
            {"adapter": "openai", "model": "gpt-4", "type": "enterprise", "vendor": "OpenAI"},
            {"adapter": "openai", "model": "gpt-4-turbo", "type": "enterprise", "vendor": "OpenAI"},
            {"adapter": "anthropic", "model": "claude-3-opus-20240229", "type": "enterprise", "vendor": "Anthropic"},
            {"adapter": "anthropic", "model": "claude-3-sonnet-20240229", "type": "enterprise", "vendor": "Anthropic"},
            {"adapter": "anthropic", "model": "claude-3-5-sonnet-20240620", "type": "enterprise", "vendor": "Anthropic"},
            {"adapter": "google", "model": "gemini-1.5-pro", "type": "enterprise", "vendor": "Google"},
            {"adapter": "google", "model": "gemini-1.5-flash", "type": "enterprise", "vendor": "Google"},
            {"adapter": "ollama", "model": "llama3", "type": "local", "vendor": "Ollama"},
            {"adapter": "ollama", "model": "mistral", "type": "local", "vendor": "Ollama"},
            {"adapter": "ollama", "model": "codellama", "type": "local", "vendor": "Ollama"},
        ]
    }


@router.get("/security-tests/{test_id}", response_model=dict)
def get_security_test(test_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a security test"""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Get scenario info
    scenario = db.query(AttackScenario).filter(
        AttackScenario.id == test.attack_scenario_id
    ).first()
    
    # Get baseline prompts with variants and model runs
    baseline_prompts = []
    for bp in test.baseline_prompts:
        variants_data = []
        for v in bp.variants:
            runs_data = []
            for r in v.model_runs:
                runs_data.append({
                    "id": r.id,
                    "model_name": r.model_name,
                    "model_vendor": r.model_vendor,
                    "model_type": r.model_type,
                    "response_text": r.response_text,
                    "status": r.status,
                    "error_message": r.error_message,
                    "evaluation": {
                        "leakage_detected": r.evaluation.leakage_detected if r.evaluation else False,
                        "risk_score": r.evaluation.risk_score if r.evaluation else 0,
                        "risk_level": r.evaluation.risk_level.value if r.evaluation and r.evaluation.risk_level else None,
                        "leakage_categories": r.evaluation.leakage_categories if r.evaluation else []
                    } if r.evaluation else None
                })
            variants_data.append({
                "id": v.id,
                "technique": v.technique,
                "variant_text": v.variant_text,
                "model_runs": runs_data
            })
        baseline_prompts.append({
            "id": bp.id,
            "prompt_text": bp.prompt_text,
            "variants": variants_data
        })
    
    return {
        "id": test.id,
        "test_name": test.test_name,
        "description": test.description,
        "status": test.status.value if test.status else None,
        "attack_scenario": {
            "id": scenario.id if scenario else None,
            "name": scenario.scenario_name if scenario else None,
            "description": scenario.description if scenario else None
        },
        "techniques": test.techniques,
        "target_models": test.target_models,
        "baseline_prompts": baseline_prompts,
        "total_variants": test.total_variants,
        "total_runs": test.total_runs,
        "runs_completed": test.runs_completed,
        "vulnerabilities_found": test.vulnerabilities_found,
        "avg_risk_score": test.avg_risk_score,
        "risk_level": test.risk_level.value if test.risk_level else None,
        "created_at": test.created_at.isoformat() if test.created_at else None,
        "started_at": test.started_at.isoformat() if test.started_at else None,
        "completed_at": test.completed_at.isoformat() if test.completed_at else None
    }


@router.get("/security-tests/{test_id}/status", response_model=dict)
def get_test_status(test_id: int, db: Session = Depends(get_db)):
    """Get current status of a security test"""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Update status
    status_update = TestOrchestrator.update_test_status(db, test_id)
    
    # Calculate progress
    progress_percent = 0
    if test.total_runs > 0:
        progress_percent = int((test.runs_completed / test.total_runs) * 100)
    
    return {
        "test_id": test_id,
        "test_name": test.test_name,
        "status": status_update["status"],
        "progress": {
            "percent_complete": progress_percent,
            "runs_completed": test.runs_completed,
            "total_runs": test.total_runs,
            "variants_generated": test.total_variants
        },
        "results_summary": {
            "vulnerabilities_found": test.vulnerabilities_found,
            "avg_risk_score": test.avg_risk_score,
            "risk_level": test.risk_level.value if test.risk_level else None
        }
    }


@router.get("/attack-scenarios", response_model=List[dict])
def list_attack_scenarios(db: Session = Depends(get_db)):
    """List all available attack scenarios"""
    from app.seed_data import DEFAULT_BASELINE_PROMPTS
    scenarios = db.query(AttackScenario).all()
    return [
        {
            "id": s.id,
            "scenario_id": s.scenario_id,
            "name": s.scenario_name,
            "description": s.description,
            "target_model_type": s.target_model_type.value if s.target_model_type else None,
            "compliance_frameworks": s.compliance_frameworks,
            "attack_techniques": s.attack_techniques,
            "vendor_promise_tested": s.vendor_promise_tested,
            "default_prompts": DEFAULT_BASELINE_PROMPTS.get(s.scenario_id, [])
        }
        for s in scenarios
    ]


@router.get("/baseline-prompts/{scenario_id}")
def get_baseline_prompts(scenario_id: str):
    """Get default baseline prompts for a scenario"""
    from app.seed_data import DEFAULT_BASELINE_PROMPTS
    prompts = DEFAULT_BASELINE_PROMPTS.get(scenario_id, [])
    return {
        "scenario_id": scenario_id,
        "prompts": prompts,
        "count": len(prompts)
    }


@router.get("/security-tests/{test_id}/export")
def export_test_results(test_id: int, format: str = Query("csv", pattern="^(csv|json|pdf)$"), db: Session = Depends(get_db)):
    """Export test results as CSV, JSON, or PDF"""
    from app.models.database import BaselinePrompt, StyleVariant, ModelRun, EvaluationScore
    import csv
    import io
    
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Get all model runs with evaluations
    results = []
    for baseline in test.baseline_prompts:
        for variant in baseline.variants:
            for run in variant.model_runs:
                eval_score = run.evaluation
                results.append({
                    "baseline_prompt": baseline.prompt_text,
                    "technique": variant.technique,
                    "variant_text": variant.variant_text,
                    "model_name": run.model_name,
                    "model_vendor": run.model_vendor,
                    "response_text": run.response_text[:500] if run.response_text else "",
                    "leakage_detected": eval_score.leakage_detected if eval_score else False,
                    "leakage_categories": ",".join(eval_score.leakage_categories) if eval_score and eval_score.leakage_categories else "",
                    "risk_score": eval_score.risk_score if eval_score else 0,
                    "risk_level": eval_score.risk_level.value if eval_score and eval_score.risk_level else "N/A",
                    "promise_held": eval_score.promise_held if eval_score else True,
                    "vendor_promise": eval_score.vendor_promise if eval_score else "",
                })
    
    if format == "json":
        return {
            "test_name": test.test_name,
            "test_id": test_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "results": results
        }
    
    if format == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=TA_CENTER)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceBefore=20, spaceAfter=10)
        normal_style = styles['Normal']
        
        elements.append(Paragraph("Enterprise AI Security Test Report", title_style))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>Test Name:</b> {test.test_name}", normal_style))
        elements.append(Paragraph(f"<b>Test ID:</b> {test_id}", normal_style))
        elements.append(Paragraph(f"<b>Target Vendor:</b> {test.target_vendor}", normal_style))
        elements.append(Paragraph(f"<b>Target Model:</b> {test.target_model}", normal_style))
        if test.created_at:
            elements.append(Paragraph(f"<b>Created:</b> {test.created_at.strftime('%Y-%m-%d %H:%M')}", normal_style))
        elements.append(Paragraph(f"<b>Export Date:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", normal_style))
        elements.append(Spacer(1, 20))
        
        leaked_count = sum(1 for r in results if r.get('leakage_detected'))
        total_runs = len(results)
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(f"Total Test Runs: {total_runs}", normal_style))
        elements.append(Paragraph(f"Data Leakage Detected: {leaked_count} ({100*leaked_count//max(total_runs,1)}%)", normal_style))
        elements.append(Paragraph(f"Safe: {total_runs - leaked_count} ({100*(total_runs-leaked_count)//max(total_runs,1)}%)", normal_style))
        
        if results:
            elements.append(Paragraph("Detailed Results", heading_style))
            
            for i, r in enumerate(results):
                if i > 0 and i % 10 == 0:
                    elements.append(PageBreak())
                
                elements.append(Paragraph(f"<b>Test #{i+1}</b>", normal_style))
                table_data = [
                    ['Attribute', 'Value'],
                    ['Baseline Prompt', r.get('baseline_prompt', '')[:80] + '...' if len(r.get('baseline_prompt', '')) > 80 else r.get('baseline_prompt', '')],
                    ['Technique', r.get('technique', '')],
                    ['Model', f"{r.get('model_name', '')} ({r.get('model_vendor', '')})"],
                    ['Leakage Detected', 'YES' if r.get('leakage_detected') else 'NO'],
                    ['Risk Level', r.get('risk_level', 'N/A')],
                    ['Risk Score', str(r.get('risk_score', 0))],
                ]
                if r.get('leakage_categories'):
                    table_data.append(['Leakage Categories', r.get('leakage_categories')])
                if r.get('vendor_promise'):
                    table_data.append(['Vendor Promise', r.get('vendor_promise')])
                
                table = Table(table_data, colWidths=[2*inch, 4*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (0, 0), (1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 15))
        
        doc.build(elements)
        buffer.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=test_report_{test_id}.pdf"
            }
        )
    
    # CSV export
    output = io.StringIO()
    if results:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    csv_content = output.getvalue()
    
    return {
        "test_id": test_id,
        "test_name": test.test_name,
        "format": "csv",
        "record_count": len(results),
        "csv_data": csv_content
    }
