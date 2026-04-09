"""Database initialization."""
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.pv import PVSystem
from app.models.wind import WindSystem
from app.models.battery import BatterySystem
from app.models.load import Load
from app.models.grid import GridConnection
from app.models.alarm import Alarm, AlarmHistory
from app.models.strategy import ControlStrategy
from app.models.config import SystemConfig
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_db(db: Session) -> None:
    """Initialize database with default data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Check if admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin)
        logger.info("Admin user created")
    
    # Check if operator user exists
    operator = db.query(User).filter(User.username == "operator").first()
    if not operator:
        operator = User(
            username="operator",
            password_hash=get_password_hash("operator123"),
            role="operator",
            is_active=True
        )
        db.add(operator)
        logger.info("Operator user created")
    
    # Initialize PV System
    pv = db.query(PVSystem).first()
    if not pv:
        pv = PVSystem(
            name="光伏阵列-1",
            capacity_kw=500.0,
            efficiency=0.18,
            panel_area=2800.0,
            is_active=True
        )
        db.add(pv)
        logger.info("PV system created")
    
    # Initialize Wind System
    wind = db.query(WindSystem).first()
    if not wind:
        wind = WindSystem(
            name="风力发电机-1",
            capacity_kw=300.0,
            cut_in_speed=3.0,
            rated_speed=12.0,
            cut_out_speed=25.0,
            is_active=True
        )
        db.add(wind)
        logger.info("Wind system created")
    
    # Initialize Battery System
    battery = db.query(BatterySystem).first()
    if not battery:
        battery = BatterySystem(
            name="储能电池组-1",
            capacity_kwh=1000.0,
            max_charge_rate=200.0,
            max_discharge_rate=200.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.1,
            max_soc=0.9,
            is_active=True
        )
        db.add(battery)
        logger.info("Battery system created")
    
    # Initialize Loads
    loads = db.query(Load).count()
    if loads == 0:
        default_loads = [
            Load(name="办公楼负载", load_type="office", rated_power=150.0, priority=2, is_controllable=True, is_active=True),
            Load(name="生产车间-1", load_type="production", rated_power=300.0, priority=1, is_controllable=True, is_active=True),
            Load(name="生产车间-2", load_type="production", rated_power=250.0, priority=1, is_controllable=True, is_active=True),
            Load(name="照明系统", load_type="lighting", rated_power=50.0, priority=3, is_controllable=True, is_active=True),
            Load(name="空调系统", load_type="hvac", rated_power=200.0, priority=2, is_controllable=True, is_active=True),
            Load(name="闪充充电桩-1", load_type="ev_charger", rated_power=120.0, priority=4, is_controllable=True, is_active=True),
            Load(name="闪充充电桩-2", load_type="ev_charger", rated_power=120.0, priority=4, is_controllable=True, is_active=True),
        ]
        for load in default_loads:
            db.add(load)
        logger.info("Default loads created")
    
    # Initialize Grid Connection
    grid = db.query(GridConnection).first()
    if not grid:
        grid = GridConnection(
            name="主电网接口",
            max_import=800.0,
            max_export=500.0,
            connection_type="bidirectional",
            is_connected=True
        )
        db.add(grid)
        logger.info("Grid connection created")
    
    # Initialize Control Strategies
    strategies = db.query(ControlStrategy).count()
    if strategies == 0:
        default_strategies = [
            ControlStrategy(
                name="经济优先模式",
                strategy_type="economic",
                parameters={
                    "peak_price": 1.2,
                    "valley_price": 0.4,
                    "flat_price": 0.8,
                    "peak_hours": [10, 11, 12, 13, 14, 15, 18, 19, 20, 21],
                    "valley_hours": [0, 1, 2, 3, 4, 5, 6, 7],
                    "battery_threshold": 0.3
                },
                is_default=True,
                is_active=True
            ),
            ControlStrategy(
                name="绿色优先模式",
                strategy_type="green",
                parameters={
                    "renewable_priority": True,
                    "grid_import_limit": 0.2,
                    "battery_reserve": 0.2
                },
                is_default=False,
                is_active=True
            ),
            ControlStrategy(
                name="稳定优先模式",
                strategy_type="stability",
                parameters={
                    "voltage_tolerance": 0.05,
                    "frequency_tolerance": 0.004,
                    "battery_reserve": 0.3,
                    "load_shedding_enabled": True
                },
                is_default=False,
                is_active=True
            ),
        ]
        for strategy in default_strategies:
            db.add(strategy)
        logger.info("Control strategies created")
    
    # Initialize System Configs
    configs = db.query(SystemConfig).count()
    if configs == 0:
        default_configs = [
            SystemConfig(config_key="voltage_nominal", config_value="380", config_type="float", description="额定电压(V)"),
            SystemConfig(config_key="frequency_nominal", config_value="50", config_type="float", description="额定频率(Hz)"),
            SystemConfig(config_key="voltage_tolerance", config_value="0.05", config_type="float", description="电压容差(±%)"),
            SystemConfig(config_key="frequency_tolerance", config_value="0.004", config_type="float", description="频率容差(±Hz)"),
            SystemConfig(config_key="simulation_speed", config_value="1.0", config_type="float", description="仿真速度倍率"),
            SystemConfig(config_key="data_retention_days", config_value="30", config_type="int", description="数据保留天数"),
        ]
        for config in default_configs:
            db.add(config)
        logger.info("System configs created")
    
    # Initialize Alarms
    alarms = db.query(Alarm).count()
    if alarms == 0:
        default_alarms = [
            Alarm(alarm_code="ALM001", alarm_name="电压过高", severity="warning", module="grid", condition_expr="voltage > 399", is_active=True),
            Alarm(alarm_code="ALM002", alarm_name="电压过低", severity="warning", module="grid", condition_expr="voltage < 361", is_active=True),
            Alarm(alarm_code="ALM003", alarm_name="频率异常", severity="critical", module="grid", condition_expr="abs(frequency - 50) > 0.2", is_active=True),
            Alarm(alarm_code="ALM004", alarm_name="储能SOC过低", severity="warning", module="battery", condition_expr="soc < 0.15", is_active=True),
            Alarm(alarm_code="ALM005", alarm_name="储能SOC过高", severity="warning", module="battery", condition_expr="soc > 0.95", is_active=True),
            Alarm(alarm_code="ALM006", alarm_name="光伏功率异常", severity="info", module="pv", condition_expr="power < 0", is_active=True),
            Alarm(alarm_code="ALM007", alarm_name="负载过载", severity="critical", module="load", condition_expr="power > rated_power * 1.1", is_active=True),
        ]
        for alarm in default_alarms:
            db.add(alarm)
        db.flush()  # Flush to get alarm IDs
        logger.info("Alarms created")
    
    # Initialize Alarm History with sample data (if empty)
    alarm_history_count = db.query(AlarmHistory).count()
    if alarm_history_count == 0:
        from datetime import datetime, timedelta
        import random
        
        alarm_list = db.query(Alarm).all()
        if alarm_list:
            alarm_history_data = []
            now = datetime.now()
            
            # Generate 50 historical alarm records over the past 7 days
            for i in range(50):
                alarm = random.choice(alarm_list)
                hours_ago = random.randint(1, 168)  # 1-168 hours (7 days)
                triggered_time = now - timedelta(hours=hours_ago)
                
                # Randomly determine status
                status_choice = random.random()
                if status_choice < 0.6:
                    status = "cleared"
                    ack_time = triggered_time + timedelta(minutes=random.randint(5, 60))
                    clear_time = ack_time + timedelta(minutes=random.randint(10, 120))
                elif status_choice < 0.85:
                    status = "acknowledged"
                    ack_time = triggered_time + timedelta(minutes=random.randint(5, 60))
                    clear_time = None
                else:
                    status = "triggered"
                    ack_time = None
                    clear_time = None
                
                history = AlarmHistory(
                    alarm_id=alarm.id,
                    status=status,
                    message=f"系统检测到{alarm.alarm_name}",
                    acknowledged_by=1 if ack_time else None,
                    triggered_at=triggered_time,
                    acknowledged_at=ack_time,
                    cleared_at=clear_time
                )
                alarm_history_data.append(history)
            
            for history in alarm_history_data:
                db.add(history)
            logger.info("Alarm history created")
    
    db.commit()
    logger.info("Database initialization completed")
