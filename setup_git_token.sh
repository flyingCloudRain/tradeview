#!/bin/bash
# 配置 GitHub Token 到 Git credential helper

if [ -f .github_token ]; then
    source .github_token
    echo "配置 GitHub Token..."
    
    # 使用 credential helper 保存 token
    git config --global credential.helper osxkeychain
    
    # 测试连接（这会触发保存凭证）
    echo "测试 GitHub 连接..."
    git ls-remote origin > /dev/null 2>&1
    
    echo "✅ Token 已配置"
    echo ""
    echo "现在可以推送代码："
    echo "  git push -u origin main"
else
    echo "❌ 未找到 .github_token 文件"
fi
