# Quick Start Guide

## First Time Setup

```bash
# Navigate to the project
cd ~/jira-metrics

# Activate virtual environment
source .venv/bin/activate

# Create a Jira API token at:
# https://id.atlassian.com/manage-profile/security/api-tokens

# Create a GitHub personal access token at:
# https://github.com/settings/tokens/new
# (Select 'repo' scope)

# Set your API tokens (add these to your ~/.zshrc for persistence)
export JIRA_API_TOKEN='your-jira-token'
export GITHUB_TOKEN='your-github-token'
```

## Running the Script

### For SP Sprint 38 (and other SP sprints)

SP sprints use board ID 55 (SP Board 2):

```bash
python sprint_metrics.py 38 --board-id 55
```

### For other sprints on the default board

```bash
python sprint_metrics.py "Sprint Name"
```

### Output as JSON

```bash
python sprint_metrics.py 38 --board-id 55 --json > sprint38_metrics.json
```

## Example Output

```
================================================================================
Sprint: SP Sprint 38
Period: 2025-10-27T00:00:00Z to 2025-11-10T00:00:00Z
State: closed
================================================================================

CYCLE TIME (hours)
  Average: 45.2h
  Median:  38.5h
  Range:   12.0h - 120.5h
  Count:   15 issues

COMPLETION RATE
  Committed: 18 issues
  Completed: 15 issues
  Rate:      83.3%

OTHER METRICS
  Carryover Count:        3 issues
  Cards per Week:         7.5
  Blocked > 24hr:         11.1%
  WIP Count (at end):     3 issues

  Average PR Size:        N/A
    Note: PR size data not available in Jira. Requires GitHub/GitLab integration.
```

## Troubleshooting

### "Sprint not found"
The script will list available sprints. Make sure you're using the correct board ID.

### "JIRA_API_TOKEN not set"
Export the token in your current shell session or add it to `~/.zshrc`.

### Import errors
Make sure the virtual environment is activated:
```bash
source .venv/bin/activate
```
