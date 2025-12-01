# Dev Metrics Suite

A collection of tools for analyzing development and productivity metrics:

1. **Sprint Metrics** - Jira sprint metrics and GitHub PR metrics including cycle time, completion rate, PR size, review quality, and more
2. **Time Metrics** - Apple Calendar analysis showing how you spend your time across meetings, focus work, and other activities

## Setup

1. Create and activate a virtual environment:
   ```bash
   cd jira-metrics
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Create a Jira API token:
   - Visit: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token

4. Create a GitHub personal access token:
   - Visit: https://github.com/settings/tokens/new
   - Select scope: `repo` (Full control of private repositories)
   - Click "Generate token"
   - Copy the token

5. Set the API tokens as environment variables:
   ```bash
   export JIRA_API_TOKEN='your-jira-token'
   export GITHUB_TOKEN='your-github-token'
   ```

## Usage

Run the script with a sprint name or number (make sure your virtual environment is activated):

```bash
# Using sprint number
python sprint_metrics.py 38

# Using full sprint name
python sprint_metrics.py "SP Sprint 38"

# Specify a different board
python sprint_metrics.py 38 --board-id 55

# Output as JSON
python sprint_metrics.py 38 --json
```

## Metrics Calculated

### Jira Metrics
1. **Cycle Time** - Time from start to done (average, median, min, max)
2. **Completion Rate** - Percentage of committed issues that were completed
3. **Carryover Count** - Number of issues carried over from previous sprint
4. **Cards per Week** - Average number of cards completed per week
5. **Blocked Percentage** - Percentage of cards blocked > 24 hours
6. **WIP Count** - Work in progress at end of sprint

### GitHub PR Metrics
1. **PR Size** - Average and median changes, file counts, size distribution (S/M/L/XL)
2. **Velocity** - PRs merged/opened, merge rate, throughput, time to merge, time to first review
3. **Review Quality** - Number of reviewers, review comments, PRs merged without review, draft PR usage

## Notes

- The script reads your Jira configuration from `~/.config/.jira/.config.yml`
- It uses the board ID from your config by default (board 46)
- For "SP Sprint" sprints, you'll likely want to use board 55 (SP Board 2): `--board-id 55`
- GitHub repos are configured in `repos.yml` in the same directory as the script
- PRs are linked to sprint issues by matching issue keys (e.g., ENG-123) in PR title, body, or branch name
- Only PRs authored by you (based on GitHub token) and linked to sprint issues are included

## Time Metrics Usage

Analyze your Apple Calendar for the last 7 days:
```bash
python time_metrics.py
```

Analyze a different time period:
```bash
python time_metrics.py --days 14
python time_metrics.py --days 30
```

Get JSON output:
```bash
python time_metrics.py --json
```

See [TIME_METRICS.md](TIME_METRICS.md) for detailed documentation.

## Troubleshooting

### Sprint Metrics
If you get "Sprint not found", the script will list available sprints to help you find the right name.

### Time Metrics
If you get permission errors, grant Calendar access:
1. Go to System Settings → Privacy & Security → Automation
2. Find Terminal (or your terminal app)
3. Enable access to Calendar
