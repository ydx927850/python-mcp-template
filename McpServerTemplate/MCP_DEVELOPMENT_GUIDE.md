# MCP Server 开发指南

本模板用于开发 MCP Server 工具，开发完成后可直接托管到平台上运行。

## 快速开始：新增一个工具

只需一步——在 `open_platform_server.py` 中添加函数：

```python
@server.tool()
async def my_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """搜索相关内容

    Args:
        query: 搜索关键词
        limit: 返回数量上限，默认10

    Returns:
        搜索结果
    """
    # 业务逻辑
    return {"results": []}
```

## 参数描述规范

### 使用 docstring Args

Python FastMCP 通过 docstring 的 `Args:` 段提取参数描述，LLM 依赖描述理解参数含义：

```python
@server.tool()
async def add(a: int, b: int) -> Dict[str, Any]:
    """加法运算

    Args:
        a: 第一个操作数
        b: 第二个操作数
    """
```

**每个参数都必须有描述**，否则 LLM 无法判断何时使用该参数。

### 类型注解

| Python 类型 | 说明 |
|------------|------|
| `str` | 字符串 |
| `int` | 整数 |
| `float` | 浮点数 |
| `bool` | 布尔值 |
| `Optional[str]` | 可选参数，可为 None |
| `List[int]` | 整数数组 |
| `Dict[str, Any]` | 字典 |

### 可选参数

使用 `Optional` 或默认值定义可选参数：

```python
async def search(query: str, limit: int = 10, sort: Optional[str] = None):
    """搜索

    Args:
        query: 搜索关键词
        limit: 返回数量上限，默认10
        sort: 排序方式，为空则默认排序
    """
```

**注意**：使用可选参数时，必须在代码中做空值判断（`if x is not None` 或 `x or default_value`）。

## 工具声明规范

### @server.tool() 装饰器

- 函数的 docstring 第一行是工具描述，LLM 据此判断何时调用此工具
- 描述应当简洁明确，说明工具的功能而非实现细节

```python
# 好的描述
"""对两个数进行加法运算"""

# 不好的描述 — 过于宽泛
"""计算"""
```

### 无参数工具

不需要任何参数时，函数签名无需参数：

```python
@server.tool()
async def get_env_configs() -> Dict[str, str]:
    """获取平台注入的环境变量配置"""
    return {
        "BASE_ENV": os.environ.get("BASE_ENV", ""),
        "SENSITIVE_ENV": os.environ.get("SENSITIVE_ENV", ""),
    }
```

## 返回格式规范

### 正常返回

返回 dict，FastMCP 框架会自动包装为 MCP 标准格式：

```python
return {"result": 42}
```

### 错误返回

**不要 throw 异常**，而是返回 `isError: True`：

```python
from mcp.types import TextContent

if invalid_input:
    return {
        "content": [TextContent(type="text", text="清晰描述错误原因")],
        "isError": True,
    }
```

LLM 会根据 `isError` 判断工具调用失败，并决定是否重试或告知用户。错误信息应当清晰描述失败原因，帮助 LLM 决定下一步行为。

### try/except 模式

```python
@server.tool()
async def my_tool(data: str) -> Dict[str, Any]:
    """工具描述

    Args:
         输入数据
    """
    try:
        result = process(data)
        return {"result": result}
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=str(e))],
            "isError": True,
        }
```

## 环境变量

平台通过环境变量注入配置，工具内通过 `os.environ` 获取：

| 变量名 | 用途 | 示例 |
|--------|------|------|
| `BASE_ENV` | 基础配置（环境标识、服务地址等） | `{"env":"prod","apiBase":"https://..."}` |
| `SENSITIVE_ENV` | 敏感凭证（API Key、Secret 等） | `{"apiKey":"sk-xxx"}` |

读取时始终提供默认值：

```python
import os

api_key = os.environ.get("SENSITIVE_ENV", "")
```

## 文件结构

```
McpServerTemplate/
├── pyproject.toml                          # 项目配置和依赖
├── MCP_DEVELOPMENT_GUIDE.md                # 开发指南（本文件）
└── src/McpServerTemplate/
    ├── __init__.py                          # 入口，启动 MCP Server
    └── open_platform_server.py             # MCP 工具定义（本文件）
```

当前模板所有工具定义在同一个文件中。如果工具数量增多，可按业务领域拆分为多个文件，每个文件创建独立的 `FastMCP` 实例。

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 工具函数名 | 动词或动词短语 | `add`, `batch_calculate`, `get_env_configs` |
| 工具 docstring | 简洁的功能描述 | `"""对两个数进行加法运算"""` |
| Args 参数描述 | 说明参数含义和约束 | `limit: 返回数量上限，默认10` |