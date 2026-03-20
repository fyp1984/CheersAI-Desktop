# CheersAI SQLite 数据库

这是 CheersAI 项目的 SQLite 数据库设计和初始化脚本。

## 📋 数据库结构

### 核心数据表

1. **users** - 用户表
   - 存储用户基本信息、认证信息和状态
   - 支持邮箱和手机号登录
   - 包含邮箱和手机验证状态

2. **products** - 产品表
   - 管理 CheersAI 的各个产品
   - 包含产品版本、下载链接和配置信息

3. **membership_plans** - 会员计划表
   - 定义不同的会员等级（Free、Pro、Team、Enterprise）
   - 包含价格、功能和限制配置

4. **subscriptions** - 用户订阅表
   - 管理用户的会员订阅
   - 支持自动续费和订阅状态跟踪

5. **audit_logs** - 审计日志表
   - 记录系统中的所有重要操作
   - 包含操作前后数据对比

6. **feedbacks** - 用户反馈表
   - 收集用户的 Bug 报告、功能请求等
   - 支持优先级和状态管理

7. **announcements** - 公告表
   - 发布系统公告和更新通知
   - 支持定时发布和过期管理

### 视图

- **v_active_subscriptions** - 活跃订阅视图
- **v_feedback_summary** - 反馈摘要视图
- **v_published_announcements** - 已发布公告视图

### 触发器

自动更新所有表的 `updated_at` 字段。

## 🚀 快速开始

### 1. 初始化数据库

使用 Python 脚本初始化：

```bash
cd database
python init_db.py
```

或手动使用 SQLite：

```bash
sqlite3 cheersai.db < init_sqlite.sql
```

### 2. 连接数据库

```bash
sqlite3 cheersai.db
```

### 3. 查看表结构

```sql
.tables
.schema users
```

## 📊 预置数据

数据库初始化时会自动创建以下会员计划：

| 计划 | 月费 | 年费 | Agent 数量 | 知识库数量 | 每日 API 调用 |
|------|------|------|-----------|-----------|--------------|
| Free | ¥0 | ¥0 | 3 | 1 | 100 |
| Pro | ¥29 | ¥299 | 20 | 10 | 1,000 |
| Team | ¥99 | ¥999 | 100 | 50 | 5,000 |
| Enterprise | 定制 | 定制 | 无限 | 无限 | 无限 |

## 💡 使用示例

### 创建用户

```sql
INSERT INTO users (email, username, password_hash, nickname)
VALUES ('user@example.com', 'johndoe', 'hashed_password', 'John Doe');
```

### 创建订阅

```sql
INSERT INTO subscriptions (user_id, plan_code, start_date, end_date, status)
VALUES (
    (SELECT id FROM users WHERE email = 'user@example.com'),
    'pro',
    date('now'),
    date('now', '+1 year'),
    'active'
);
```

### 查询活跃订阅

```sql
SELECT * FROM v_active_subscriptions;
```

### 创建反馈

```sql
INSERT INTO feedbacks (user_id, type, title, content, status, priority)
VALUES (
    (SELECT id FROM users WHERE email = 'user@example.com'),
    'bug',
    '登录问题',
    '无法使用邮箱登录',
    'pending',
    'high'
);
```

### 创建公告

```sql
INSERT INTO announcements (type, title, content, status, created_by, publish_at)
VALUES (
    'update',
    '系统维护通知',
    '系统将于今晚 22:00 进行维护',
    'published',
    (SELECT id FROM users WHERE email = 'admin@example.com'),
    datetime('now')
);
```

### 记录审计日志

```sql
INSERT INTO audit_logs (log_type, action, operator_id, operator_name, target_type, target_id, result)
VALUES (
    'user',
    'login',
    (SELECT id FROM users WHERE email = 'user@example.com'),
    'johndoe',
    'session',
    'session_id_123',
    'success'
);
```

## 🔍 常用查询

### 查看用户的订阅历史

```sql
SELECT 
    u.email,
    s.plan_code,
    s.status,
    s.start_date,
    s.end_date
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.email = 'user@example.com'
ORDER BY s.created_at DESC;
```

### 查看待处理的反馈

```sql
SELECT 
    f.title,
    f.type,
    f.priority,
    u.username,
    f.created_at
FROM feedbacks f
JOIN users u ON f.user_id = u.id
WHERE f.status = 'pending'
ORDER BY 
    CASE f.priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    f.created_at;
```

### 统计会员分布

```sql
SELECT 
    mp.name,
    COUNT(s.id) as subscriber_count
FROM membership_plans mp
LEFT JOIN subscriptions s ON mp.code = s.plan_code AND s.status = 'active'
GROUP BY mp.code, mp.name
ORDER BY mp.sort_order;
```

## 🔧 维护

### 备份数据库

```bash
sqlite3 cheersai.db ".backup cheersai_backup.db"
```

### 导出数据

```bash
sqlite3 cheersai.db ".dump" > cheersai_dump.sql
```

### 优化数据库

```sql
VACUUM;
ANALYZE;
```

## 📝 注意事项

1. **UUID 生成**: SQLite 使用 `randomblob(16)` 生成 UUID，格式为 32 位十六进制字符串
2. **BOOLEAN 类型**: SQLite 使用 INTEGER (0/1) 表示布尔值
3. **JSON 字段**: 存储为 TEXT，需要在应用层进行 JSON 序列化/反序列化
4. **日期时间**: 使用 TEXT 类型存储 ISO 8601 格式的日期时间字符串
5. **外键约束**: 需要在连接时启用 `PRAGMA foreign_keys = ON;`

## 🔗 与 PostgreSQL 的差异

| 特性 | PostgreSQL | SQLite |
|------|-----------|--------|
| UUID | UUID 类型 + gen_random_uuid() | TEXT + randomblob(16) |
| BOOLEAN | BOOLEAN 类型 | INTEGER (0/1) |
| JSON | JSONB 类型 | TEXT (JSON 字符串) |
| ARRAY | ARRAY 类型 | TEXT (JSON 数组字符串) |
| TIMESTAMP | TIMESTAMP 类型 | TEXT (ISO 8601) |
| DECIMAL | DECIMAL 类型 | REAL |

## 📚 相关文档

- [SQLite 官方文档](https://www.sqlite.org/docs.html)
- [SQLite JSON 函数](https://www.sqlite.org/json1.html)
- [SQLite 日期时间函数](https://www.sqlite.org/lang_datefunc.html)
