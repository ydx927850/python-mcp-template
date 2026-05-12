from McpServerTemplate.open_platform_server import server as mcp

def main():
    # 启用 gzip 压缩，与 Node.js egg.js 框架保持一致
    mcp.run(transport="sse", gzip=True)

if __name__ == "__main__":
    main()
