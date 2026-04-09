# 工业园区微网控制系统

Industrial Park Microgrid Control System - 一个功能完整的模拟微网控制系统，用于工业园区电力系统的全面监控与管理。

## 快速开始

### 前置检查

确保以下文件存在：
- `docker-compose.yml` - Docker 编排文件
- `backend/` - 后端 Python 代码
- `frontend-admin/` - 前端 Vue 3 代码

### 启动服务

```bash
# 启动所有服务
docker-compose up --build -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 本地开发（不使用 Docker）

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend-admin
npm install
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pip install -r requirements.txt
pytest

# 前端测试
cd frontend-admin
npm install
npm run test
```

## Services

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | http://localhost:8081 | 前端管理界面 |
| Backend API | http://localhost:8000 | 后端 API 服务 |
| MySQL | localhost:3306 | 数据库服务 |
| Redis | localhost:6379 | 缓存服务 |

## 测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| operator | operator123 | 操作员 |

## 题目内容

请基于python设计一个功能完整、界面友好的模拟微网控制系统，用于对工业园区电力系统进行全面监控与管理。该系统需集成以下核心组件与功能：

### 1. 能源生产模块
- 光伏系统模拟（包含光照强度、温度等环境参数影响）
- 风力发电系统模拟（包含风速、风向等参数影响）
- 可配置的发电容量与效率参数

### 2. 储能系统模块
- 电池储能系统模拟（SOC状态、充放电效率、充放电速率限制）
- 储能调度策略配置界面

### 3. 负载系统模块
- 多种类型常规负载模拟（办公负载、生产负载、照明负载等）
- 冲击性负载模拟（包含闪充充电桩系统，需模拟短时高功率特性）
- 负载优先级与分类管理功能

### 4. 核心功能模块
- 能源管理系统：优化能源分配，实现多能互补
- 精细化负载管理：按优先级、时段、电价等因素智能控制负载
- 电力系统控制策略：提供多种预设控制模式与自定义策略配置
- 先进控制算法实现：包含但不限于PID控制、模型预测控制等
- 电网调度功能：与上级电网协调互动，支持并网/离网模式切换
- 余电上网管理：符合电网标准的并网控制与计量
- 实时监测系统：关键节点电压、电流、功率等电参数监测
- 电力系统平衡控制：实时维持电压稳定（±5%额定值）、频率稳定（50Hz±0.2Hz）、相角稳定

### 5. UI界面要求
- 直观的电力系统拓扑图显示
- 实时数据仪表盘（发电量、负荷、储能状态等关键指标）
- 趋势图表与历史数据分析功能
- 告警与事件记录系统
- 用户权限管理与操作日志
- 响应式设计，支持多终端访问

---

## 系统架构

### 技术栈
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + MySQL 8.0
- **Frontend**: Vue 3 + Vite + Element Plus + ECharts + Pinia
- **实时通信**: WebSocket
- **控制算法**: NumPy + SciPy (PID, MPC)

### 架构设计

#### 仿真引擎与 WebSocket 解耦

系统采用**后台独立仿真**架构，确保工业级可靠性：

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  Lifespan Manager                                           │
│  ├── 启动时: asyncio.create_task(background_simulation)    │
│  └── 关闭时: 取消后台任务                                    │
├─────────────────────────────────────────────────────────────┤
│  Background Simulation Loop (独立运行)                       │
│  ├── 每秒执行 engine.simulate_step()                        │
│  ├── 广播状态到所有 WebSocket 客户端                         │
│  └── 检测告警并广播                                          │
├─────────────────────────────────────────────────────────────┤
│  WebSocket Endpoints (仅负责连接管理)                        │
│  ├── /ws/realtime - 接收状态广播，处理客户端命令             │
│  └── /ws/alarm - 接收告警广播                                │
└─────────────────────────────────────────────────────────────┘
```

**设计优势**：
- ✅ **无客户端依赖**: 仿真引擎在后台持续运行，即使无 WebSocket 连接
- ✅ **多用户安全**: 多个客户端连接不会导致仿真重复执行
- ✅ **线程安全**: MicrogridEngine 使用锁保护状态访问
- ✅ **工业级架构**: 控制回路独立于用户界面，符合真实产品形态

### 核心模块

#### 仿真引擎
- `PVSimulator`: 光伏系统仿真，考虑光照强度、温度影响
- `WindSimulator`: 风力发电仿真，包含功率曲线模型
- `BatterySimulator`: 储能系统仿真，SOC管理、充放电效率
- `LoadSimulator`: 负载仿真，支持多种负载类型和冲击性负载
- `GridSimulator`: 电网接口仿真，并网/离网模式

#### 控制算法
- `PIDController`: PID控制器，用于电压/频率稳定
- `MPCController`: 模型预测控制，优化功率调度
- `EnergyManagementSystem`: 能源管理系统，多策略支持

#### 控制策略
- **经济优先模式**: 根据电价时段优化储能充放电
- **绿色优先模式**: 最大化可再生能源利用率
- **稳定优先模式**: 优先保证电压和频率稳定（含相角控制）

#### 电力系统平衡控制
- **电压稳定**: PID 控制器维持 ±5% 额定值 (361V-399V)
- **频率稳定**: PID 控制器维持 50Hz±0.2Hz
- **相角稳定**: PLL 锁相环 + PID 相角控制器

### API 接口

系统提供完整的 RESTful API：
- `/api/auth/*` - 认证接口
- `/api/users/*` - 用户管理
- `/api/pv/*` - 光伏系统
- `/api/wind/*` - 风力发电
- `/api/battery/*` - 储能系统
- `/api/loads/*` - 负载管理
- `/api/grid/*` - 电网管理
- `/api/strategies/*` - 控制策略
- `/api/alarms/*` - 告警管理
- `/api/analytics/*` - 数据分析
- `/ws/realtime` - 实时数据 WebSocket

## 功能特性

### 后端仿真引擎
✅ 光伏系统模拟（光照、温度影响） - `backend/app/simulation/pv_simulator.py`  
✅ 风力发电系统模拟（风速、功率曲线） - `backend/app/simulation/wind_simulator.py`  
✅ 储能系统模拟（SOC、充放电控制） - `backend/app/simulation/battery_simulator.py`  
✅ 多类型负载模拟（含闪充充电桩） - `backend/app/simulation/load_simulator.py`  
✅ 能源管理系统（多能互补优化） - `backend/app/simulation/microgrid_engine.py`  
✅ PID/MPC 控制算法 - `backend/app/simulation/control_algorithms.py`  
✅ 并网/离网模式切换 - `backend/app/simulation/grid_simulator.py`  
✅ 电压/频率/相角稳定控制 - `backend/app/simulation/control_algorithms.py`  
✅ 后台独立仿真循环 - `backend/app/main.py` (asyncio.create_task)

### 前端 UI 界面 (Vue 3 + Element Plus + ECharts)
✅ 实时数据仪表盘 - `frontend-admin/src/views/Dashboard.vue`  
✅ 系统拓扑图显示 (Vue Flow) - `frontend-admin/src/views/Topology.vue`  
✅ 趋势图表分析 - `frontend-admin/src/views/Analytics.vue`  
✅ 光伏系统监控 - `frontend-admin/src/views/PVSystem.vue`  
✅ 风力发电监控 - `frontend-admin/src/views/WindSystem.vue`  
✅ 储能系统管理 - `frontend-admin/src/views/BatterySystem.vue`  
✅ 负载管理界面 - `frontend-admin/src/views/LoadManagement.vue`  
✅ 电网管理界面 - `frontend-admin/src/views/GridManagement.vue`  
✅ 控制策略配置 - `frontend-admin/src/views/Strategy.vue`  
✅ 告警管理系统 - `frontend-admin/src/views/Alarm.vue`  
✅ 用户权限管理 - `frontend-admin/src/views/Users.vue`  
✅ 操作日志记录 - `frontend-admin/src/views/Logs.vue`  
✅ 系统设置 - `frontend-admin/src/views/Settings.vue`  
✅ WebSocket 实时通信 - `frontend-admin/src/composables/useWebSocket.js`  
✅ 响应式界面设计

## 项目结构

```
.
├── backend/                 # 后端服务 (Python FastAPI)
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   ├── simulation/     # 仿真引擎
│   │   └── main.py         # 入口文件
│   ├── tests/              # 后端测试
│   ├── Dockerfile          # 后端 Docker 配置
│   ├── requirements.txt    # Python 依赖
│   └── schema.sql          # 数据库初始化脚本
├── frontend-admin/          # 前端应用 (Vue 3 + Element Plus)
│   ├── src/
│   │   ├── api/            # API 调用
│   │   ├── composables/    # 组合式函数
│   │   ├── layouts/        # 布局组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── styles/         # 样式文件
│   │   ├── views/          # 页面组件
│   │   ├── __tests__/      # 前端测试
│   │   ├── App.vue         # 根组件
│   │   └── main.js         # 入口文件
│   ├── index.html          # HTML 入口
│   ├── Dockerfile          # 前端 Docker 配置
│   ├── nginx.conf          # Nginx 配置
│   ├── package.json        # Node.js 依赖
│   └── vite.config.js      # Vite 构建配置
├── docs/                    # 文档
│   └── project_design.md   # 设计文档
├── docker-compose.yml       # Docker Compose 编排文件 (启动入口)
└── README.md                # 项目说明
```

> **注意**: 前端代码位于 `frontend-admin/` 目录，Docker Compose 会自动构建并部署到 8081 端口。

## License

MIT
