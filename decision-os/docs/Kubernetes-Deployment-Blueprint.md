# Kubernetes Deployment Blueprint

## Components

- Deployment
- Service
- Horizontal Pod Autoscaler

Manifests:

- [deployment.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/k8s/deployment.yaml)
- [service.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/k8s/service.yaml)
- [hpa.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/k8s/hpa.yaml)

## Runtime Notes

- Use `gunicorn` + `uvicorn` worker class for API pods.
- Scale stateless API pods horizontally.
- Keep Redis and PostgreSQL as managed services in production when possible.
