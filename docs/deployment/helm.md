# Helm Chart Reference

## Values

| Parameter                    | Default                   | Description                          |
|------------------------------|---------------------------|--------------------------------------|
| `replicaCount`               | `1`                       | Number of API replicas               |
| `image.repository`           | `securesight/api`         | Image repository                     |
| `image.tag`                  | `latest`                  | Image tag                            |
| `image.pullPolicy`           | `Always`                  | Image pull policy                    |
| `config.appEnv`              | `production`              | Application environment              |
| `config.debug`               | `false`                   | Enable debug mode                    |
| `config.logLevel`            | `INFO`                    | Logging level                        |
| `config.secretKey`           | (auto-generated)          | Flask/FastAPI secret key             |
| `postgresql.enabled`         | `true`                    | Deploy PostgreSQL sub-chart          |
| `postgresql.auth.database`   | `securesight`             | Database name                        |
| `redis.enabled`              | `true`                    | Deploy Redis sub-chart               |
| `redis.auth.enabled`         | `true`                    | Enable Redis auth                    |
| `ingress.enabled`            | `false`                   | Enable Ingress                       |
| `ingress.host`               | `securesight.local`       | Ingress hostname                     |
| `ingress.tls`                | `false`                   | Enable TLS                           |
| `resources.api.requests.cpu` | `250m`                    | API CPU request                      |
| `resources.worker.requests.cpu` | `500m`                 | Worker CPU request                   |
| `monitoring.prometheus.enabled` | `false`               | Deploy Prometheus                    |
| `monitoring.grafana.enabled` | `false`                   | Deploy Grafana                       |
| `worker.replicas`            | `1`                       | Celery worker replicas               |
| `beat.enabled`               | `true`                    | Enable Celery Beat scheduler          |

## Installing from Source

```bash
git clone https://github.com/your-org/securesight.git
cd securesight/deploy/helm
helm install securesight ./securesight \
  --namespace securesight \
  --create-namespace \
  -f values.yaml
```

## Upgrading

```bash
helm upgrade securesight ./securesight \
  --namespace securesight \
  -f values.yaml
```
