from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone

from app.core.config import settings
from app.models.database import get_session_local, SecurityTest, AttackScenario, TestStatus
from app.services.executive_summary_jobs import get_summary_job, start_summary_job
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


def _as_string_list(value: object) -> List[str]:
    """Normalize JSON-backed values into a deduplicated list of display strings."""
    if not isinstance(value, list):
        return []
    return sorted({str(item) for item in value if item})


def _build_executive_summary_context(test: SecurityTest) -> str:
    """Build compact, aggregated evidence for the executive-summary model prompt."""
    models_tested: Set[str] = set()
    risk_levels: Dict[str, int] = {}
    vulnerability_categories: Set[str] = set()
    compliance_frameworks: Set[str] = set(_as_string_list(
        test.attack_scenario.compliance_frameworks if test.attack_scenario else []
    ))
    total_variants = 0
    total_runs = 0
    vulnerabilities_found = 0

    for baseline_prompt in test.baseline_prompts:
        for variant in baseline_prompt.variants:
            total_variants += 1
            for model_run in variant.model_runs:
                total_runs += 1
                models_tested.add(model_run.model_name)
                evaluation = model_run.evaluation
                if not evaluation:
                    continue

                risk_level = evaluation.risk_level.value if evaluation.risk_level else "Unknown"
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
                if evaluation.leakage_detected:
                    vulnerabilities_found += 1
                    vulnerability_categories.update(_as_string_list(evaluation.leakage_categories))
                compliance_frameworks.update(_as_string_list(evaluation.compliance_violations))

    configured_models = set()
    if isinstance(test.target_models, list):
        configured_models = {
            str(model.get("model"))
            for model in test.target_models
            if isinstance(model, dict) and model.get("model")
        }
    models_tested.update(configured_models)
    scenario_name = test.attack_scenario.scenario_name if test.attack_scenario else "Unspecified scenario"
    risk_level_text = ", ".join(
        f"{level}: {count}" for level, count in sorted(risk_levels.items())
    ) or "No completed evaluations"

    return "\n".join([
        f"Scenario: {scenario_name}",
        f"Test name: {test.test_name}",
        f"Models tested: {', '.join(sorted(models_tested)) or 'None recorded'}",
        f"Baseline prompts: {len(test.baseline_prompts)}; variants: {total_variants}; model runs: {total_runs}",
        f"Vulnerabilities found: {vulnerabilities_found}",
        f"Risk levels across evaluated runs: {risk_level_text}",
        f"Vulnerability categories: {', '.join(sorted(vulnerability_categories)) or 'None detected'}",
        f"Compliance frameworks implicated: {', '.join(sorted(compliance_frameworks)) or 'None recorded'}",
        f"Overall test risk: {test.risk_level.value if test.risk_level else 'Not calculated'}",
    ])


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
        run_errors: List[str] = []  # collect errors instead of swallowing them

        for baseline in test.baseline_prompts:
            for variant in baseline.variants:
                for model_config in test.target_models:
                    try:
                        # execute_model_run returns the newly-created ModelRun.
                        # Counting via the return value avoids the previous
                        # double-counting bug, which re-iterated all of the
                        # variant's prior runs and accumulated their leakage
                        # counts on every loop pass.
                        new_run = TestOrchestrator.execute_model_run(
                            db=db,
                            variant_id=variant.id,
                            model_config=model_config,
                        )
                        total_completed += 1
                        if new_run and new_run.evaluation and new_run.evaluation.leakage_detected:
                            vulnerabilities_found += 1
                    except Exception as e:
                        # Don't crash the whole test if one model fails.
                        # Capture for visibility instead of silent print().
                        run_errors.append(f"{model_config.get('model', 'unknown')}: {e}")

        # Update test completion (this also recomputes counts from the DB,
        # so the DB stays authoritative even if the inline counters drift)
        TestOrchestrator.update_test_status(db, test.id)

        # Re-fetch to return the authoritative DB values rather than the inline counters
        test = db.query(SecurityTest).filter(SecurityTest.id == test.id).first()
        return {
            "test_id": test.id,
            "status": test.status.value if test.status else "completed",
            "message": "Test completed successfully",
            "runs_completed": test.runs_completed or total_completed,
            "vulnerabilities_found": test.vulnerabilities_found or vulnerabilities_found,
            "errors": run_errors if run_errors else None,
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
                # Extract matched phrases from evidence (stored as JSON, fall back to legacy str repr)
                matched_phrases = []
                if r.evaluation and r.evaluation.evidence:
                    try:
                        import json as _json
                        ev_list = _json.loads(r.evaluation.evidence)
                        if isinstance(ev_list, list):
                            seen = set()
                            for ev in ev_list:
                                if isinstance(ev, dict):
                                    mt = ev.get("matched_text") or ""
                                    if mt and mt != "[PII detected]" and mt.lower() not in seen:
                                        matched_phrases.append(mt)
                                        seen.add(mt.lower())
                    except Exception:
                        pass

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
                        "leakage_categories": r.evaluation.leakage_categories if r.evaluation else [],
                        "matched_phrases": matched_phrases,
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


@router.post("/security-tests/{test_id}/executive-summary", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
def generate_executive_summary(test_id: int, db: Session = Depends(get_db)):
    """Start background generation of a plain-English executive summary."""
    test = db.query(SecurityTest).filter(SecurityTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found",
        )

    if test.status != TestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Executive summaries are available after a security test is completed.",
        )

    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executive Summary is unavailable because the OPENAI_API_KEY is not configured.",
        )

    job_id = start_summary_job(test_id, _build_executive_summary_context(test))
    return {"test_id": test_id, "job_id": job_id, "status": "processing"}


@router.get("/security-tests/{test_id}/executive-summary/{job_id}", response_model=dict)
def get_executive_summary_job(test_id: int, job_id: str):
    """Return the current status or completed result of an executive-summary job."""
    job = get_summary_job(job_id, test_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Executive Summary job not found",
        )
    if job["status"] == "failed":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=job["error"])
    return job


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
