"""FastAPI application entry point."""
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import (
    AppException, app_exception_handler, http_exception_handler,
    validation_exception_handler, sqlalchemy_exception_handler,
    general_exception_handler
)
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.init_db import init_db
from app.simulation.microgrid_engine import engine as microgrid_engine
from app.services.data_persistence import persistence_service

from app.api import auth, users, pv, wind, battery, load, grid, strategy, alarm, analytics, config, logs, websocket

logger = get_logger(__name__)

# Background simulation task reference
_simulation_task: asyncio.Task = None
_aggregation_task: asyncio.Task = None


async def background_simulation_loop():
    """
    Background task that runs the simulation independently of WebSocket connections.
    This ensures the microgrid simulation continues running even when no clients are connected.
    Also handles data persistence to database.
    """
    logger.info("Background simulation loop started")
    
    while True:
        try:
            now = datetime.now()
            
            # Run simulation step
            state = microgrid_engine.simulate_step(now)
            
            # Persist data to database at configured interval (every minute)
            if persistence_service.should_persist(now):
                db = SessionLocal()
                try:
                    persistence_service.persist_snapshot(state, db)
                except Exception as e:
                    logger.error(f"Failed to persist data: {e}")
                finally:
                    db.close()
            
            # Process and persist pending alarms
            pending_alarms = microgrid_engine.get_pending_alarms()
            if pending_alarms:
                db = SessionLocal()
                try:
                    await _persist_alarms(pending_alarms, db)
                    # Broadcast alarms to WebSocket clients
                    for alarm in pending_alarms:
                        await websocket.broadcast_alarm(alarm)
                except Exception as e:
                    logger.error(f"Failed to persist alarms: {e}")
                finally:
                    db.close()
            
            # Broadcast state to all connected WebSocket clients
            await websocket.broadcast_state(state)
            
            # Wait for next simulation interval (1 second)
            await asyncio.sleep(1.0)
            
        except asyncio.CancelledError:
            logger.info("Background simulation loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background simulation: {e}")
            await asyncio.sleep(1.0)  # Continue after error


async def _persist_alarms(alarms: list, db) -> None:
    """Persist alarms to database."""
    from app.models.alarm import Alarm, AlarmHistory
    
    for alarm_data in alarms:
        # Find or create alarm definition
        alarm = db.query(Alarm).filter(Alarm.alarm_code == alarm_data["alarm_code"]).first()
        
        if not alarm:
            # Create alarm definition if not exists
            alarm = Alarm(
                alarm_code=alarm_data["alarm_code"],
                alarm_name=alarm_data["alarm_name"],
                severity=alarm_data["severity"],
                module=alarm_data["module"],
                condition_expr="auto_generated",
                is_active=True
            )
            db.add(alarm)
            db.flush()
        
        # Check if there's already an active alarm of this type
        existing = db.query(AlarmHistory).filter(
            AlarmHistory.alarm_id == alarm.id,
            AlarmHistory.status.in_(["triggered", "acknowledged"])
        ).first()
        
        if not existing:
            # Create alarm history entry
            history = AlarmHistory(
                alarm_id=alarm.id,
                status="triggered",
                message=alarm_data.get("message", "")
            )
            db.add(history)
    
    db.commit()


async def background_aggregation_loop():
    """
    Background task that computes hourly and daily aggregations.
    Runs every hour to compute aggregations for reporting.
    """
    logger.info("Background aggregation loop started")
    
    while True:
        try:
            # Wait until the next hour boundary
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            wait_seconds = (next_hour - now).total_seconds()
            
            await asyncio.sleep(wait_seconds)
            
            # Compute hourly aggregation for the previous hour
            db = SessionLocal()
            try:
                prev_hour = next_hour - timedelta(hours=1)
                persistence_service.compute_hourly_aggregation(prev_hour, db)
                
                # If it's midnight, compute daily aggregation for yesterday
                if next_hour.hour == 0:
                    yesterday = (next_hour - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    persistence_service.compute_daily_aggregation(yesterday, db)
                    
            except Exception as e:
                logger.error(f"Failed to compute aggregation: {e}")
            finally:
                db.close()
                
        except asyncio.CancelledError:
            logger.info("Background aggregation loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in aggregation loop: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _simulation_task, _aggregation_task
    
    logger.info("Starting Microgrid Control System...")
    
    # Create database tables (including new analytics tables)
    Base.metadata.create_all(bind=engine)
    
    # Initialize database with default data
    db = SessionLocal()
    try:
        init_db(db)
        
        # Initialize simulation engine from database
        microgrid_engine.initialize_from_db(db)
        
        logger.info("Application started successfully")
    finally:
        db.close()
    
    # Start background simulation task
    _simulation_task = asyncio.create_task(background_simulation_loop())
    logger.info("Background simulation task started")
    
    # Start background aggregation task
    _aggregation_task = asyncio.create_task(background_aggregation_loop())
    logger.info("Background aggregation task started")
    
    yield
    
    # Stop background tasks
    if _simulation_task:
        _simulation_task.cancel()
        try:
            await _simulation_task
        except asyncio.CancelledError:
            pass
        logger.info("Background simulation task stopped")
    
    if _aggregation_task:
        _aggregation_task.cancel()
        try:
            await _aggregation_task
        except asyncio.CancelledError:
            pass
        logger.info("Background aggregation task stopped")
    
    logger.info("Shutting down Microgrid Control System...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Industrial Park Microgrid Control System API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pv.router)
app.include_router(wind.router)
app.include_router(battery.router)
app.include_router(load.router)
app.include_router(grid.router)
app.include_router(strategy.router)
app.include_router(alarm.router)
app.include_router(analytics.router)
app.include_router(config.router)
app.include_router(logs.router)
app.include_router(websocket.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
