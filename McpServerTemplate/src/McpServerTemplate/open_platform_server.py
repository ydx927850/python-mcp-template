import os
import json
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, field_validator
from jinja2 import Template
import chardet
from mcp.server import FastMCP
from mcp.types import TextContent

server = FastMCP("utility-tools")


# ==================== Pydantic数据验证模型 ====================

class UserInfo(BaseModel):
    """用户信息模型 - 演示Pydantic的数据验证能力"""
    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    age: int = Field(..., ge=0, le=150, description="年龄")
    email: str = Field(..., description="邮箱地址")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


# ==================== Pydantic数据验证工具 ====================

@server.tool()
async def validate_user_data(name: str, age: int, email: str) -> Dict[str, Any]:
    """使用Pydantic验证用户数据 - 演示数据验证和序列化

    Args:
        name: 用户名（长度1-50）
        age: 年龄（0-150）
        email: 邮箱地址

    Returns:
        验证后的用户数据或错误信息
    """
    try:
        user = UserInfo(name=name, age=age, email=email)
        return {
            "data": user.model_dump(),
            "json": user.model_dump_json()
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=str(e))],
            "isError": True,
        }


# ==================== python-dateutil高级日期工具 ====================

@server.tool()
async def datetime_parse_auto(date_str: str) -> Dict[str, Any]:
    """智能解析任意格式的日期时间字符串（使用python-dateutil）

    Args:
        date_str: 任意格式的日期时间字符串，如 "2024-01-15"、"Jan 15, 2024"、"15/01/2024"

    Returns:
        解析后的日期时间信息
    """
    try:
        dt = date_parser.parse(date_str)
        return {
            "original": date_str,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "second": dt.second,
            "timestamp": dt.timestamp(),
            "iso_format": dt.isoformat()
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=str(e))],
            "isError": True,
        }


@server.tool()
async def datetime_add(
    years: int = 0,
    months: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    base_date: Optional[str] = None
) -> Dict[str, Any]:
    """日期时间加减计算（使用python-dateutil，支持智能计算跨月、闰年等）

    Args:
        years: 增加的年数（负数为减）
        months: 增加的月数（负数为减）
        days: 增加的天数（负数为减）
        hours: 增加的小时数（负数为减）
        minutes: 增加的分钟数（负数为减）
        seconds: 增加的秒数（负数为减）
        base_date: 基准日期字符串，为空则使用当前时间

    Returns:
        计算后的日期信息
    """
    from datetime import datetime

    base = date_parser.parse(base_date) if base_date else datetime.now()
    result = base + relativedelta(
        years=years,
        months=months,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds
    )

    return {
        "base_date": base.isoformat(),
        "added": {
            "years": years,
            "months": months,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds
        },
        "result_date": result.isoformat(),
        "result_timestamp": result.timestamp()
    }


@server.tool()
async def datetime_diff(date1: str, date2: str) -> Dict[str, Any]:
    """计算两个日期之间的差异（使用python-dateutil）

    Args:
        date1: 第一个日期字符串
        date2: 第二个日期字符串

    Returns:
        日期差异信息
    """
    dt1 = date_parser.parse(date1)
    dt2 = date_parser.parse(date2)
    diff = relativedelta(dt1, dt2)

    return {
        "date1": dt1.isoformat(),
        "date2": dt2.isoformat(),
        "years": diff.years,
        "months": diff.months,
        "days": diff.days,
        "hours": diff.hours,
        "minutes": diff.minutes,
        "seconds": diff.seconds
    }


# ==================== Jinja2模板引擎工具 ====================

@server.tool()
async def template_render(template_str: str, variables: str) -> Dict[str, Any]:
    """使用Jinja2模板引擎渲染字符串（类似Java的Velocity/Thymeleaf）

    Args:
        template_str: Jinja2模板字符串，如 "Hello, {{name}}! You are {{age}} years old."
        variables: JSON格式的变量字典，如 '{"name": "Alice", "age": 25}'

    Returns:
        渲染后的字符串
    """
    try:
        template = Template(template_str)
        vars_dict = json.loads(variables) if isinstance(variables, str) else variables
        return {"result": template.render(**vars_dict)}
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"模板渲染错误: {str(e)}")],
            "isError": True,
        }


@server.tool()
async def template_render_advanced(template_str: str, variables: str) -> Dict[str, Any]:
    """使用Jinja2模板引擎渲染字符串（高级版本，返回详细信息）

    Args:
        template_str: Jinja2模板字符串
        variables: JSON格式的变量字典

    Returns:
        包含渲染结果和详细信息的字典
    """
    try:
        template = Template(template_str)
        vars_dict = json.loads(variables) if isinstance(variables, str) else variables
        result = template.render(**vars_dict)

        return {
            "result": result,
            "template": template_str,
            "variables": vars_dict
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"模板渲染错误: {str(e)}")],
            "isError": True,
        }


# ==================== URL解析和构建工具 ====================

@server.tool()
async def url_parse(url: str) -> Dict[str, Any]:
    """解析URL（使用urllib）

    Args:
        url: 要解析的URL字符串

    Returns:
        URL的各个组成部分
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "query_params": query_params
    }


@server.tool()
async def url_build(scheme: str, netloc: str, path: str, query_params: str) -> Dict[str, Any]:
    """构建URL（使用urllib）

    Args:
        scheme: 协议，如 "https"
        netloc: 网络位置，如 "example.com:8080"
        path: 路径，如 "/api/users"
        query_params: JSON格式的查询参数，如 '{"key": "value", "page": 1}'

    Returns:
        完整的URL字符串
    """
    try:
        params_dict = json.loads(query_params) if isinstance(query_params, str) else query_params
        query_string = urlencode(params_dict)

        url = f"{scheme}://{netloc}{path}"
        if query_string:
            url += f"?{query_string}"

        return {"result": url}
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"URL构建错误: {str(e)}")],
            "isError": True,
        }


@server.tool()
async def url_encode(text: str) -> str:
    """URL编码（使用urllib）

    Args:
        text: 要编码的文本

    Returns:
        URL编码后的字符串
    """
    return quote(text, safe='')


@server.tool()
async def url_decode(encoded_text: str) -> str:
    """URL解码（使用urllib）

    Args:
        encoded_text: URL编码的文本

    Returns:
        解码后的字符串
    """
    return unquote(encoded_text)


# ==================== chardet编码检测工具 ====================

@server.tool()
async def detect_encoding(text: str) -> Dict[str, Any]:
    """检测文本编码（使用chardet）

    Args:
        text: 要检测编码的文本

    Returns:
        编码检测结果
    """
    # 将文本转为字节进行检测
    if isinstance(text, str):
        text_bytes = text.encode('utf-8')
    else:
        text_bytes = text

    result = chardet.detect(text_bytes)

    return {
        "encoding": result['encoding'],
        "confidence": result['confidence'],
        "language": result.get('language', 'unknown')
    }


# ==================== 环境变量调试工具 ====================

@server.tool()
async def print_env() -> Dict[str, str]:
    """打印环境变量BASE_ENV和SENSITIVE_ENV的值（调试用）

    Returns:
        环境变量的值
    """
    base_env = os.environ.get("BASE_ENV", "未设置")
    sensitive_env = os.environ.get("SENSITIVE_ENV", "未设置")
    print(f"BASE_ENV = {base_env}")
    print(f"SENSITIVE_ENV = {sensitive_env}")
    return {
        "BASE_ENV": base_env,
        "SENSITIVE_ENV": sensitive_env
    }


# ==================== 出参Schema验证工具（BaseModel返回类型） ====================

class ValidateUserDataV2Output(BaseModel):
    """validate_user_data_v2 的出参模型"""
    name: str = Field(description="用户名")
    age: int = Field(description="年龄")
    email: str = Field(description="邮箱地址")


@server.tool()
async def validate_user_data_v2(name: str, age: int, email: str) -> ValidateUserDataV2Output:
    """使用Pydantic验证用户数据V2 - 演示带出参Schema的版本

    Args:
        name: 用户名（长度1-50）
        age: 年龄（0-150）
        email: 邮箱地址

    Returns:
        验证后的用户数据
    """
    user = UserInfo(name=name, age=age, email=email)
    return ValidateUserDataV2Output(
        name=user.name,
        age=user.age,
        email=user.email
    )


# ==================== 请求Header读取工具 ====================

import httpx
from mcp.server.fastmcp.server import Context

@server.tool()
async def get_request_headers(ctx: Context) -> Dict[str, Any]:
    """获取当前MCP请求的HTTP Header信息

    通过Context访问底层Starlette Request对象，读取请求头。
    仅在HTTP传输模式（SSE/StreamableHTTP）下有效，stdio模式下返回空。

    Returns:
        请求头信息，包含所有header键值对、客户端IP、请求方法等
    """
    request = ctx.request_context.request
    if request is None:
        return {
            "transport": "stdio",
            "headers": {},
            "note": "当前为stdio传输模式，无HTTP请求对象"
        }

    headers = dict(request.headers)
    client_host = request.client if hasattr(request, 'client') and request.client else None

    return {
        "transport": "http",
        "method": request.method if hasattr(request, 'method') else None,
        "url": str(request.url) if hasattr(request, 'url') else None,
        "client_host": f"{client_host[0]}:{client_host[1]}" if client_host else None,
        "headers": headers,
        "header_keys": list(headers.keys()),
    }


# ==================== 外部API调用工具 ====================

@server.tool()
async def fetch_jsonplaceholder(
    resource: str = "posts",
    resource_id: Optional[str] = None,
) -> Dict[str, Any]:
    """调用JSONPlaceholder公共API获取模拟数据

    Args:
        resource: 资源类型，可选值: posts, comments, albums, photos, todos, users
        resource_id: 资源ID，为空则获取列表，指定则获取单条

    Returns:
        API返回的JSON数据
    """
    # 平台可能传空字符串，需要手动处理
    if resource_id is not None and resource_id.strip() != "":
        rid = int(resource_id)
    else:
        rid = None

    allowed_resources = {"posts", "comments", "albums", "photos", "todos", "users"}
    if resource not in allowed_resources:
        return {
            "content": [TextContent(
                type="text",
                text=f"不支持的资源类型: {resource}，可选值: {', '.join(sorted(allowed_resources))}"
            )],
            "isError": True,
        }

    url = f"https://jsonplaceholder.typicode.com/{resource}"
    if rid is not None:
        url += f"/{rid}"

    import time
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            http_cost = round((time.monotonic() - t0) * 1000)
            resp.raise_for_status()
            data = resp.json()
            total_cost = round((time.monotonic() - t0) * 1000)

        # 列表请求只返回前5条，减少响应体积
        if rid is None and isinstance(data, list):
            data = data[:10]

        return {
            "content": [TextContent(type="text", text=json.dumps({
                "url": url,
                "status_code": resp.status_code,
                "debug": {
                    "http_cost_ms": http_cost,
                    "total_cost_ms": total_cost,
                    "response_content_length": len(resp.content),
                },
                "data": data,
            }, ensure_ascii=False))],
        }
    except httpx.HTTPStatusError as e:
        http_cost = round((time.monotonic() - t0) * 1000)
        return {
            "content": [TextContent(type="text", text=f"HTTP错误: {e.response.status_code} - {e.response.text}, http_cost_ms={http_cost}")],
            "isError": True,
        }
    except httpx.RequestError as e:
        http_cost = round((time.monotonic() - t0) * 1000)
        return {
            "content": [TextContent(type="text", text=f"请求失败: {str(e)}, http_cost_ms={http_cost}")],
            "isError": True,
        }
