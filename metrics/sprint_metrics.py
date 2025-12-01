#!/usr/bin/env python3
"""
Sprint Metrics Calculator for Jira + GitHub

Calculates sprint metrics including:
- Cycle Time (start → done)
- Completion Rate (# done / # committed)
- Carryover Count
- Cards Completed per Week
- PR Metrics (size, velocity, review quality)
- % of Cards Blocked > 24hr
- WIP Count
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
import yaml

from github_client import GitHubClient, get_github_token


class JiraClient:
    """Client for interacting with Jira REST API v3."""

    def __init__(self, server: str, email: str, api_token: str):
        self.server = server.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to Jira API."""
        url = f"{self.server}/rest/api/3/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_issues(self, jql: str, fields: List[str], max_results: int = 100) -> List[Dict]:
        """Search for issues using JQL."""
        all_issues = []
        start_at = 0

        while True:
            params = {
                "jql": jql,
                "fields": ",".join(fields),
                "maxResults": max_results,
                "startAt": start_at,
            }
            result = self._get("search", params)
            issues = result.get("issues", [])
            all_issues.extend(issues)

            if len(issues) < max_results:
                break
            start_at += max_results

        return all_issues
    
    def get_issue_changelog(self, issue_key: str) -> Dict:
        """Get changelog for a specific issue."""
        return self._get(f"issue/{issue_key}/changelog")

    def get_board_sprints(self, board_id: int) -> List[Dict]:
        """Get all sprints for a board."""
        # Use agile API for sprints
        url = f"{self.server}/rest/agile/1.0/board/{board_id}/sprint"
        all_sprints = []
        start_at = 0
        max_results = 50

        while True:
            params = {"startAt": start_at, "maxResults": max_results}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            sprints = result.get("values", [])
            all_sprints.extend(sprints)

            if result.get("isLast", True):
                break
            start_at += max_results

        return all_sprints

    def get_sprint_issues(self, sprint_id: int) -> List[Dict]:
        """Get all issues in a sprint with their changelogs."""
        # Use Agile API to get sprint issues
        url = f"{self.server}/rest/agile/1.0/sprint/{sprint_id}/issue"
        all_issues = []
        start_at = 0
        max_results = 50
        
        fields = [
            "summary",
            "status",
            "assignee",
            "created",
            "resolutiondate",
            "customfield_10020",  # Sprint field
            "customfield_10021",  # Flagged field
            "customfield_10034",  # Story Points
        ]

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "fields": ",".join(fields),
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            issues = result.get("issues", [])
            all_issues.extend(issues)

            if result.get("isLast", True) or len(issues) < max_results:
                break
            start_at += max_results
        
        # Fetch changelog for each issue separately
        for issue in all_issues:
            issue_key = issue.get("key")
            if issue_key:
                try:
                    changelog_data = self.get_issue_changelog(issue_key)
                    # Jira v3 changelog returns 'values'; normalize to expected 'histories'
                    issue["changelog"] = {"histories": changelog_data.get("values", [])}
                except Exception as e:
                    print(f"Warning: Could not fetch changelog for {issue_key}: {e}", file=sys.stderr)
                    issue["changelog"] = {"histories": []}
        
        return all_issues


class SprintMetricsCalculator:
    """Calculate metrics for a sprint."""

    def __init__(self, sprint_data: Dict, issues: List[Dict]):
        self.sprint = sprint_data
        self.issues = issues
        self.sprint_start = self._parse_date(sprint_data.get("startDate"))
        self.sprint_end = self._parse_date(sprint_data.get("endDate"))

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _get_status_transitions(self, issue: Dict) -> List[Tuple[str, datetime]]:
        """Extract status transitions from issue changelog."""
        transitions = []
        changelog = issue.get("changelog", {}).get("histories", [])

        for history in changelog:
            created = self._parse_date(history.get("created"))
            if not created:
                continue

            for item in history.get("items", []):
                if item.get("field") == "status":
                    to_status = item.get("toString", "")
                    transitions.append((to_status, created))

        # Sort by date
        transitions.sort(key=lambda x: x[1])
        return transitions

    def _find_first_transition_to(
        self, transitions: List[Tuple[str, datetime]], statuses: List[str]
    ) -> Optional[datetime]:
        """Find first transition to any of the given statuses."""
        for status, timestamp in transitions:
            if status in statuses:
                return timestamp
        return None

    def calculate_cycle_time(self) -> Dict[str, float]:
        """Calculate cycle time statistics (start → done)."""
        cycle_times = []

        for issue in self.issues:
            transitions = self._get_status_transitions(issue)

            # Find when issue started (In Progress, In Development, etc.)
            start_time = self._find_first_transition_to(
                transitions, ["In Progress", "In Development", "In Review"]
            )

            # Find when issue completed (Done, Closed, Resolved)
            done_time = self._find_first_transition_to(
                transitions, ["Done", "Closed", "Resolved"]
            )

            if start_time and done_time and done_time > start_time:
                cycle_time = (done_time - start_time).total_seconds() / 3600  # hours
                cycle_times.append(cycle_time)

        if not cycle_times:
            return {"average": 0, "median": 0, "min": 0, "max": 0, "count": 0}

        cycle_times.sort()
        return {
            "average": sum(cycle_times) / len(cycle_times),
            "median": cycle_times[len(cycle_times) // 2],
            "min": min(cycle_times),
            "max": max(cycle_times),
            "count": len(cycle_times),
        }

    def calculate_completion_rate(self) -> Dict[str, Any]:
        """Calculate completion rate (# done / # committed)."""
        total_issues = len(self.issues)
        done_statuses = {"Done", "Closed", "Resolved"}

        completed_issues = sum(
            1
            for issue in self.issues
            if issue.get("fields", {}).get("status", {}).get("name") in done_statuses
        )

        rate = (completed_issues / total_issues * 100) if total_issues > 0 else 0

        return {
            "committed": total_issues,
            "completed": completed_issues,
            "rate": rate,
        }

    def calculate_carryover_count(self) -> int:
        """Calculate count of issues carried over from previous sprint."""
        carryover_count = 0

        for issue in self.issues:
            # Check if issue was created before sprint start
            created = self._parse_date(issue.get("fields", {}).get("created"))
            if created and self.sprint_start and created < self.sprint_start:
                # Check if issue has sprint transitions in changelog
                changelog = issue.get("changelog", {}).get("histories", [])
                has_sprint_change = False
                for history in changelog:
                    for item in history.get("items", []):
                        if item.get("field") == "Sprint":
                            # This indicates the issue was moved between sprints
                            has_sprint_change = True
                            break
                    if has_sprint_change:
                        break
                
                if has_sprint_change:
                    carryover_count += 1

        return carryover_count

    def calculate_cards_per_week(self) -> float:
        """Calculate average cards completed per week."""
        if not self.sprint_start or not self.sprint_end:
            return 0

        sprint_duration_weeks = (self.sprint_end - self.sprint_start).days / 7
        if sprint_duration_weeks == 0:
            return 0

        done_statuses = {"Done", "Closed", "Resolved"}
        completed_issues = sum(
            1
            for issue in self.issues
            if issue.get("fields", {}).get("status", {}).get("name") in done_statuses
        )

        return completed_issues / sprint_duration_weeks

    def calculate_average_pr_size(self) -> Dict[str, Any]:
        """Calculate average PR size (if available from custom fields)."""
        # Note: PR size might need to be extracted from custom fields or external tools
        # This is a placeholder that returns N/A
        return {
            "average": "N/A",
            "note": "PR size data not available in Jira. Requires GitHub/GitLab integration.",
        }

    def calculate_blocked_percentage(self) -> float:
        """Calculate percentage of cards blocked > 24hr."""
        blocked_count = 0
        total_count = len(self.issues)

        for issue in self.issues:
            # Check if issue was flagged (blocked)
            flagged = issue.get("fields", {}).get("customfield_10021")

            if not flagged:
                continue

            # Check changelog for blocked duration
            changelog = issue.get("changelog", {}).get("histories", [])
            blocked_start = None
            blocked_duration = timedelta(0)

            for history in changelog:
                created = self._parse_date(history.get("created"))
                if not created:
                    continue

                for item in history.get("items", []):
                    if item.get("field") == "Flagged":
                        if item.get("toString") == "Impediment":
                            blocked_start = created
                        elif blocked_start:
                            blocked_duration += created - blocked_start
                            blocked_start = None

            # If still blocked
            if blocked_start and self.sprint_end:
                blocked_duration += self.sprint_end - blocked_start

            if blocked_duration > timedelta(hours=24):
                blocked_count += 1

        return (blocked_count / total_count * 100) if total_count > 0 else 0

    def calculate_wip_count(self) -> int:
        """Calculate Work In Progress count at end of sprint."""
        in_progress_statuses = {"In Progress", "In Development", "In Review", "To Do"}

        wip_count = sum(
            1
            for issue in self.issues
            if issue.get("fields", {}).get("status", {}).get("name")
            in in_progress_statuses
        )

        return wip_count

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all sprint metrics."""
        return {
            "sprint_name": self.sprint.get("name"),
            "sprint_id": self.sprint.get("id"),
            "start_date": self.sprint.get("startDate"),
            "end_date": self.sprint.get("endDate"),
            "state": self.sprint.get("state"),
            "cycle_time": self.calculate_cycle_time(),
            "completion_rate": self.calculate_completion_rate(),
            "carryover_count": self.calculate_carryover_count(),
            "cards_per_week": self.calculate_cards_per_week(),
            "blocked_percentage": self.calculate_blocked_percentage(),
            "wip_count": self.calculate_wip_count(),
        }


class GitHubPRMetricsCalculator:
    """Calculate GitHub PR metrics for a sprint."""

    def __init__(self, prs: List[Dict], sprint_start: datetime, sprint_end: datetime):
        self.prs = prs
        self.sprint_start = sprint_start
        self.sprint_end = sprint_end

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _filter_merged_in_sprint(self) -> List[Dict]:
        """Get PRs that were merged during the sprint."""
        merged = []
        for pr in self.prs:
            merged_at = self._parse_date(pr.get("mergedAt"))
            if merged_at and self.sprint_start <= merged_at <= self.sprint_end:
                merged.append(pr)
        return merged

    def _filter_opened_in_sprint(self) -> List[Dict]:
        """Get PRs that were opened during the sprint."""
        opened = []
        for pr in self.prs:
            created_at = self._parse_date(pr.get("createdAt"))
            if created_at and self.sprint_start <= created_at <= self.sprint_end:
                opened.append(pr)
        return opened

    def calculate_pr_size_metrics(self) -> Dict[str, Any]:
        """Calculate PR size metrics."""
        merged_prs = self._filter_merged_in_sprint()
        
        if not merged_prs:
            return {
                "average_additions": 0,
                "average_deletions": 0,
                "average_total_changes": 0,
                "average_files_changed": 0,
                "median_total_changes": 0,
                "size_distribution": {"small": 0, "medium": 0, "large": 0, "huge": 0},
                "count": 0,
            }
        
        additions_list = [pr.get("additions", 0) for pr in merged_prs]
        deletions_list = [pr.get("deletions", 0) for pr in merged_prs]
        total_changes_list = [pr.get("additions", 0) + pr.get("deletions", 0) for pr in merged_prs]
        files_changed_list = [pr.get("changedFiles", 0) for pr in merged_prs]
        
        # Size buckets
        small = sum(1 for tc in total_changes_list if tc <= 100)
        medium = sum(1 for tc in total_changes_list if 101 <= tc <= 500)
        large = sum(1 for tc in total_changes_list if 501 <= tc <= 1000)
        huge = sum(1 for tc in total_changes_list if tc > 1000)
        
        total_changes_sorted = sorted(total_changes_list)
        
        return {
            "average_additions": sum(additions_list) / len(additions_list),
            "average_deletions": sum(deletions_list) / len(deletions_list),
            "average_total_changes": sum(total_changes_list) / len(total_changes_list),
            "average_files_changed": sum(files_changed_list) / len(files_changed_list),
            "median_total_changes": total_changes_sorted[len(total_changes_sorted) // 2],
            "size_distribution": {"small": small, "medium": medium, "large": large, "huge": huge},
            "count": len(merged_prs),
        }

    def calculate_velocity_metrics(self) -> Dict[str, Any]:
        """Calculate PR velocity and flow metrics."""
        merged_prs = self._filter_merged_in_sprint()
        opened_prs = self._filter_opened_in_sprint()
        
        sprint_duration_weeks = (self.sprint_end - self.sprint_start).days / 7
        prs_per_week = len(merged_prs) / sprint_duration_weeks if sprint_duration_weeks > 0 else 0
        merge_rate = (len(merged_prs) / len(opened_prs) * 100) if opened_prs else 0
        
        # Calculate time to merge
        time_to_merge_hours = []
        for pr in merged_prs:
            created_at = self._parse_date(pr.get("createdAt"))
            merged_at = self._parse_date(pr.get("mergedAt"))
            if created_at and merged_at and merged_at > created_at:
                hours = (merged_at - created_at).total_seconds() / 3600
                time_to_merge_hours.append(hours)
        
        # Calculate time to first review
        time_to_first_review_hours = []
        for pr in merged_prs:
            created_at = self._parse_date(pr.get("createdAt"))
            reviews = pr.get("reviews", {}).get("nodes", [])
            if reviews and created_at:
                first_review_at = self._parse_date(reviews[0].get("submittedAt"))
                if first_review_at and first_review_at > created_at:
                    hours = (first_review_at - created_at).total_seconds() / 3600
                    time_to_first_review_hours.append(hours)
        
        time_to_merge_hours.sort()
        time_to_first_review_hours.sort()
        
        return {
            "prs_merged": len(merged_prs),
            "prs_opened": len(opened_prs),
            "merge_rate": merge_rate,
            "prs_per_week": prs_per_week,
            "median_time_to_merge_hours": time_to_merge_hours[len(time_to_merge_hours) // 2] if time_to_merge_hours else 0,
            "median_time_to_first_review_hours": time_to_first_review_hours[len(time_to_first_review_hours) // 2] if time_to_first_review_hours else 0,
        }

    def calculate_review_quality_metrics(self) -> Dict[str, Any]:
        """Calculate review quality metrics."""
        merged_prs = self._filter_merged_in_sprint()
        
        if not merged_prs:
            return {
                "median_review_comments": 0,
                "median_reviewers": 0,
                "pct_merged_without_review": 0,
                "pct_opened_as_draft": 0,
            }
        
        review_comments_list = []
        reviewers_list = []
        merged_without_review = 0
        opened_as_draft = 0
        
        for pr in merged_prs:
            # Review comments
            thread_count = pr.get("reviewThreads", {}).get("totalCount", 0)
            comment_count = pr.get("comments", {}).get("totalCount", 0)
            review_comments_list.append(thread_count + comment_count)
            
            # Number of reviewers
            reviews = pr.get("reviews", {}).get("nodes", [])
            unique_reviewers = set()
            for review in reviews:
                author = review.get("author", {}).get("login")
                if author:
                    unique_reviewers.add(author)
            reviewers_list.append(len(unique_reviewers))
            
            # PRs merged without review
            if len(unique_reviewers) == 0:
                merged_without_review += 1
            
            # Draft PRs
            if pr.get("isDraft"):
                opened_as_draft += 1
        
        review_comments_list.sort()
        reviewers_list.sort()
        
        return {
            "median_review_comments": review_comments_list[len(review_comments_list) // 2] if review_comments_list else 0,
            "median_reviewers": reviewers_list[len(reviewers_list) // 2] if reviewers_list else 0,
            "pct_merged_without_review": (merged_without_review / len(merged_prs) * 100) if merged_prs else 0,
            "pct_opened_as_draft": (opened_as_draft / len(merged_prs) * 100) if merged_prs else 0,
        }

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all GitHub PR metrics."""
        return {
            "size": self.calculate_pr_size_metrics(),
            "velocity": self.calculate_velocity_metrics(),
            "review_quality": self.calculate_review_quality_metrics(),
            "total_prs_linked": len(self.prs),
        }


def load_jira_config() -> Dict[str, Any]:
    """Load Jira configuration from CLI config file."""
    config_path = Path.home() / ".config" / ".jira" / ".config.yml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Jira config not found at {config_path}. Run 'jira init' first."
        )

    with open(config_path) as f:
        return yaml.safe_load(f)


def load_repos_config() -> Dict[str, Any]:
    """Load GitHub repos configuration."""
    config_path = Path("repos.yml")
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"repos.yml not found. Please create it with GitHub org and repo list."
        )
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_api_token() -> str:
    """Get Jira API token from environment or prompt."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print(
            "JIRA_API_TOKEN environment variable not set.",
            file=sys.stderr,
        )
        print(
            "Please create a token at: https://id.atlassian.com/manage-profile/security/api-tokens",
            file=sys.stderr,
        )
        print(
            "Then set: export JIRA_API_TOKEN='your-token'",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def format_metrics_output(metrics: Dict[str, Any]) -> str:
    """Format metrics for display."""
    output = []
    output.append("=" * 80)
    output.append(f"Sprint: {metrics['sprint_name']}")
    output.append(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    output.append(f"State: {metrics['state']}")
    output.append("=" * 80)
    output.append("")

    # Cycle Time
    ct = metrics["cycle_time"]
    output.append("CYCLE TIME (hours)")
    output.append(f"  Average: {ct['average']:.1f}h")
    output.append(f"  Median:  {ct['median']:.1f}h")
    output.append(f"  Range:   {ct['min']:.1f}h - {ct['max']:.1f}h")
    output.append(f"  Count:   {ct['count']} issues")
    output.append("")

    # Completion Rate
    cr = metrics["completion_rate"]
    output.append("COMPLETION RATE")
    output.append(f"  Committed: {cr['committed']} issues")
    output.append(f"  Completed: {cr['completed']} issues")
    output.append(f"  Rate:      {cr['rate']:.1f}%")
    output.append("")

    # Other Metrics
    output.append("OTHER METRICS")
    output.append(f"  Carryover Count:        {metrics['carryover_count']} issues")
    output.append(f"  Cards per Week:         {metrics['cards_per_week']:.1f}")
    output.append(f"  Blocked > 24hr:         {metrics['blocked_percentage']:.1f}%")
    output.append(f"  WIP Count (at end):     {metrics['wip_count']} issues")
    output.append("")

    # GitHub PR Metrics
    if "github_prs" in metrics:
        gh = metrics["github_prs"]
        output.append("GITHUB PR METRICS")
        output.append(f"  Total PRs Linked:       {gh['total_prs_linked']} PRs")
        output.append("")
        
        # Size metrics
        size = gh["size"]
        output.append("  PR Size:")
        output.append(f"    Average Changes:      {size['average_total_changes']:.0f} lines")
        output.append(f"    Median Changes:       {size['median_total_changes']:.0f} lines")
        output.append(f"    Average Files:        {size['average_files_changed']:.1f}")
        output.append(f"    Distribution:         S:{size['size_distribution']['small']} M:{size['size_distribution']['medium']} L:{size['size_distribution']['large']} XL:{size['size_distribution']['huge']}")
        output.append("")
        
        # Velocity metrics
        vel = gh["velocity"]
        output.append("  Velocity:")
        output.append(f"    PRs Merged:           {vel['prs_merged']}")
        output.append(f"    PRs Opened:           {vel['prs_opened']}")
        output.append(f"    Merge Rate:           {vel['merge_rate']:.1f}%")
        output.append(f"    PRs per Week:         {vel['prs_per_week']:.1f}")
        output.append(f"    Time to Merge:        {vel['median_time_to_merge_hours']:.1f}h")
        output.append(f"    Time to 1st Review:   {vel['median_time_to_first_review_hours']:.1f}h")
        output.append("")
        
        # Review quality
        rev = gh["review_quality"]
        output.append("  Review Quality:")
        output.append(f"    Median Reviewers:     {rev['median_reviewers']}")
        output.append(f"    Median Comments:      {rev['median_review_comments']}")
        output.append(f"    Merged w/o Review:    {rev['pct_merged_without_review']:.1f}%")
        output.append(f"    Opened as Draft:      {rev['pct_opened_as_draft']:.1f}%")
        output.append("")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Jira sprint metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "sprint_name",
        help="Sprint name or number (e.g., 'SP Sprint 38' or '38')",
    )
    parser.add_argument(
        "--board-id",
        type=int,
        help="Jira board ID (defaults to board in config)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_jira_config()
    api_token = get_api_token()

    # Initialize Jira client
    client = JiraClient(
        server=config["server"],
        email=config["login"],
        api_token=api_token,
    )

    # Get board ID
    board_id = args.board_id or config.get("board", {}).get("id")
    if not board_id:
        print("Error: No board ID specified", file=sys.stderr)
        sys.exit(1)

    # Find sprint
    print(f"Fetching sprints from board {board_id}...", file=sys.stderr)
    sprints = client.get_board_sprints(board_id)

    # Normalize sprint name for comparison
    search_name = args.sprint_name
    if search_name.isdigit():
        search_name = f"SP Sprint {search_name}"

    sprint = None
    for s in sprints:
        if search_name.lower() in s.get("name", "").lower():
            sprint = s
            break

    if not sprint:
        print(f"Error: Sprint '{args.sprint_name}' not found", file=sys.stderr)
        print("\nAvailable sprints:", file=sys.stderr)
        for s in sprints[:10]:
            print(f"  - {s.get('name')} (ID: {s.get('id')})", file=sys.stderr)
        sys.exit(1)

    # Fetch sprint issues
    print(f"Fetching issues for {sprint['name']}...", file=sys.stderr)
    issues = client.get_sprint_issues(sprint["id"])
    print(f"Found {len(issues)} issues", file=sys.stderr)

    # Calculate Jira metrics
    print("Calculating Jira metrics...", file=sys.stderr)
    calculator = SprintMetricsCalculator(sprint, issues)
    metrics = calculator.calculate_all_metrics()
    
    # Fetch and calculate GitHub PR metrics
    try:
        print("Fetching GitHub PRs...", file=sys.stderr)
        github_token = get_github_token()
        repos_config = load_repos_config()
        gh_client = GitHubClient(github_token)
        
        # Get current GitHub user
        gh_user = gh_client.get_current_user()
        print(f"  GitHub user: {gh_user}", file=sys.stderr)
        
        # Extract issue keys from sprint
        issue_keys = {issue.get("key") for issue in issues if issue.get("key")}
        
        # Parse sprint dates
        sprint_start = calculator.sprint_start
        sprint_end = calculator.sprint_end
        
        if sprint_start and sprint_end:
            # Fetch PRs from configured repos
            gh_org = repos_config.get("github", {}).get("org")
            gh_repos = repos_config.get("github", {}).get("repos", [])
            
            prs = gh_client.fetch_prs_for_sprint(
                org=gh_org,
                repos=gh_repos,
                author=gh_user,
                start_date=sprint_start,
                end_date=sprint_end,
                issue_keys=issue_keys,
            )
            
            print(f"Found {len(prs)} PRs linked to sprint issues", file=sys.stderr)
            
            # Calculate GitHub metrics
            gh_calculator = GitHubPRMetricsCalculator(prs, sprint_start, sprint_end)
            metrics["github_prs"] = gh_calculator.calculate_all_metrics()
        else:
            print("  Warning: Sprint dates not available, skipping GitHub metrics", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"  Warning: {e}", file=sys.stderr)
        print("  Skipping GitHub metrics", file=sys.stderr)
    except Exception as e:
        print(f"  Warning: Error fetching GitHub metrics: {e}", file=sys.stderr)
        print("  Skipping GitHub metrics", file=sys.stderr)

    # Output
    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print(format_metrics_output(metrics))


if __name__ == "__main__":
    main()
