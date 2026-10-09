import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml'))
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import pymysql
from classifier import auto_categorize, predict_top3, detect_anomaly  # type: ignore[reportMissingImports]
from sentiment import analyze_sentiment  # type: ignore[reportMissingImports]

server = Server("complainify")

def get_db():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', os.environ.get('DB_PASS', '')),
        database=os.environ.get('DB_NAME', 'complainify'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )  # type: ignore[arg-type]


def _safe_limit(value, default=20, max_value=100):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, max_value))


def _count(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return (cur.fetchone() or {}).get('cnt', 0)
    finally:
        cur.close()

@server.list_tools()
async def list_tools():
    return [
        Tool(name="get_complaint_stats", description="Get overall complaint statistics (total, resolved, pending, in-progress, critical)", inputSchema={"type": "object", "properties": {}}),
        Tool(name="search_complaints", description="Search complaints by keyword, status, category, priority", inputSchema={"type": "object", "properties": {"keyword": {"type": "string"}, "status": {"type": "string", "enum": ["", "Pending", "In Progress", "Resolved"]}, "category": {"type": "string"}, "priority": {"type": "string", "enum": ["", "Low", "Medium", "High"]}, "limit": {"type": "integer", "default": 20}}}),
        Tool(name="predict_category", description="Predict complaint category from text", inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
        Tool(name="analyze_sentiment", description="Analyze sentiment of text", inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
        Tool(name="get_training_log", description="Get latest training metrics", inputSchema={"type": "object", "properties": {}}),
        Tool(name="get_recent_complaints", description="Get most recent complaints", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 10}}}),
        Tool(name="predict_top3_categories", description="Get top-3 predicted categories with probabilities", inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
        Tool(name="detect_anomaly", description="Check if complaint text is anomalous", inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_complaint_stats":
        conn = get_db()
        try:
            total = _count(conn, "SELECT COUNT(*) cnt FROM complaints")
            resolved = _count(conn, "SELECT COUNT(*) cnt FROM complaints WHERE status='Resolved'")
            in_progress = _count(conn, "SELECT COUNT(*) cnt FROM complaints WHERE status='In Progress'")
            pending = _count(conn, "SELECT COUNT(*) cnt FROM complaints WHERE status='Pending'")
            critical = _count(conn, "SELECT COUNT(*) cnt FROM complaints WHERE priority='High' AND status!='Resolved'")
        finally:
            conn.close()
        return [TextContent(type="text", text=json.dumps({"total": total, "resolved": resolved, "in_progress": in_progress, "pending": pending, "critical": critical}, indent=2))]
    elif name == "search_complaints":
        conn = get_db()
        try:
            cur = conn.cursor()
            try:
                conditions = ["1=1"]
                params: list = []
                kw = arguments.get("keyword", "")
                if kw:
                    conditions.append("(subject LIKE %s OR description LIKE %s)")
                    params.extend([f"%{kw}%", f"%{kw}%"])
                st = arguments.get("status", "")
                if st:
                    if st not in ("Pending", "In Progress", "Resolved"):
                        raise ValueError(f"Invalid status: {st}")
                    conditions.append("status=%s")
                    params.append(st)
                cat = arguments.get("category", "")
                if cat:
                    conditions.append("category=%s")
                    params.append(cat)
                pri = arguments.get("priority", "")
                if pri:
                    if pri not in ("Low", "Medium", "High"):
                        raise ValueError(f"Invalid priority: {pri}")
                    conditions.append("priority=%s")
                    params.append(pri)
                limit = _safe_limit(arguments.get("limit", 20))
                cur.execute(f"SELECT ticket_id, fullname, category, priority, status, sentiment, subject, date_format(created_at,'%%d %%b %%Y') created_at FROM complaints WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT {limit}", params)
                rows = cur.fetchall()
            finally:
                cur.close()
        finally:
            conn.close()
        return [TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]
    elif name == "predict_category":
        return [TextContent(type="text", text=json.dumps(auto_categorize(arguments["text"]), indent=2))]
    elif name == "analyze_sentiment":
        return [TextContent(type="text", text=json.dumps(analyze_sentiment(arguments["text"]), indent=2))]
    elif name == "get_training_log":
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'training_log.json')
        if os.path.isfile(log_path):
            with open(log_path) as f:
                data = json.load(f)
        else:
            data = {"error": "No training log found"}
        return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]
    elif name == "get_recent_complaints":
        conn = get_db()
        try:
            cur = conn.cursor()
            try:
                limit = _safe_limit(arguments.get('limit', 10))
                cur.execute(f"SELECT ticket_id, fullname, category, priority, status, sentiment, subject, date_format(created_at,'%d %b %Y') created_at FROM complaints ORDER BY created_at DESC LIMIT {limit}")
                rows = cur.fetchall()
            finally:
                cur.close()
        finally:
            conn.close()
        return [TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]
    elif name == "predict_top3_categories":
        return [TextContent(type="text", text=json.dumps(predict_top3(arguments["text"]), indent=2))]
    elif name == "detect_anomaly":
        return [TextContent(type="text", text=json.dumps(detect_anomaly(arguments["text"]), indent=2))]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
