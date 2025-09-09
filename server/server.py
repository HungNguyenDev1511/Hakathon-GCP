import os
import logging
import mysql.connector
from fastmcp import FastMCP, tool

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Khởi tạo MCP server
mcp = FastMCP("mysql-mcp-server")

# Hàm helper để kết nối MySQL
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "password"),
        database=os.getenv("MYSQL_DB", "ecommerce"),
    )

# Tool để query database
@mcp.tool
def query_mysql(sql: str) -> str:
    """
    Execute a SELECT query on MySQL database.
    
    Args:
        sql: câu lệnh SQL (chỉ SELECT).
    Returns:
        Tối đa 10 dòng kết quả.
    """
    if not sql.strip().lower().startswith("select"):
        return "Only SELECT queries are allowed."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    logger.info(f"Executed SQL: {sql}, got {len(rows)} rows")
    return str(rows[:10]) if rows else "No results."

if __name__ == "__main__":
    logger.info(f" MCP server started on port {os.getenv('PORT', 8080)}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    asyncio.run(
        mcp.run_async(
            transport="streamable-http", 
            host="0.0.0.0", 
            port=os.getenv("PORT", 8080),
        )
    )
