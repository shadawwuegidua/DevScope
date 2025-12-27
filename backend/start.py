#!/usr/bin/env python
"""
DevScope Phase 3 - 快速启动脚本

此脚本提供便捷的启动选项，包括：
- 检查依赖
- 验证环境
- 启动 API 服务
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """检查必要的 Python 包"""
    print("\n" + "=" * 70)
    print("检查依赖...")
    print("=" * 70)
    
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "requests": "Requests",
        "pydantic": "Pydantic",
        "numpy": "NumPy",
        "scipy": "SciPy",
        "pandas": "Pandas",
        "dateutil": "python-dateutil",
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} (缺失)")
            missing.append(package)
    
    if missing:
        print(f"\n缺少 {len(missing)} 个依赖包，请运行:")
        print(f"  pip install {' '.join(missing)}")
        print("\n或安装完整的依赖:")
        print("  pip install -r requirements.txt")
        return False
    
    print("\n✓ 所有依赖已安装")
    return True


def check_files():
    """检查必要的文件"""
    print("\n" + "=" * 70)
    print("检查文件...")
    print("=" * 70)
    
    required_files = [
        "main.py",
        "github_client.py",
        "modeling.py",
        "seed_data.py",
    ]
    
    missing = []
    backend_dir = Path(__file__).parent
    
    for filename in required_files:
        filepath = backend_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} (缺失)")
            missing.append(filename)
    
    if missing:
        print(f"\n缺少 {len(missing)} 个关键文件")
        return False
    
    print("\n✓ 所有文件已就位")
    return True


def check_environment():
    """检查环境变量"""
    print("\n" + "=" * 70)
    print("检查环境变量...")
    print("=" * 70)
    
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        print(f"  ✓ GITHUB_TOKEN 已设置 (token 长度: {len(github_token)})")
    else:
        print(f"  ⚠ GITHUB_TOKEN 未设置")
        print(f"    API 限额: 60 请求/小时（无 token）vs 5000 请求/小时（有 token）")
        print(f"    设置方式: export GITHUB_TOKEN=your_token_here")


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """启动 FastAPI 服务"""
    print("\n" + "=" * 70)
    print("启动 DevScope API 服务...")
    print("=" * 70)
    
    print(f"\n服务器配置：")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  热重载: {'启用' if reload else '禁用'}")
    print(f"\n访问地址：")
    print(f"  健康检查: http://localhost:{port}/health")
    print(f"  API 文档: http://localhost:{port}/docs")
    print(f"  API 定义: http://localhost:{port}/openapi.json")
    print(f"\n按 Ctrl+C 停止服务器\n")
    
    # 构建 uvicorn 命令
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        f"--host={host}",
        f"--port={port}",
        "--log-level=info",
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DevScope Phase 3 - 后端 API 快速启动脚本"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="禁用热重载（生产模式）"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="跳过依赖和文件检查"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("DevScope Phase 3 - Backend API")
    print("=" * 70)
    
    # 执行检查
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)
        
        if not check_files():
            sys.exit(1)
        
        check_environment()
    
    # 启动服务
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )


if __name__ == "__main__":
    main()
