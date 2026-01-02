#!/usr/bin/env python3
"""
Chat Statistics Report Generator

Generates comprehensive visualizations and statistics for chat log analysis.
Creates plots, charts, and graphs for the chat history summary document.

Usage:
    python scripts/chat_statistics_report.py [--output-dir OUTPUT_DIR]
"""

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed. Install with: pip install matplotlib")


def get_db_connection(db_path: str = ".workspace/knowledge.db") -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_session_stats(conn: sqlite3.Connection) -> list[dict]:
    """Fetch all session statistics."""
    cursor = conn.execute("""
        SELECT 
            cs.id,
            cs.title,
            cs.message_count,
            cs.user_message_count,
            cs.assistant_message_count,
            cs.first_message_at,
            cs.last_message_at
        FROM chat_sessions cs
        ORDER BY cs.first_message_at
    """)
    return [dict(row) for row in cursor.fetchall()]


def fetch_messages_by_session(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Fetch messages grouped by session."""
    cursor = conn.execute("""
        SELECT 
            session_id,
            role,
            LENGTH(content) as content_length,
            timestamp
        FROM chat_messages
        ORDER BY session_id, sequence_num
    """)
    
    by_session = defaultdict(list)
    for row in cursor:
        by_session[row['session_id']].append(dict(row))
    return dict(by_session)


def fetch_source_file_stats(conn: sqlite3.Connection) -> list[dict]:
    """Fetch source file statistics."""
    cursor = conn.execute("""
        SELECT 
            file_path,
            message_count,
            new_messages,
            imported_at
        FROM chat_source_files
        ORDER BY imported_at
    """)
    return [dict(row) for row in cursor.fetchall()]


def compute_statistics(sessions: list[dict], messages_by_session: dict) -> dict:
    """Compute comprehensive statistics."""
    stats = {
        "total_sessions": len(sessions),
        "total_messages": sum(s["message_count"] for s in sessions),
        "total_user_messages": sum(s["user_message_count"] or 0 for s in sessions),
        "total_assistant_messages": sum(s["assistant_message_count"] or 0 for s in sessions),
        "avg_messages_per_session": 0,
        "max_messages_session": None,
        "min_messages_session": None,
        "message_length_stats": {},
        "sessions_by_day": {},
        "topic_distribution": {},
    }
    
    if sessions:
        stats["avg_messages_per_session"] = stats["total_messages"] / len(sessions)
        
        sorted_by_count = sorted(sessions, key=lambda s: s["message_count"], reverse=True)
        stats["max_messages_session"] = {
            "id": sorted_by_count[0]["id"],
            "title": sorted_by_count[0]["title"],
            "count": sorted_by_count[0]["message_count"]
        }
        stats["min_messages_session"] = {
            "id": sorted_by_count[-1]["id"],
            "title": sorted_by_count[-1]["title"],
            "count": sorted_by_count[-1]["message_count"]
        }
    
    # Message length statistics
    all_lengths = []
    for session_id, messages in messages_by_session.items():
        for msg in messages:
            if msg.get("content_length"):
                all_lengths.append(msg["content_length"])
    
    if all_lengths:
        stats["message_length_stats"] = {
            "min": min(all_lengths),
            "max": max(all_lengths),
            "avg": sum(all_lengths) / len(all_lengths),
            "total_chars": sum(all_lengths)
        }
    
    # Sessions by day (from file timestamps in title parsing)
    day_counts = Counter()
    for session in sessions:
        if session.get("first_message_at"):
            try:
                dt = datetime.fromisoformat(session["first_message_at"].replace("Z", "+00:00"))
                day_counts[dt.strftime("%Y-%m-%d")] += 1
            except (ValueError, AttributeError):
                pass
    stats["sessions_by_day"] = dict(day_counts)
    
    # Topic distribution (from titles)
    topic_keywords = Counter()
    for session in sessions:
        title = session.get("title", "")
        words = title.lower().replace("-", " ").replace("_", " ").split()
        for word in words:
            if len(word) > 3:  # Skip short words
                topic_keywords[word] += 1
    stats["topic_distribution"] = dict(topic_keywords.most_common(20))
    
    return stats


def generate_text_report(stats: dict, sessions: list[dict], output_dir: Path) -> str:
    """Generate text-based report with ASCII charts."""
    
    lines = [
        "=" * 80,
        "COMPREHENSIVE CHAT LOG STATISTICS REPORT",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 80,
        "",
        "## OVERVIEW",
        f"  Total Sessions:           {stats['total_sessions']}",
        f"  Total Messages:           {stats['total_messages']}",
        f"  User Messages:            {stats['total_user_messages']}",
        f"  Assistant Messages:       {stats['total_assistant_messages']}",
        f"  Avg Messages/Session:     {stats['avg_messages_per_session']:.1f}",
        "",
    ]
    
    if stats.get("max_messages_session"):
        lines.extend([
            "## SESSION SIZE EXTREMES",
            f"  Largest:  {stats['max_messages_session']['title']} ({stats['max_messages_session']['count']} msgs)",
            f"  Smallest: {stats['min_messages_session']['title']} ({stats['min_messages_session']['count']} msgs)",
            "",
        ])
    
    if stats.get("message_length_stats"):
        mls = stats["message_length_stats"]
        lines.extend([
            "## MESSAGE LENGTH STATISTICS",
            f"  Min Length:     {mls['min']:,} chars",
            f"  Max Length:     {mls['max']:,} chars",
            f"  Avg Length:     {mls['avg']:,.0f} chars",
            f"  Total Content:  {mls['total_chars']:,} chars ({mls['total_chars']/1024:.1f} KB)",
            "",
        ])
    
    # ASCII bar chart of sessions by message count
    lines.extend([
        "## SESSION SIZE DISTRIBUTION (Messages per Session)",
        "-" * 60,
    ])
    
    # Bucket sessions by message count
    buckets = {"1-5": 0, "6-10": 0, "11-20": 0, "21-30": 0, "31-50": 0, "50+": 0}
    for s in sessions:
        count = s["message_count"]
        if count <= 5:
            buckets["1-5"] += 1
        elif count <= 10:
            buckets["6-10"] += 1
        elif count <= 20:
            buckets["11-20"] += 1
        elif count <= 30:
            buckets["21-30"] += 1
        elif count <= 50:
            buckets["31-50"] += 1
        else:
            buckets["50+"] += 1
    
    max_bucket = max(buckets.values()) if buckets.values() else 1
    for label, count in buckets.items():
        bar_len = int((count / max_bucket) * 40) if max_bucket > 0 else 0
        lines.append(f"  {label:8} | {'█' * bar_len} {count}")
    
    lines.append("")
    
    # Top topics
    if stats.get("topic_distribution"):
        lines.extend([
            "## TOP TOPIC KEYWORDS",
            "-" * 40,
        ])
        for keyword, count in list(stats["topic_distribution"].items())[:10]:
            lines.append(f"  {keyword:20} {count}")
        lines.append("")
    
    # Session list with scores
    lines.extend([
        "## ALL SESSIONS (Sorted by Message Count)",
        "-" * 80,
        f"  {'ID':<20} {'Title':<35} {'Msgs':>6} {'Grade':>6}",
        "-" * 80,
    ])
    
    for s in sorted(sessions, key=lambda x: x["message_count"], reverse=True):
        # Estimate grade based on message count (placeholder until real grading)
        count = s["message_count"]
        if count >= 40:
            grade = "A"
        elif count >= 20:
            grade = "B"
        elif count >= 10:
            grade = "C"
        elif count >= 5:
            grade = "D"
        else:
            grade = "F"
        
        title = (s["title"] or "Untitled")[:33]
        lines.append(f"  {s['id']:<20} {title:<35} {count:>6} {grade:>6}")
    
    lines.extend(["", "=" * 80, "END OF REPORT", "=" * 80])
    
    report_text = "\n".join(lines)
    
    # Save report
    report_path = output_dir / "chat_statistics_report.txt"
    report_path.write_text(report_text)
    print(f"Text report saved to: {report_path}")
    
    return report_text


def generate_matplotlib_charts(stats: dict, sessions: list[dict], output_dir: Path):
    """Generate matplotlib visualizations."""
    if not HAS_MATPLOTLIB:
        print("Skipping matplotlib charts (not installed)")
        return
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Session Size Distribution (Histogram)
    fig, ax = plt.subplots(figsize=(10, 6))
    message_counts = [s["message_count"] for s in sessions]
    ax.hist(message_counts, bins=15, color='steelblue', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Messages per Session', fontsize=12)
    ax.set_ylabel('Number of Sessions', fontsize=12)
    ax.set_title('Chat Session Size Distribution', fontsize=14, fontweight='bold')
    ax.axvline(stats['avg_messages_per_session'], color='red', linestyle='--', 
               label=f'Average: {stats["avg_messages_per_session"]:.1f}')
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / 'session_size_histogram.png', dpi=150)
    plt.close()
    print(f"Saved: {output_dir / 'session_size_histogram.png'}")
    
    # 2. Top Sessions Bar Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    top_sessions = sorted(sessions, key=lambda x: x["message_count"], reverse=True)[:10]
    titles = [s["title"][:25] + "..." if len(s["title"]) > 25 else s["title"] for s in top_sessions]
    counts = [s["message_count"] for s in top_sessions]
    
    bars = ax.barh(range(len(titles)), counts, color='steelblue', alpha=0.8)
    ax.set_yticks(range(len(titles)))
    ax.set_yticklabels(titles)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Messages', fontsize=12)
    ax.set_title('Top 10 Largest Chat Sessions', fontsize=14, fontweight='bold')
    
    # Add value labels
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                str(count), va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'top_sessions_bar.png', dpi=150)
    plt.close()
    print(f"Saved: {output_dir / 'top_sessions_bar.png'}")
    
    # 3. Topic Word Cloud (using simple bar chart as fallback)
    if stats.get("topic_distribution"):
        fig, ax = plt.subplots(figsize=(10, 8))
        topics = list(stats["topic_distribution"].items())[:15]
        words = [t[0] for t in topics]
        freqs = [t[1] for t in topics]
        
        colors = plt.cm.Blues([(f - min(freqs)) / (max(freqs) - min(freqs) + 1) * 0.6 + 0.4 
                               for f in freqs])
        
        bars = ax.barh(range(len(words)), freqs, color=colors)
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words)
        ax.invert_yaxis()
        ax.set_xlabel('Frequency', fontsize=12)
        ax.set_title('Most Common Topic Keywords', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'topic_keywords.png', dpi=150)
        plt.close()
        print(f"Saved: {output_dir / 'topic_keywords.png'}")
    
    # 4. Pie Chart - Grade Distribution (estimated)
    fig, ax = plt.subplots(figsize=(8, 8))
    grade_counts = {"A (40+ msgs)": 0, "B (20-39)": 0, "C (10-19)": 0, "D (5-9)": 0, "F (<5)": 0}
    for s in sessions:
        count = s["message_count"]
        if count >= 40:
            grade_counts["A (40+ msgs)"] += 1
        elif count >= 20:
            grade_counts["B (20-39)"] += 1
        elif count >= 10:
            grade_counts["C (10-19)"] += 1
        elif count >= 5:
            grade_counts["D (5-9)"] += 1
        else:
            grade_counts["F (<5)"] += 1
    
    labels = [k for k, v in grade_counts.items() if v > 0]
    sizes = [v for v in grade_counts.values() if v > 0]
    colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c'][:len(labels)]
    
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title('Session Grade Distribution\n(Based on Message Count)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'grade_distribution_pie.png', dpi=150)
    plt.close()
    print(f"Saved: {output_dir / 'grade_distribution_pie.png'}")
    
    # 5. Summary Dashboard
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('Chat Log Analytics Dashboard', fontsize=16, fontweight='bold', y=0.98)
    
    # Subplot 1: Key metrics
    ax1 = fig.add_subplot(2, 2, 1)
    metrics = ['Sessions', 'Messages', 'Avg/Session']
    values = [stats['total_sessions'], stats['total_messages'], stats['avg_messages_per_session']]
    ax1.bar(metrics, values, color=['#3498db', '#2ecc71', '#9b59b6'])
    ax1.set_title('Key Metrics', fontsize=12)
    for i, v in enumerate(values):
        ax1.text(i, v + 0.5, f'{v:.0f}', ha='center', fontsize=10)
    
    # Subplot 2: Size distribution
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.hist(message_counts, bins=10, color='steelblue', edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Messages')
    ax2.set_ylabel('Sessions')
    ax2.set_title('Size Distribution', fontsize=12)
    
    # Subplot 3: Top 5 sessions
    ax3 = fig.add_subplot(2, 2, 3)
    top5 = sorted(sessions, key=lambda x: x["message_count"], reverse=True)[:5]
    t5_titles = [s["title"][:20] for s in top5]
    t5_counts = [s["message_count"] for s in top5]
    ax3.barh(range(len(t5_titles)), t5_counts, color='#e74c3c')
    ax3.set_yticks(range(len(t5_titles)))
    ax3.set_yticklabels(t5_titles)
    ax3.invert_yaxis()
    ax3.set_xlabel('Messages')
    ax3.set_title('Top 5 Sessions', fontsize=12)
    
    # Subplot 4: Grade pie
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.0f%%', startangle=90)
    ax4.set_title('Grade Distribution', fontsize=12)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_dir / 'analytics_dashboard.png', dpi=150)
    plt.close()
    print(f"Saved: {output_dir / 'analytics_dashboard.png'}")


def main():
    parser = argparse.ArgumentParser(description="Generate chat statistics report")
    parser.add_argument("--output-dir", "-o", default="reports", help="Output directory for reports")
    parser.add_argument("--db", default=".workspace/knowledge.db", help="Database path")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Connecting to database: {args.db}")
    conn = get_db_connection(args.db)
    
    print("Fetching session statistics...")
    sessions = fetch_session_stats(conn)
    print(f"  Found {len(sessions)} sessions")
    
    print("Fetching message data...")
    messages_by_session = fetch_messages_by_session(conn)
    
    print("Computing statistics...")
    stats = compute_statistics(sessions, messages_by_session)
    
    # Save stats as JSON
    stats_path = output_dir / "chat_statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"Statistics saved to: {stats_path}")
    
    print("Generating text report...")
    generate_text_report(stats, sessions, output_dir)
    
    print("Generating charts...")
    generate_matplotlib_charts(stats, sessions, output_dir)
    
    conn.close()
    print("\nDone! All reports generated in:", output_dir)


if __name__ == "__main__":
    main()
