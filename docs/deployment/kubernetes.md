# Kubernetes Deployment

SecureSight can be deployed on Kubernetes using the provided Helm chart.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- Ingress controller (nginx, traefik, or similar)
- cert-manager (for TLS, optional)

## Helm Install

```bash
# Add the repository
helm repo add securesight https://charts.securesight.example.com
helm repo update

# Install the chart
helm install securesight securesight/securesight \
  --namespace securesight \
  --create-namespace \
  --set postgresql.auth.password=securepassword \
  --set redis.auth.password=securepassword
```

## Configuration

Create a custom `values.yaml`:

```yaml
replicaCount: 3

image:
  repository: ghcr.io/your-org/securesight
  tag: latest

config:
  appEnv: production
  debug: false
  databaseUrl: postgresql+asyncpg://postgres:password@postgres:5432/securesight
  redisUrl: redis://redis:6379/0

ingress:
  enabled: true
  host: securesight.example.com
  tls: true

resources:
  api:
    requests:
      cpu: 250m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 512Mi
  worker:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2
      memory: 1Gi
```

```bash
helm upgrade --install securesight securesight/securesight \
  --namespace securesight \
  -f values.yaml
```

## Uninstall

```bash
helm uninstall securesight --namespace securesight
kubectl delete namespace securesight
```
