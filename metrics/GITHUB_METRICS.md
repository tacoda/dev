# GitHub PR Metrics

## Overview

The sprint metrics script now includes comprehensive GitHub PR metrics that link PRs to Jira sprint issues based on issue key references (e.g., ENG-123) in PR titles, bodies, or branch names.

## Setup

1. Create a GitHub personal access token:
   - Visit: https://github.com/settings/tokens/new
   - Select scope: `repo` (Full control of private repositories)
   - Generate and copy the token

2. Set environment variable:
   ```bash
   export GITHUB_TOKEN='your-github-token'
   ```

3. Configure repositories in `repos.yml`:
   ```yaml
   github:
     org: MDHQ
     repos:
       - infrastructure
       - MDHQ2.4
       - Clients
       - api-docs
   ```

## Metrics Collected

### 1. PR Size Metrics
- **Average Changes**: Mean total lines changed (additions + deletions)
- **Median Changes**: Median total lines changed
- **Average Files Changed**: Mean number of files modified per PR
- **Size Distribution**: 
  - Small: ≤100 lines
  - Medium: 101-500 lines
  - Large: 501-1000 lines
  - Huge: >1000 lines

### 2. Velocity Metrics
- **PRs Merged**: Count of PRs merged during sprint
- **PRs Opened**: Count of PRs opened during sprint
- **Merge Rate**: Percentage of opened PRs that were merged
- **PRs per Week**: Average PRs merged per week
- **Time to Merge**: Median hours from PR creation to merge
- **Time to First Review**: Median hours from PR creation to first review

### 3. Review Quality Metrics
- **Median Reviewers**: Median number of unique reviewers per PR
- **Median Comments**: Median number of review comments per PR
- **Merged Without Review**: Percentage of PRs merged with no reviews
- **Opened as Draft**: Percentage of PRs opened as drafts

## How It Works

1. **PR Filtering**: 
   - Fetches PRs authored by you (determined by GitHub token)
   - Filters PRs active during the sprint window (created before sprint end, updated after sprint start)
   - Links PRs to sprint by matching Jira issue keys in PR title, body, or branch name

2. **Time Windows**:
   - Uses sprint start and end dates from Jira
   - "Merged during sprint": merged_at between sprint start and end
   - "Opened during sprint": created_at between sprint start and end

3. **Data Source**:
   - GitHub GraphQL API for efficient querying
   - Fetches PR metadata, review information, and change statistics

## Example Output

```
GITHUB PR METRICS
  Total PRs Linked:       12 PRs

  PR Size:
    Average Changes:      245 lines
    Median Changes:       180 lines
    Average Files:        8.3
    Distribution:         S:4 M:6 L:2 XL:0

  Velocity:
    PRs Merged:           10
    PRs Opened:           12
    Merge Rate:           83.3%
    PRs per Week:         5.0
    Time to Merge:        28.5h
    Time to 1st Review:   4.2h

  Review Quality:
    Median Reviewers:     2
    Median Comments:      5
    Merged w/o Review:    10.0%
    Opened as Draft:      16.7%
```

## Troubleshooting

### No PRs found
- Check that your GitHub username matches the token owner
- Verify issue keys are present in PR titles, bodies, or branch names
- Ensure PRs fall within the sprint date range

### GitHub API errors
- Verify GITHUB_TOKEN is set correctly
- Check token has `repo` scope
- Ensure repos.yml lists correct org and repo names

### Rate limiting
- GitHub GraphQL API has rate limits
- Script uses efficient pagination to minimize requests
- For large sprints with many PRs, consider running during off-peak hours
