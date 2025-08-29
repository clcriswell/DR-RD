# Cloud Deployment Checklist

- **API/Schema Contract**: specify deployment endpoints and payload schema.
- **Auth/Keys/Env Names**: `CLOUD_DEPLOY_TOKEN` or cloud-specific credentials.
- **QoS/Rate-Limit**: define scaling limits and health check intervals.
- **Cost Budget**: enforce budget alarms and usage caps.
- **PII/Privacy**: environment and secret management with logging controls.
- **Test Fixtures**: deployment smoke tests and rollback scripts.
- **Acceptance**: verified rollback and safe-mode flags.
