# Dependency — 第三方依赖制品

## 目标

定义第三方依赖——包名、版本范围、许可证、安全风险。Dependency 是治理域的依赖管理制品，它记录系统使用的所有第三方库和服务的元数据，确保依赖的可追溯性、合规性和安全性。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `DEP-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 依赖名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 依赖类型 |
| `package_name` | string | | 包名/服务名（如 `org.springframework:spring-core`、`com.amazonaws:aws-java-sdk-s3`） |
| `version_range` | string | SemVer 版本范围（如 `^2.0.0`、`>=1.0.0,<2.0.0`） | 允许的版本范围 |
| `current_version` | string | 具体版本号（如 `2.7.0`） | 当前使用的版本 |
| `license` | enum | 见下方 | 许可证类型 |
| `license_url` | string | URL | 许可证原文链接 |
| `source` | enum | 见下方 | 来源 |
| `source_url` | string | URL | 源码仓库链接 |
| `security_risk` | enum | 见下方 | 安全风险等级 |
| `vulnerabilities` | list\<Vulnerability\> | | 已知漏洞（可选） |
| `usage_scope` | list\<ref\> | `MOD-\d+` | 使用该依赖的模块列表 |
| `introduction_reason` | string | | 引入原因（可选） |

### type 枚举

| 值 | 含义 |
|----|------|
| `LIBRARY` | 程序库（Java Maven、JavaScript npm、Python pip 等） |
| `FRAMEWORK` | 框架（Spring Boot、React、Django 等） |
| `SERVICE` | 外部服务（AWS S3、Stripe API、SendGrid 等） |
| `TOOL` | 构建工具/开发工具（Webpack、Docker、ESLint 等） |

### license 枚举

| 值 | 含义 |
|----|------|
| `MIT` | MIT License |
| `APACHE_2_0` | Apache License 2.0 |
| `GPL_3_0` | GNU General Public License v3.0 |
| `BSD_3_CLAUSE` | BSD 3-Clause License |
| `LGPL_2_1` | GNU Lesser General Public License v2.1 |
| `MPL_2_0` | Mozilla Public License 2.0 |
| `PROPRIETARY` | 专有/商业许可证 |
| `OTHER` | 其他许可证 |

### source 枚举

| 值 | 含义 |
|----|------|
| `MAVEN_CENTRAL` | Maven Central |
| `NPM` | npm Registry |
| `PYPI` | PyPI |
| `GITHUB` | GitHub |
| `CLOUD_VENDOR` | 云厂商（AWS、Azure、GCP） |
| `PRIVATE_REGISTRY` | 私有仓库 |
| `OTHER` | 其他来源 |

### security_risk 枚举

| 值 | 含义 |
|----|------|
| `CRITICAL` | 严重——已知高危漏洞 |
| `HIGH` | 高——存在中高风险漏洞 |
| `MEDIUM` | 中——存在低风险漏洞 |
| `LOW` | 低——无已知漏洞或风险可控 |
| `UNKNOWN` | 未知——未进行安全评估 |

---

## 子结构定义

### Vulnerability

| 字段 | 类型 | 约束 |
|------|------|------|
| `cve_id` | string | CVE 标识符（如 `CVE-2021-44228`） |
| `severity` | enum | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` |
| `description` | string | 漏洞描述 |
| `affected_versions` | string | 受影响的版本范围 |
| `fixed_in_version` | string | 修复版本（如有） |
| `reference_url` | string | 漏洞详情链接 |

---

## 格式

```yaml
id: "DEP-1"
name: "Spring Boot Starter Web"
description: "Spring Boot Web 启动器，提供构建 Web 应用所需的基础依赖"

type: FRAMEWORK
package_name: "org.springframework.boot:spring-boot-starter-web"
version_range: ">=2.7.0,<3.0.0"
current_version: "2.7.0"

license: APACHE_2_0
license_url: "https://www.apache.org/licenses/LICENSE-2.0"

source: MAVEN_CENTRAL
source_url: "https://github.com/spring-projects/spring-boot"

security_risk: LOW
vulnerabilities: []

usage_scope:
  - "MOD-1"    # UserService
  - "MOD-2"    # OrderService
  - "MOD-3"    # PaymentService

introduction_reason: "提供 RESTful API 开发框架"
```

```yaml
id: "DEP-2"
name: "Log4j Core"
description: "Apache Log4j 2 日志框架核心库"

type: LIBRARY
package_name: "org.apache.logging.log4j:log4j-core"
version_range: ">=2.17.0"
current_version: "2.17.1"

license: APACHE_2_0
license_url: "https://www.apache.org/licenses/LICENSE-2.0"

source: MAVEN_CENTRAL
source_url: "https://logging.apache.org/log4j/2.x/"

security_risk: LOW
vulnerabilities:
  - cve_id: "CVE-2021-44228"
    severity: CRITICAL
    description: "Log4Shell 远程代码执行漏洞"
    affected_versions: ">=2.0-beta9,<2.15.0"
    fixed_in_version: "2.15.0"
    reference_url: "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"

usage_scope:
  - "MOD-1"    # UserService
  - "MOD-2"    # OrderService

introduction_reason: "日志记录"
```

```yaml
id: "DEP-3"
name: "AWS S3 Service"
description: "Amazon S3 对象存储服务"

type: SERVICE
package_name: "com.amazonaws:aws-java-sdk-s3"
version_range: ">=1.12.0"
current_version: "1.12.200"

license: APACHE_2_0
license_url: "https://aws.amazon.com/apache-2-0/"

source: CLOUD_VENDOR
source_url: "https://docs.aws.amazon.com/s3/"

security_risk: LOW
vulnerabilities: []

usage_scope:
  - "MOD-4"    # FileStorageService

introduction_reason: "对象存储服务"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DEPENDS_ON` | [Module](../module.md) |
