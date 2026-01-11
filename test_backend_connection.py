#!/usr/bin/env python3
"""
后端连接测试脚本
检查数据库连接、API 配置等
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "functions" / "trading-api"))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("1. 测试模块导入")
    print("=" * 60)
    
    try:
        from app.config import settings
        print("✅ 配置模块导入成功")
        print(f"   项目名称: {settings.PROJECT_NAME}")
        print(f"   版本: {settings.VERSION}")
        print(f"   API 前缀: {settings.API_V1_PREFIX}")
        return True
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("\n" + "=" * 60)
    print("2. 测试配置")
    print("=" * 60)
    
    try:
        from app.config import settings
        
        # 检查数据库配置
        db_url = settings.DATABASE_URL
        if db_url:
            # 隐藏密码
            safe_url = db_url
            if "@" in db_url:
                parts = db_url.split("@")
                if len(parts) == 2 and ":" in parts[0]:
                    user_pass = parts[0].split(":")
                    if len(user_pass) == 2:
                        safe_url = f"{user_pass[0]}:***@{parts[1]}"
            
            print(f"✅ 数据库 URL: {safe_url}")
        else:
            print("⚠️  数据库 URL 未配置")
        
        # 检查 CORS 配置
        cors_origins = settings.CORS_ORIGINS
        print(f"✅ CORS 源数量: {len(cors_origins)}")
        print(f"   CORS 源: {', '.join(cors_origins[:3])}...")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("3. 测试数据库连接")
    print("=" * 60)
    
    try:
        from app.database.session import engine, SessionLocal
        from sqlalchemy import text
        from pathlib import Path
        
        db_url = str(engine.url)
        
        # 尝试连接数据库
        print("正在连接数据库...")
        try:
            with engine.connect() as conn:
                # 执行简单查询
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    print("✅ 数据库连接成功")
                    
                    # 获取数据库信息
                    try:
                        result = conn.execute(text("SELECT version()"))
                        version = result.fetchone()[0]
                        print(f"   PostgreSQL 版本: {version[:50]}...")
                    except Exception as e:
                        print(f"   ⚠️  无法获取数据库版本: {e}")
                    
                    return True
                else:
                    print("❌ 数据库连接测试失败")
                    return False
        except Exception as conn_error:
            raise conn_error
                
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 数据库连接失败: {error_msg}")
        print("   请检查 DATABASE_URL 环境变量是否正确配置")
        return False

def test_models():
    """测试模型导入"""
    print("\n" + "=" * 60)
    print("4. 测试数据模型")
    print("=" * 60)
    
    try:
        from app.models import (
            index, sector, lhb, zt_pool, 
            trading_calendar, task_execution
        )
        print("✅ 数据模型导入成功")
        print("   - IndexHistory")
        print("   - SectorHistory")
        print("   - LhbDetail")
        print("   - ZtPool")
        print("   - TradingCalendar")
        print("   - TaskExecution")
        return True
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_routes():
    """测试 API 路由"""
    print("\n" + "=" * 60)
    print("5. 测试 API 路由")
    print("=" * 60)
    
    try:
        from app.main import app
        
        # 获取所有路由
        routes = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                methods = list(route.methods) if route.methods else ["GET"]
                routes.append((route.path, methods))
        
        print(f"✅ 找到 {len(routes)} 个路由")
        
        # 显示主要路由
        print("\n主要路由:")
        for path, methods in routes[:10]:
            methods_str = ", ".join(methods)
            print(f"   {methods_str:8} {path}")
        
        if len(routes) > 10:
            print(f"   ... 还有 {len(routes) - 10} 个路由")
        
        return True
    except Exception as e:
        print(f"❌ API 路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cors_config():
    """测试 CORS 配置"""
    print("\n" + "=" * 60)
    print("6. 测试 CORS 配置")
    print("=" * 60)
    
    try:
        from app.main import app
        import re
        
        # 检查 CORS 中间件
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                cors_middleware = middleware
                break
        
        if cors_middleware:
            print("✅ CORS 中间件已配置")
        else:
            print("❌ CORS 中间件未找到")
            return False
        
        # 测试 CORS 函数
        from app.main import get_allowed_origin, get_cors_headers
        from fastapi import Request
        from unittest.mock import Mock
        
        # 模拟请求
        mock_request = Mock(spec=Request)
        mock_request.headers = {"origin": "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com"}
        
        origin = get_allowed_origin(mock_request)
        headers = get_cors_headers(mock_request)
        
        print(f"✅ CORS 函数测试成功")
        print(f"   测试 Origin: {mock_request.headers['origin']}")
        print(f"   允许的 Origin: {origin}")
        print(f"   CORS 头: {list(headers.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ CORS 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """测试依赖"""
    print("\n" + "=" * 60)
    print("7. 测试关键依赖")
    print("=" * 60)
    
    dependencies = {
        "fastapi": "FastAPI",
        "sqlalchemy": "SQLAlchemy",
        "alembic": "Alembic",
        "pydantic": "Pydantic",
    }
    
    # CloudBase 特定依赖（仅在 CloudBase 环境中需要）
    cloudbase_dependencies = {
        "mangum": "Mangum (CloudBase 适配器)",
    }
    
    all_ok = True
    for module_name, description in dependencies.items():
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - 未安装")
            all_ok = False
    
    # CloudBase 依赖（可选，仅在 CloudBase 环境中需要）
    print("\nCloudBase 环境依赖（可选）:")
    for module_name, description in cloudbase_dependencies.items():
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except ImportError:
            print(f"⚠️  {description} - 未安装（仅在 CloudBase 环境中需要）")
            # 不视为错误，因为这是本地测试环境
    
    return all_ok

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("后端连接测试")
    print("=" * 60)
    print(f"工作目录: {os.getcwd()}")
    print(f"Python 版本: {sys.version}")
    print()
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("配置", test_config()))
    results.append(("数据库连接", test_database_connection()))
    results.append(("数据模型", test_models()))
    results.append(("API 路由", test_api_routes()))
    results.append(("CORS 配置", test_cors_config()))
    results.append(("依赖", test_dependencies()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20} {status}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！后端应用状态正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
