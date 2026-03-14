# Disaster Recovery And Rollback

## Database Backup

Use:

```bash
./scripts/backup_db.sh decision_os_prod
```

## Release Rollback

Use:

```bash
./scripts/rollback_release.sh decision-os:v2
```

## Decision Recovery

Use:

```bash
python scripts/recover_portfolio.py DEC-0001
```

## Kubernetes Rollback

```bash
kubectl rollout undo deployment/decision-os
```
