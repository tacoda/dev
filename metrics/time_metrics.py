#!/usr/bin/env python3
"""
Time Metrics Analyzer for Apple Calendar

Analyzes calendar events from the last week and provides a breakdown of time spent.
"""

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class CalendarEvent:
    """Represents a calendar event."""
    
    def __init__(self, title: str, start: datetime, end: datetime, calendar: str):
        self.title = title
        self.start = start
        self.end = end
        self.calendar = calendar
        self.duration_hours = (end - start).total_seconds() / 3600
    
    def __repr__(self):
        return f"CalendarEvent('{self.title}', {self.start}, {self.end})"


class CalendarAnalyzer:
    """Analyzes calendar events and generates time metrics."""
    
    def __init__(self, events: List[CalendarEvent]):
        self.events = events
    
    def categorize_event(self, event: CalendarEvent) -> str:
        """Categorize an event based on its title and properties."""
        title_lower = event.title.lower()
        
        # Define category keywords
        categories = {
            "Meetings": ["meeting", "standup", "sync", "1:1", "one-on-one", "review", "retro", "retrospective", "planning", "demo"],
            "Focus Time": ["focus", "deep work", "coding", "development", "writing"],
            "Interviews": ["interview", "screening", "candidate"],
            "Lunch/Breaks": ["lunch", "break", "coffee"],
            "Learning": ["learning", "training", "course", "workshop", "study"],
            "Admin": ["admin", "email", "expense", "timesheet"],
            "Personal": ["personal", "appointment", "doctor", "dentist", "errand"],
        }
        
        # Check for category keywords
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        # Default to "Other"
        return "Other"
    
    def calculate_time_by_category(self) -> Dict[str, float]:
        """Calculate total hours spent in each category."""
        category_hours = defaultdict(float)
        
        for event in self.events:
            category = self.categorize_event(event)
            category_hours[category] += event.duration_hours
        
        return dict(sorted(category_hours.items(), key=lambda x: x[1], reverse=True))
    
    def calculate_time_by_day(self) -> Dict[str, float]:
        """Calculate total hours of events per day."""
        day_hours = defaultdict(float)
        
        for event in self.events:
            day_key = event.start.strftime("%Y-%m-%d (%A)")
            day_hours[day_key] += event.duration_hours
        
        return dict(sorted(day_hours.items()))
    
    def calculate_time_by_calendar(self) -> Dict[str, float]:
        """Calculate total hours per calendar."""
        calendar_hours = defaultdict(float)
        
        for event in self.events:
            calendar_hours[event.calendar] += event.duration_hours
        
        return dict(sorted(calendar_hours.items(), key=lambda x: x[1], reverse=True))
    
    def get_busiest_days(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get the busiest days by total event time."""
        day_hours = self.calculate_time_by_day()
        return sorted(day_hours.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_meeting_stats(self) -> Dict[str, Any]:
        """Calculate meeting-specific statistics."""
        meetings = [e for e in self.events if self.categorize_event(e) == "Meetings"]
        
        if not meetings:
            return {
                "count": 0,
                "total_hours": 0,
                "average_duration": 0,
                "longest_meeting": None,
            }
        
        durations = [m.duration_hours for m in meetings]
        longest = max(meetings, key=lambda m: m.duration_hours)
        
        return {
            "count": len(meetings),
            "total_hours": sum(durations),
            "average_duration": sum(durations) / len(durations),
            "longest_meeting": {
                "title": longest.title,
                "duration": longest.duration_hours,
                "date": longest.start.strftime("%Y-%m-%d"),
            },
        }
    
    def calculate_focus_time_percentage(self) -> float:
        """Calculate percentage of time spent in focus/deep work."""
        total_hours = sum(e.duration_hours for e in self.events)
        if total_hours == 0:
            return 0
        
        focus_events = [e for e in self.events if self.categorize_event(e) == "Focus Time"]
        focus_hours = sum(e.duration_hours for e in focus_events)
        
        return (focus_hours / total_hours) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate a complete time metrics summary."""
        total_hours = sum(e.duration_hours for e in self.events)
        total_days = len(set(e.start.date() for e in self.events))
        
        return {
            "total_events": len(self.events),
            "total_hours": total_hours,
            "total_days": total_days,
            "average_hours_per_day": total_hours / total_days if total_days > 0 else 0,
            "by_category": self.calculate_time_by_category(),
            "by_day": self.calculate_time_by_day(),
            "by_calendar": self.calculate_time_by_calendar(),
            "busiest_days": dict(self.get_busiest_days()),
            "meeting_stats": self.get_meeting_stats(),
            "focus_time_percentage": self.calculate_focus_time_percentage(),
        }


def fetch_calendar_events(days_back: int = 7) -> List[CalendarEvent]:
    """
    Fetch calendar events from Apple Calendar using AppleScript.
    
    Args:
        days_back: Number of days to look back from today
    
    Returns:
        List of CalendarEvent objects
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Format dates for AppleScript
    start_str = start_date.strftime("%m/%d/%Y")
    end_str = end_date.strftime("%m/%d/%Y")
    
    # AppleScript to fetch calendar events
    applescript = f'''
    set startDate to date "{start_str}"
    set endDate to date "{end_str}"
    set endDate to endDate + (1 * days) - 1 -- Include full end day
    
    set output to ""
    
    tell application "Calendar"
        set allCalendars to every calendar
        repeat with cal in allCalendars
            set calName to name of cal
            set theEvents to (every event of cal whose start date ≥ startDate and start date ≤ endDate)
            
            repeat with evt in theEvents
                set eventTitle to summary of evt
                set eventStart to start date of evt
                set eventEnd to end date of evt
                
                -- Format: title|||start|||end|||calendar
                set output to output & eventTitle & "|||" & (eventStart as «class isot» as string) & "|||" & (eventEnd as «class isot» as string) & "|||" & calName & "\\n"
            end repeat
        end repeat
    end tell
    
    return output
    '''
    
    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            check=True
        )
        
        events = []
        lines = result.stdout.strip().split("\n")
        
        for line in lines:
            if not line or "|||" not in line:
                continue
            
            parts = line.split("|||")
            if len(parts) != 4:
                continue
            
            title, start_str, end_str, calendar = parts
            
            # Parse ISO 8601 datetime strings from AppleScript
            try:
                # AppleScript returns format like: 2025-11-21T14:00:00
                start = datetime.fromisoformat(start_str)
                end = datetime.fromisoformat(end_str)
                
                events.append(CalendarEvent(title, start, end, calendar))
            except ValueError as e:
                print(f"Warning: Could not parse date for event '{title}': {e}")
                continue
        
        return events
    
    except subprocess.CalledProcessError as e:
        print(f"Error fetching calendar events: {e}")
        print(f"stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def format_summary(summary: Dict[str, Any]) -> str:
    """Format the summary for display."""
    output = []
    output.append("=" * 80)
    output.append("TIME METRICS - LAST 7 DAYS")
    output.append("=" * 80)
    output.append("")
    
    # Overview
    output.append("OVERVIEW")
    output.append(f"  Total Events:         {summary['total_events']}")
    output.append(f"  Total Hours:          {summary['total_hours']:.1f}h")
    output.append(f"  Days with Events:     {summary['total_days']}")
    output.append(f"  Avg Hours/Day:        {summary['average_hours_per_day']:.1f}h")
    output.append(f"  Focus Time:           {summary['focus_time_percentage']:.1f}%")
    output.append("")
    
    # Time by category
    output.append("TIME BY CATEGORY")
    for category, hours in summary["by_category"].items():
        percentage = (hours / summary["total_hours"] * 100) if summary["total_hours"] > 0 else 0
        output.append(f"  {category:20s} {hours:6.1f}h  ({percentage:5.1f}%)")
    output.append("")
    
    # Meeting stats
    meeting_stats = summary["meeting_stats"]
    output.append("MEETING STATISTICS")
    output.append(f"  Total Meetings:       {meeting_stats['count']}")
    output.append(f"  Total Meeting Time:   {meeting_stats['total_hours']:.1f}h")
    if meeting_stats['count'] > 0:
        output.append(f"  Average Duration:     {meeting_stats['average_duration']:.1f}h")
        longest = meeting_stats['longest_meeting']
        output.append(f"  Longest Meeting:      {longest['title']} ({longest['duration']:.1f}h on {longest['date']})")
    output.append("")
    
    # Busiest days
    output.append("BUSIEST DAYS")
    for day, hours in summary["busiest_days"].items():
        output.append(f"  {day:30s} {hours:6.1f}h")
    output.append("")
    
    # Daily breakdown
    output.append("DAILY BREAKDOWN")
    for day, hours in summary["by_day"].items():
        output.append(f"  {day:30s} {hours:6.1f}h")
    output.append("")
    
    # By calendar
    if len(summary["by_calendar"]) > 1:
        output.append("BY CALENDAR")
        for calendar, hours in summary["by_calendar"].items():
            percentage = (hours / summary["total_hours"] * 100) if summary["total_hours"] > 0 else 0
            output.append(f"  {calendar:20s} {hours:6.1f}h  ({percentage:5.1f}%)")
        output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Apple Calendar time metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()
    
    print(f"Fetching calendar events for the last {args.days} days...", file=sys.stderr)
    
    # Fetch events
    events = fetch_calendar_events(days_back=args.days)
    
    if not events:
        print("No calendar events found in the specified time range.")
        return
    
    print(f"Found {len(events)} events", file=sys.stderr)
    
    # Analyze
    analyzer = CalendarAnalyzer(events)
    summary = analyzer.get_summary()
    
    # Output
    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(format_summary(summary))


if __name__ == "__main__":
    import sys
    main()
