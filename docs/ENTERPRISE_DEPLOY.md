# Enterprise Deployment Quickstart

This guide covers Docker Compose and Helm deployments for DR-RD.

## Docker Compose

```bash
docker-compose up --build
```

Services `app` and `worker` will share the `.dr_rd/` volume for logs and
knowledge base data.

## Helm

```bash
helm install dr-rd deploy/helm/dr-rd
```

Feature flags are configured via the `configmap-flags` resource and environment
variables from Kubernetes secrets.
