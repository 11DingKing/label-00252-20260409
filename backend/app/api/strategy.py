"""Control strategy API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.strategy import ControlStrategy
from app.models.user import User, OperationLog
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from app.schemas.common import ResponseModel
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/strategies", tags=["Control Strategies"])
logger = get_logger(__name__)


@router.get("", response_model=ResponseModel[List[StrategyResponse]])
async def get_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all control strategies."""
    strategies = db.query(ControlStrategy).all()
    return ResponseModel(data=[StrategyResponse.model_validate(s) for s in strategies])


@router.post("", response_model=ResponseModel[StrategyResponse])
async def create_strategy(
    request: Request,
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new control strategy."""
    existing = db.query(ControlStrategy).filter(ControlStrategy.name == strategy_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Strategy name already exists")
    
    strategy = ControlStrategy(**strategy_data.model_dump())
    db.add(strategy)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="strategy",
        detail=f"Created strategy: {strategy_data.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy {strategy_data.name} created by {current_user.username}")
    
    return ResponseModel(data=StrategyResponse.model_validate(strategy))


@router.get("/{strategy_id}", response_model=ResponseModel[StrategyResponse])
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategy by ID."""
    strategy = db.query(ControlStrategy).filter(ControlStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return ResponseModel(data=StrategyResponse.model_validate(strategy))


@router.put("/{strategy_id}", response_model=ResponseModel[StrategyResponse])
async def update_strategy(
    request: Request,
    strategy_id: int,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update control strategy."""
    strategy = db.query(ControlStrategy).filter(ControlStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    update_data = strategy_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(strategy, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="strategy",
        detail=f"Updated strategy: {strategy.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(strategy)
    
    logger.info(f"Strategy {strategy.name} updated by {current_user.username}")
    
    return ResponseModel(data=StrategyResponse.model_validate(strategy))


@router.delete("/{strategy_id}", response_model=ResponseModel)
async def delete_strategy(
    request: Request,
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete control strategy."""
    strategy = db.query(ControlStrategy).filter(ControlStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if strategy.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default strategy")
    
    name = strategy.name
    db.delete(strategy)
    
    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        module="strategy",
        detail=f"Deleted strategy: {name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Strategy {name} deleted by {current_user.username}")
    
    return ResponseModel(message="Strategy deleted successfully")


@router.post("/{strategy_id}/activate", response_model=ResponseModel)
async def activate_strategy(
    request: Request,
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a control strategy."""
    strategy = db.query(ControlStrategy).filter(ControlStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if not strategy.is_active:
        raise HTTPException(status_code=400, detail="Strategy is disabled")
    
    # Deactivate current default
    db.query(ControlStrategy).filter(ControlStrategy.is_default == True).update({"is_default": False})
    
    # Set new default
    strategy.is_default = True
    
    # Apply to engine
    engine = get_engine()
    engine.set_strategy(strategy.strategy_type, strategy.parameters)
    
    log = OperationLog(
        user_id=current_user.id,
        action="activate",
        module="strategy",
        detail=f"Activated strategy: {strategy.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Strategy {strategy.name} activated by {current_user.username}")
    
    return ResponseModel(message=f"Strategy '{strategy.name}' activated")
