#!/usr/bin/env python3
"""
GitHub Client for fetching PR metrics.

Uses GitHub GraphQL API to efficiently fetch PR data for sprint metrics.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests


class GitHubClient:
    """Client for interacting with GitHub GraphQL API."""

    def __init__(self, token: str):
        """Initialize GitHub client with personal access token."""
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        self.api_url = "https://api.github.com/graphql"

    def _graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.session.post(self.api_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result.get("data", {})

    def get_current_user(self) -> str:
        """Get the authenticated user's login."""
        query = """
        query {
            viewer {
                login
            }
        }
        """
        data = self._graphql_query(query)
        return data.get("viewer", {}).get("login", "")

    def fetch_prs_for_sprint(
        self,
        org: str,
        repos: List[str],
        author: str,
        start_date: datetime,
        end_date: datetime,
        issue_keys: Set[str],
    ) -> List[Dict[str, Any]]:
        """
        Fetch PRs authored by user within date range and linked to sprint issues.
        
        Args:
            org: GitHub organization name
            repos: List of repository names
            author: GitHub username
            start_date: Sprint start date
            end_date: Sprint end date
            issue_keys: Set of Jira issue keys in the sprint (e.g., {"ENG-123", "ENG-456"})
        
        Returns:
            List of PR data dictionaries
        """
        all_prs = []
        
        for repo in repos:
            print(f"  Fetching PRs from {org}/{repo}...", file=sys.stderr)
            prs = self._fetch_repo_prs(org, repo, author, start_date, end_date)
            
            # Filter PRs that link to sprint issue keys
            linked_prs = []
            for pr in prs:
                if self._pr_links_to_issues(pr, issue_keys):
                    linked_prs.append(pr)
            
            print(f"    Found {len(prs)} PRs, {len(linked_prs)} linked to sprint issues", file=sys.stderr)
            all_prs.extend(linked_prs)
        
        return all_prs

    def _pr_links_to_issues(self, pr: Dict, issue_keys: Set[str]) -> bool:
        """Check if PR links to any of the sprint issue keys."""
        # Check in title, body, and branch name
        title = pr.get("title", "").upper()
        body = (pr.get("body") or "").upper()
        branch = pr.get("headRefName", "").upper()
        
        combined_text = f"{title} {body} {branch}"
        
        for key in issue_keys:
            if key.upper() in combined_text:
                return True
        
        return False

    def _fetch_repo_prs(
        self,
        org: str,
        repo: str,
        author: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch all PRs from a repository within the date range."""
        query = """
        query($owner: String!, $repo: String!, $cursor: String) {
            repository(owner: $owner, name: $repo) {
                pullRequests(
                    first: 100,
                    after: $cursor,
                    orderBy: {field: UPDATED_AT, direction: DESC}
                ) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        number
                        title
                        body
                        state
                        isDraft
                        createdAt
                        updatedAt
                        mergedAt
                        closedAt
                        headRefName
                        author {
                            login
                        }
                        additions
                        deletions
                        changedFiles
                        reviews(first: 100) {
                            totalCount
                            nodes {
                                submittedAt
                                author {
                                    login
                                }
                            }
                        }
                        reviewThreads(first: 100) {
                            totalCount
                        }
                        comments(first: 100) {
                            totalCount
                        }
                    }
                }
            }
        }
        """
        
        prs = []
        cursor = None
        has_next_page = True
        
        # Convert dates to ISO format for comparison
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        
        while has_next_page:
            variables = {
                "owner": org,
                "repo": repo,
                "cursor": cursor,
            }
            
            try:
                data = self._graphql_query(query, variables)
            except Exception as e:
                print(f"    Warning: Error fetching from {org}/{repo}: {e}", file=sys.stderr)
                break
            
            repo_data = data.get("repository")
            if not repo_data:
                break
            
            pull_requests = repo_data.get("pullRequests", {})
            page_info = pull_requests.get("pageInfo", {})
            nodes = pull_requests.get("nodes", [])
            
            for pr in nodes:
                # Filter by author
                pr_author = pr.get("author", {})
                if not pr_author or pr_author.get("login") != author:
                    continue
                
                # Filter by date range - check if PR was active during sprint
                created_at = pr.get("createdAt", "")
                updated_at = pr.get("updatedAt", "")
                
                # Include PRs that were created before sprint end and updated after sprint start
                if created_at <= end_iso and updated_at >= start_iso:
                    prs.append(pr)
                
                # Stop if we've gone past the sprint start date
                if updated_at < start_iso:
                    has_next_page = False
                    break
            
            cursor = page_info.get("endCursor")
            has_next_page = has_next_page and page_info.get("hasNextPage", False)
        
        return prs


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            "GITHUB_TOKEN or GH_TOKEN environment variable not set.",
            file=sys.stderr,
        )
        print(
            "Please create a personal access token with 'repo' scope at:",
            file=sys.stderr,
        )
        print(
            "https://github.com/settings/tokens/new",
            file=sys.stderr,
        )
        print(
            "Then set: export GITHUB_TOKEN='your-token'",
            file=sys.stderr,
        )
        sys.exit(1)
    return token
