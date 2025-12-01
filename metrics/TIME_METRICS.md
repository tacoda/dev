# Time Metrics - Apple Calendar Analyzer

## Overview

Analyzes your Apple Calendar events to provide insights into how you spend your time. The script automatically categorizes events and generates reports showing time distribution across different activities.

## Features

- **Automatic Categorization**: Events are categorized based on title keywords:
  - Meetings (standups, syncs, 1:1s, reviews, etc.)
  - Focus Time (coding, deep work, development)
  - Interviews
  - Lunch/Breaks
  - Learning (training, courses, workshops)
  - Admin (email, expenses, timesheets)
  - Personal (appointments, errands)
  - Other (everything else)

- **Comprehensive Metrics**:
  - Total time spent on calendar events
  - Time breakdown by category, day, and calendar
  - Meeting statistics (count, duration, longest meeting)
  - Focus time percentage
  - Busiest days identification
  - Daily and weekly trends

## Usage

### Basic Usage

Analyze the last 7 days:
```bash
python time_metrics.py
```

### Custom Time Range

Analyze the last 14 days:
```bash
python time_metrics.py --days 14
```

Analyze the last 30 days:
```bash
python time_metrics.py --days 30
```

### JSON Output

Get results as JSON for further processing:
```bash
python time_metrics.py --json
```

## Example Output

```
================================================================================
TIME METRICS - LAST 7 DAYS
================================================================================

OVERVIEW
  Total Events:         42
  Total Hours:          28.5h
  Days with Events:     5
  Avg Hours/Day:        5.7h
  Focus Time:           12.3%

TIME BY CATEGORY
  Meetings              15.5h  ( 54.4%)
  Focus Time             3.5h  ( 12.3%)
  Lunch/Breaks           3.0h  ( 10.5%)
  Admin                  2.5h  (  8.8%)
  Learning               2.0h  (  7.0%)
  Other                  2.0h  (  7.0%)

MEETING STATISTICS
  Total Meetings:       28
  Total Meeting Time:   15.5h
  Average Duration:     0.6h
  Longest Meeting:      Sprint Planning (2.0h on 2025-11-18)

BUSIEST DAYS
  2025-11-20 (Wednesday)         7.5h
  2025-11-19 (Tuesday)           6.5h
  2025-11-18 (Monday)            6.0h

DAILY BREAKDOWN
  2025-11-18 (Monday)            6.0h
  2025-11-19 (Tuesday)           6.5h
  2025-11-20 (Wednesday)         7.5h
  2025-11-21 (Thursday)          5.0h
  2025-11-22 (Friday)            3.5h

BY CALENDAR
  Work                  25.0h  ( 87.7%)
  Personal               3.5h  ( 12.3%)
```

## How It Works

1. **Data Fetching**: Uses AppleScript to access your Calendar app and fetch events within the specified date range

2. **Event Processing**: Each event is analyzed for:
   - Title and keywords
   - Start and end times
   - Duration calculation
   - Calendar association

3. **Categorization**: Events are automatically categorized based on keywords in their titles. You can customize the categories in the script by editing the `categorize_event` method.

4. **Analysis**: Calculates various metrics:
   - Aggregates time by category, day, and calendar
   - Identifies patterns and trends
   - Computes statistics like averages and percentages

## Customization

### Adding Custom Categories

Edit the `categorize_event` method in `time_metrics.py`:

```python
categories = {
    "Your Category": ["keyword1", "keyword2", "keyword3"],
    # ... other categories
}
```

### Changing Analysis Window

Use the `--days` parameter:
- Last week: `--days 7` (default)
- Last 2 weeks: `--days 14`
- Last month: `--days 30`
- Last quarter: `--days 90`

## Permissions

The first time you run the script, macOS may ask for permission to access your Calendar. You need to grant this permission for the script to work.

If you get permission errors:
1. Go to System Settings → Privacy & Security → Automation
2. Find Terminal (or your terminal app)
3. Enable access to Calendar

## Tips

- **Regular Reviews**: Run weekly to track trends over time
- **Identify Patterns**: Look for weeks with too many meetings or too little focus time
- **Set Goals**: Use focus time percentage to track progress on deep work goals
- **Compare Weeks**: Save JSON output from different weeks to compare
- **Adjust Schedule**: Use busiest days data to better distribute your calendar load

## Limitations

- Only analyzes events in Apple Calendar (not Google Calendar, Outlook, etc. unless synced)
- All-day events are included but may skew hourly calculations
- Declined events are included (Calendar doesn't easily distinguish)
- Categories are keyword-based, so naming consistency in events helps accuracy

## JSON Format

When using `--json`, the output includes:
```json
{
  "total_events": 42,
  "total_hours": 28.5,
  "total_days": 5,
  "average_hours_per_day": 5.7,
  "by_category": { ... },
  "by_day": { ... },
  "by_calendar": { ... },
  "busiest_days": { ... },
  "meeting_stats": { ... },
  "focus_time_percentage": 12.3
}
```

Perfect for:
- Tracking metrics over time
- Importing into spreadsheets
- Building dashboards
- Further analysis with other tools
