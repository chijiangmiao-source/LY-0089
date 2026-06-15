# 商场儿童推车滞留回收与跨楼层调拨系统

## 技术栈

- **后端**: Python 3.10+、Django 4.2、Django Ninja、PostgreSQL
- **前端**: Vue 3、TypeScript、Vuetify 3、Pinia、Vue Router、Axios、ECharts

## 项目结构

```
cj89/
├── backend/                    # Django 后端项目
│   ├── core/                   # 核心配置（settings、urls、api入口）
│   ├── users/                  # 用户与认证模块
│   ├── stations/               # 楼层服务点管理
│   ├── carts/                  # 推车档案
│   ├── rentals/                # 借还登记
│   ├── transfers/              # 跨点调拨
│   ├── stranded/               # 滞留上报
│   ├── dashboard/              # 调度看板统计
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/                   # Vue 3 前端项目
    ├── src/
    │   ├── api/                # Axios 封装
    │   ├── layouts/            # 布局组件
    │   ├── plugins/            # Vuetify 插件配置
    │   ├── router/             # 路由配置
    │   ├── stores/             # Pinia 状态管理
    │   ├── styles/             # 全局样式
    │   ├── views/              # 页面组件
    │   ├── App.vue
    │   └── main.ts
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

## 核心功能

| 模块 | 功能说明 |
|------|----------|
| 登录 | JWT 身份认证，区分管理员/工作人员角色 |
| 服务点管理 | 各楼层服务点 CRUD，配置安全保有量 |
| 推车档案 | 推车编号、车型、状态、所属服务点、清洁时间管理 |
| 借出登记 | 校验推车状态和手机号逾期情况，生成借用单 |
| 归还登记 | 同点归还直接投放，跨点归还进入复位检查 |
| 滞留上报 | 上报推车滞留位置，跟踪回收处理流程 |
| 跨点调拨 | 创建调拨单，支持优先级，推车在调拨途中不可借还 |
| 清洁复位 | 处理清洁中和复位检查中的推车 |
| 调度看板 | 总览、楼层缺车、滞留时长分布、调拨完成率、逾期列表 |

## 业务约束

1. **未归还推车不能再次借出**：推车状态必须为 `available` 才能借出
2. **跨点归还必须复位检查**：归还点 ≠ 借出点时，推车进入 `reset_check` 状态
3. **调拨中推车不可操作**：推车状态为 `transferring` 时不能借出或归还入库
4. **逾期手机号限制借车**：同一手机号存在 `overdue` 记录时拒绝借车
5. **低于安全保有量优先调拨**：看板和调拨接口自动计算缺车服务点并推荐源站

## 数据模型关键字段

### 推车 (Cart)
- `cart_no`: 推车编号（唯一）
- `station`: 所属服务点
- `cart_type`: 车型 (standard/large)
- `status`: 状态 (available/borrowed/stranded/transferring/cleaning/reset_check)
- `last_clean_time`: 最近清洁时间

### 借还记录 (RentalRecord)
- `rental_no`: 借用单号
- `user_phone`: 借用人手机号
- `borrow_time` / `return_time`: 借还时间
- `borrow_station` / `return_station`: 借还服务点
- `stage`: 环节 (borrowing/returned/overdue)

## 后端启动

```bash
cd backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库（先创建 PostgreSQL 数据库）
copy .env.example .env
# 编辑 .env 填写数据库连接信息

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 创建超级管理员
python manage.py createsuperuser

# 6. 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

API 文档地址: http://localhost:8000/api/docs

## 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install
# 或 yarn install / pnpm install

# 2. 启动开发服务器
npm run dev
```

访问地址: http://localhost:3000

## API 端点列表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/login` | 登录获取 Token | 否 |
| GET | `/api/auth/me` | 获取当前用户信息 | 是 |
| GET/POST/PUT/DELETE | `/api/stations` | 服务点 CRUD | 是 |
| GET/POST/PUT/DELETE | `/api/carts` | 推车 CRUD | 是 |
| POST | `/api/carts/{id}/clean` | 推车清洁完成 | 是 |
| GET | `/api/rentals` | 借还记录列表 | 是 |
| POST | `/api/rentals/borrow` | 借出登记 | 是 |
| POST | `/api/rentals/return` | 归还登记 | 是 |
| GET | `/api/rentals/check-phone/{phone}` | 检查手机号可用性 | 是 |
| GET/POST | `/api/transfers` | 调拨单列表/创建 | 是 |
| PUT | `/api/transfers/{id}/start` | 开始调拨 | 是 |
| PUT | `/api/transfers/{id}/complete` | 完成调拨 | 是 |
| PUT | `/api/transfers/{id}/cancel` | 取消调拨 | 是 |
| GET | `/api/transfers/priority-queue` | 优先调拨队列 | 是 |
| GET/POST | `/api/stranded` | 滞留记录列表/上报 | 是 |
| PUT | `/api/stranded/{id}/recycle` | 开始回收 | 是 |
| PUT | `/api/stranded/{id}/complete` | 完成回收 | 是 |
| GET | `/api/dashboard/overview` | 总览统计 | 是 |
| GET | `/api/dashboard/floor-shortage` | 楼层缺车情况 | 是 |
| GET | `/api/dashboard/stranded-distribution` | 滞留时长分布 | 是 |
| GET | `/api/dashboard/transfer-rate` | 调拨完成率 | 是 |
| GET | `/api/dashboard/overdue-list` | 逾期未还列表 | 是 |
