# Secret — 敏感信息制品

## 目标

定义敏感信息——密码、密钥、证书、API Token。Secret 是环境与配置域的特殊制品，专门管理需要加密存储和访问控制的敏感数据。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `SEC-\d+` | 唯一标识符 |
| `name` | string | snake_case，≤ 80 字符 | **描述性** — 敏感信息名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 敏感信息类型 |
| `algorithm` | enum | 见下方 | 加密算法 |
| `rotation_policy` | RotationPolicy | | 轮换策略（可选） |
| `access_control_ids` | list\<ref\> | `PERM-\d+` | 访问控制权限（引用 [Permission](../governance/rbac/permission.md)） |

### type 枚举

| 值 | 含义 |
|----|------|
| `PASSWORD` | 密码 |
| `API_KEY` | API 密钥 |
| `CERTIFICATE` | 证书（公钥+私钥） |
| `TOKEN` | 访问令牌 |
| `DATABASE_URL` | 数据库连接字符串 |
| `ENCRYPTION_KEY` | 加密密钥 |

### algorithm 枚举

| 值 | 含义 |
|----|------|
| `AES256` | AES-256 加密 |
| `RSA2048` | RSA-2048 非对称加密 |
| `SHA256` | SHA-256 哈希 |
| `PLAINTEXT_BASE64` | Base64 编码（仅用于非生产环境） |

---

## 子结构定义

### RotationPolicy

| 字段 | 类型 | 约束 |
|------|------|------|
| `enabled` | boolean | 是否启用轮换 |
| `interval` | string | 轮换间隔（如 `90d`、`6m`、`1y`） |
| `auto_rotate` | boolean | 是否自动轮换 |

---

## 格式

```yaml
id: "SEC-1"
name: "database_password"
description: "生产数据库密码"

type: PASSWORD
algorithm: AES256

rotation_policy:
  enabled: true
  interval: "90d"
  auto_rotate: true

access_control_ids:
  - "PERM-1"   # 数据库管理员权限
  - "PERM-2"   # 应用服务读取权限
```

```yaml
id: "SEC-2"
name: "payment_gateway_api_key"
description: "支付网关 API 密钥"

type: API_KEY
algorithm: AES256

rotation_policy:
  enabled: false
  interval: null
  auto_rotate: false

access_control_ids:
  - "PERM-3"   # 支付服务权限
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `REQUIRES` | [Environment](environment.md) / [Module](../module.md) |
| 出 → | `AUTHORIZED_BY` | [Permission](../governance/rbac/permission.md) |
