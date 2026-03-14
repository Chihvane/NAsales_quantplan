# Multi-Tenant And Permissions

## JWT Claims

```json
{
  "user_id": "",
  "tenant_id": "",
  "role": "",
  "exp": ""
}
```

## Tenant Table

Defined in [schema.sql](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/database/schema.sql) as `tenant_registry`.

## Permission Matrix

| Role | Gate | Capital | Risk | Audit |
|------|------|---------|------|-------|
| Analyst | Read | No | No | No |
| Risk Officer | Read | Read | Modify | Yes |
| Strategy Director | Approve | Modify | Modify | Yes |
| Admin | Full | Full | Full | Full |
| Auditor | Read | Read | Read | Full |

Implementation stubs:

- [jwt_handler.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backend/auth/jwt_handler.py)
- [permissions.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/backend/auth/permissions.py)
