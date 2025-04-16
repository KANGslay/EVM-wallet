#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成长期有效的JWT令牌
"""

import os
import sys
from datetime import datetime, timedelta
from jose import jwt

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.auth import create_long_lived_token

def main():
    # 默认使用admin用户名生成令牌
    username = "admin"
    # 生成有效期为10年的令牌
    token = create_long_lived_token(username, expires_days=3650)
    
    print(f"\n生成的长期有效JWT令牌 (10年有效期):\n")
    print(token)
    print("\n请将此令牌复制到app/config.py文件中的AUTH_TOKEN设置中")
    
    # 解码令牌以显示信息
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    exp_time = datetime.fromtimestamp(payload.get("exp"))
    print(f"\n令牌信息:")
    print(f"用户名: {payload.get('sub')}")
    print(f"过期时间: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 更新配置文件中的令牌
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app/config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()
    
    # 查找并替换AUTH_TOKEN行
    import re
    pattern = r'AUTH_TOKEN: str = os.getenv\("AUTH_TOKEN", "[^"]*"\)'
    replacement = f'AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "{token}")'
    
    updated_content = re.sub(pattern, replacement, config_content)
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print(f"\n已自动更新配置文件: {config_path}")
    
    # 更新Cherry Studio配置文件中的令牌
    cherry_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cherry_studio_mcp_config.json")
    with open(cherry_config_path, "r", encoding="utf-8") as f:
        cherry_config = f.read()
    
    # 替换AUTH_TOKEN值
    pattern = r'"AUTH_TOKEN": "[^"]*"'
    replacement = f'"AUTH_TOKEN": "{token}"'
    
    updated_cherry_config = re.sub(pattern, replacement, cherry_config)
    
    with open(cherry_config_path, "w", encoding="utf-8") as f:
        f.write(updated_cherry_config)
    
    print(f"已自动更新Cherry Studio配置文件: {cherry_config_path}")
    print("\n请重启系统以应用更改")

if __name__ == "__main__":
    main()
