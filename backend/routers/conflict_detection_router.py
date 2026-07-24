"""
Multi-Plan Conflict Detection Router (Phase 2c)
Endpoints for detecting and resolving plan conflicts
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from core.db import get_db
from core.security import get_current_user
from models.phase2_schemas import (
    PlanConflict,
    ConflictResolutionSuggestion,
)
from services.conflict_detection_service import ConflictDetectionService


router = APIRouter(prefix="/api/v1/conflicts", tags=["conflicts"])


# ========================================================================
# CONFLICT DETECTION ENDPOINTS
# ========================================================================


@router.get("/detect", response_model=dict)
async def detect_conflicts(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Detect all conflicts in user's study plans
    
    Returns:
        - List of detected conflicts
        - Summary (total count, affected hours, types)
    """
    service = ConflictDetectionService(db)
    
    try:
        conflicts, summary = await service.detect_conflicts(
            ObjectId(current_user["_id"])
        )
        
        return {
            "success": True,
            "conflicts": [c.dict() for c in conflicts],
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect conflicts: {str(e)}"
        )


@router.get("/list", response_model=List[PlanConflict])
async def list_conflicts(
    resolved: bool = False,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List user's detected conflicts
    
    Args:
        resolved: Filter by resolution status (True=resolved, False=unresolved)
    """
    service = ConflictDetectionService(db)
    
    try:
        conflicts = await service.list_conflicts(
            user_id=ObjectId(current_user["_id"]),
            resolved=resolved,
        )
        return conflicts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{conflict_id}", response_model=PlanConflict)
async def get_conflict(
    conflict_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get details of a specific conflict"""
    service = ConflictDetectionService(db)
    
    try:
        conflict = await service.get_conflict(ObjectId(conflict_id))
        if not conflict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conflict not found"
            )
        
        # Verify ownership
        if str(conflict.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conflict"
            )
        
        return conflict
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========================================================================
# CONFLICT ANALYSIS ENDPOINTS
# ========================================================================


@router.get("/{conflict_id}/analyze")
async def analyze_conflict(
    conflict_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get detailed analysis of a conflict
    
    Returns:
        - Conflict details
        - Affected plans
        - Severity assessment
        - Recommended actions
    """
    service = ConflictDetectionService(db)
    
    try:
        conflict = await service.get_conflict(ObjectId(conflict_id))
        if not conflict or str(conflict.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        return {
            "success": True,
            "conflict": conflict.dict(),
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity,
            "affected_hours": conflict.affected_total_hours,
            "affected_plans": conflict.plan_names,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========================================================================
# RESOLUTION SUGGESTION ENDPOINTS
# ========================================================================


@router.get("/{conflict_id}/suggestions", response_model=List[ConflictResolutionSuggestion])
async def get_resolution_suggestions(
    conflict_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get resolution suggestions for a conflict
    
    Returns multiple suggestions with:
    - Suggestion type (reschedule, redistribute_hours, extend_deadline, etc.)
    - Affected plans
    - Expected impact and confidence scores
    """
    service = ConflictDetectionService(db)
    
    try:
        conflict = await service.get_conflict(ObjectId(conflict_id))
        if not conflict or str(conflict.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        suggestions = await service.suggest_resolutions(ObjectId(conflict_id))
        return suggestions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========================================================================
# RESOLUTION EXECUTION ENDPOINTS
# ========================================================================


@router.post("/{conflict_id}/resolve")
async def apply_resolution(
    conflict_id: str,
    suggestion_type: str,
    resolution_details: dict = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Apply a resolution to a conflict
    
    Args:
        conflict_id: Conflict to resolve
        suggestion_type: Type of resolution (reschedule, extend_deadline, deprioritize, etc.)
        resolution_details: Additional details for the resolution
    """
    service = ConflictDetectionService(db)
    
    try:
        conflict = await service.get_conflict(ObjectId(conflict_id))
        if not conflict or str(conflict.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        resolution_details = resolution_details or {}
        success = await service.apply_resolution(
            ObjectId(conflict_id),
            suggestion_type,
            resolution_details,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply resolution"
            )
        
        return {
            "success": True,
            "conflict_id": conflict_id,
            "resolution_type": suggestion_type,
            "message": f"Conflict resolved using strategy: {suggestion_type}"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply resolution: {str(e)}"
        )


# ========================================================================
# BULK CONFLICT RESOLUTION ENDPOINTS
# ========================================================================


@router.post("/resolve/auto")
async def auto_resolve_conflicts(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Automatically resolve all unresolved conflicts using best suggestions
    """
    service = ConflictDetectionService(db)
    
    try:
        conflicts = await service.list_conflicts(
            ObjectId(current_user["_id"]),
            resolved=False,
        )
        
        resolved_count = 0
        for conflict in conflicts:
            suggestions = await service.suggest_resolutions(conflict.id)
            if suggestions:
                # Pick the suggestion with highest confidence and lowest impact
                best_suggestion = min(
                    suggestions,
                    key=lambda s: (-s.confidence_score, s.impact_score)
                )
                
                success = await service.apply_resolution(
                    conflict.id,
                    best_suggestion.suggestion_type,
                    {},
                )
                
                if success:
                    resolved_count += 1
        
        return {
            "success": True,
            "total_conflicts": len(conflicts),
            "resolved_count": resolved_count,
            "remaining_conflicts": len(conflicts) - resolved_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-resolution failed: {str(e)}"
        )


@router.post("/resolve/batch")
async def batch_resolve_conflicts(
    conflict_ids: List[str],
    suggestion_type: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Apply the same resolution strategy to multiple conflicts
    """
    service = ConflictDetectionService(db)
    
    try:
        resolved_count = 0
        
        for conflict_id in conflict_ids:
            conflict = await service.get_conflict(ObjectId(conflict_id))
            if not conflict or str(conflict.user_id) != current_user["_id"]:
                continue
            
            success = await service.apply_resolution(
                ObjectId(conflict_id),
                suggestion_type,
                {},
            )
            
            if success:
                resolved_count += 1
        
        return {
            "success": True,
            "total_processed": len(conflict_ids),
            "resolved_count": resolved_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch resolution failed: {str(e)}"
        )


# ========================================================================
# CONFLICT DASHBOARD ENDPOINT
# ========================================================================


@router.get("/dashboard/summary")
async def get_conflict_dashboard(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get comprehensive conflict dashboard summary
    
    Returns:
        - Total conflicts
        - Breakdown by type
        - Breakdown by severity
        - Total affected hours
        - Auto-resolution recommendations
    """
    service = ConflictDetectionService(db)
    
    try:
        conflicts, summary = await service.detect_conflicts(
            ObjectId(current_user["_id"])
        )
        
        resolved = await service.list_conflicts(
            ObjectId(current_user["_id"]),
            resolved=True,
        )
        
        unresolved = await service.list_conflicts(
            ObjectId(current_user["_id"]),
            resolved=False,
        )
        
        return {
            "success": True,
            "total_conflicts": summary["total_conflicts"],
            "resolved_conflicts": len(resolved),
            "unresolved_conflicts": len(unresolved),
            "affected_total_hours": summary["affected_hours"],
            "conflict_types": summary["conflict_types"],
            "severity_breakdown": summary["severity_breakdown"],
            "requires_immediate_attention": len(
                [c for c in conflicts if c.severity == "high"]
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )