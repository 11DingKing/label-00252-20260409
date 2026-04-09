-- Microgrid Control System Database Schema

CREATE DATABASE IF NOT EXISTS microgrid CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE microgrid;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB;

-- Operation logs table
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    module VARCHAR(50) NOT NULL,
    detail TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_created_at (created_at),
    INDEX idx_module (module)
) ENGINE=InnoDB;

-- PV systems table
CREATE TABLE IF NOT EXISTS pv_systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity_kw FLOAT NOT NULL,
    efficiency FLOAT NOT NULL DEFAULT 0.18,
    panel_area FLOAT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- PV data table
CREATE TABLE IF NOT EXISTS pv_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pv_id INT NOT NULL,
    irradiance FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    power_output FLOAT NOT NULL,
    voltage FLOAT NOT NULL,
    current FLOAT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pv_id) REFERENCES pv_systems(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Wind systems table
CREATE TABLE IF NOT EXISTS wind_systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity_kw FLOAT NOT NULL,
    cut_in_speed FLOAT NOT NULL DEFAULT 3.0,
    rated_speed FLOAT NOT NULL DEFAULT 12.0,
    cut_out_speed FLOAT NOT NULL DEFAULT 25.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Wind data table
CREATE TABLE IF NOT EXISTS wind_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wind_id INT NOT NULL,
    wind_speed FLOAT NOT NULL,
    wind_direction FLOAT NOT NULL,
    power_output FLOAT NOT NULL,
    rotor_speed FLOAT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wind_id) REFERENCES wind_systems(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Battery systems table
CREATE TABLE IF NOT EXISTS battery_systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity_kwh FLOAT NOT NULL,
    max_charge_rate FLOAT NOT NULL,
    max_discharge_rate FLOAT NOT NULL,
    charge_efficiency FLOAT NOT NULL DEFAULT 0.95,
    discharge_efficiency FLOAT NOT NULL DEFAULT 0.95,
    min_soc FLOAT NOT NULL DEFAULT 0.1,
    max_soc FLOAT NOT NULL DEFAULT 0.9,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Battery data table
CREATE TABLE IF NOT EXISTS battery_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    battery_id INT NOT NULL,
    soc FLOAT NOT NULL,
    power FLOAT NOT NULL,
    voltage FLOAT NOT NULL,
    current FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (battery_id) REFERENCES battery_systems(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Loads table
CREATE TABLE IF NOT EXISTS loads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    load_type VARCHAR(50) NOT NULL,
    rated_power FLOAT NOT NULL,
    priority INT NOT NULL DEFAULT 3,
    is_controllable BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Load data table
CREATE TABLE IF NOT EXISTS load_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    load_id INT NOT NULL,
    power FLOAT NOT NULL,
    voltage FLOAT NOT NULL,
    current FLOAT NOT NULL,
    power_factor FLOAT NOT NULL DEFAULT 0.95,
    is_on BOOLEAN NOT NULL DEFAULT TRUE,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (load_id) REFERENCES loads(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Grid connections table
CREATE TABLE IF NOT EXISTS grid_connections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    max_import FLOAT NOT NULL,
    max_export FLOAT NOT NULL,
    connection_type VARCHAR(50) NOT NULL DEFAULT 'bidirectional',
    is_connected BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Grid data table
CREATE TABLE IF NOT EXISTS grid_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grid_id INT NOT NULL,
    power FLOAT NOT NULL,
    voltage FLOAT NOT NULL,
    frequency FLOAT NOT NULL,
    phase_angle FLOAT NOT NULL DEFAULT 0,
    mode VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grid_id) REFERENCES grid_connections(id) ON DELETE CASCADE,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Alarms table
CREATE TABLE IF NOT EXISTS alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alarm_code VARCHAR(20) NOT NULL UNIQUE,
    alarm_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    module VARCHAR(50) NOT NULL,
    condition_expr VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Alarm history table
CREATE TABLE IF NOT EXISTS alarm_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alarm_id INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    acknowledged_by INT,
    triggered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    cleared_at DATETIME,
    FOREIGN KEY (alarm_id) REFERENCES alarms(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_triggered_at (triggered_at),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- Control strategies table
CREATE TABLE IF NOT EXISTS control_strategies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSON NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- System configs table
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description VARCHAR(255),
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Config history table
CREATE TABLE IF NOT EXISTS config_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_id INT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_by INT,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES system_configs(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;


-- System snapshots table for historical data
CREATE TABLE IF NOT EXISTS system_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    pv_power FLOAT NOT NULL DEFAULT 0,
    wind_power FLOAT NOT NULL DEFAULT 0,
    total_generation FLOAT NOT NULL DEFAULT 0,
    total_load FLOAT NOT NULL DEFAULT 0,
    battery_power FLOAT NOT NULL DEFAULT 0,
    battery_soc FLOAT NOT NULL DEFAULT 0.5,
    grid_power FLOAT NOT NULL DEFAULT 0,
    grid_voltage FLOAT NOT NULL DEFAULT 380,
    grid_frequency FLOAT NOT NULL DEFAULT 50,
    grid_mode VARCHAR(20) NOT NULL DEFAULT 'grid_connected',
    renewable_ratio FLOAT NOT NULL DEFAULT 0,
    self_sufficiency FLOAT NOT NULL DEFAULT 0,
    strategy VARCHAR(50) NOT NULL DEFAULT 'economic',
    INDEX idx_snapshot_timestamp (timestamp)
) ENGINE=InnoDB;

-- Energy aggregations table for reporting
CREATE TABLE IF NOT EXISTS energy_aggregations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    period_type VARCHAR(10) NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    pv_generation FLOAT NOT NULL DEFAULT 0,
    wind_generation FLOAT NOT NULL DEFAULT 0,
    total_generation FLOAT NOT NULL DEFAULT 0,
    total_consumption FLOAT NOT NULL DEFAULT 0,
    grid_import FLOAT NOT NULL DEFAULT 0,
    grid_export FLOAT NOT NULL DEFAULT 0,
    battery_charge FLOAT NOT NULL DEFAULT 0,
    battery_discharge FLOAT NOT NULL DEFAULT 0,
    peak_generation FLOAT NOT NULL DEFAULT 0,
    peak_load FLOAT NOT NULL DEFAULT 0,
    peak_grid_import FLOAT NOT NULL DEFAULT 0,
    avg_load FLOAT NOT NULL DEFAULT 0,
    avg_renewable_ratio FLOAT NOT NULL DEFAULT 0,
    avg_self_sufficiency FLOAT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_aggregation_period (period_type, period_start)
) ENGINE=InnoDB;
