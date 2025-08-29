# Slack, Teams, and Jira Integrations

Optional bridge shims expose DR-RD through external platforms. Enable by
providing the required environment variables and routing rules.

## Slack
- `SLACK_SIGNING_SECRET`
- `SLACK_BOT_TOKEN`
Endpoint: `/slack/events`

## Microsoft Teams
- `MS_APP_ID`
- `MS_APP_PASSWORD`
Endpoint: `/teams/messages`

## Jira
- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`
Endpoint: `/jira/hook`

Bridges are disabled by default. Provide fixtures in tests to work offline.
