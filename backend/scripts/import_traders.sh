#!/bin/bash
# 游资和游资机构导入脚本
# 使用方法: ./import_traders.sh [--force|--incremental]

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python"
    exit 1
fi

# 检查导入脚本是否存在
IMPORT_SCRIPT="$SCRIPT_DIR/import_traders_detailed.py"
if [ ! -f "$IMPORT_SCRIPT" ]; then
    echo "❌ 错误: 导入脚本不存在: $IMPORT_SCRIPT"
    exit 1
fi

# 解析参数
FORCE_REIMPORT=true
if [ "$1" == "--incremental" ] || [ "$1" == "-i" ]; then
    FORCE_REIMPORT=false
    echo "📝 使用增量导入模式（保留现有关联）"
elif [ "$1" == "--force" ] || [ "$1" == "-f" ]; then
    FORCE_REIMPORT=true
    echo "🔄 使用强制重新导入模式（删除并重新创建所有关联）"
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "游资和游资机构导入脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --force, -f        强制重新导入（删除并重新创建所有机构关联）"
    echo "  --incremental, -i   增量导入（保留现有关联，只添加新的）"
    echo "  --help, -h          显示此帮助信息"
    echo ""
    echo "默认: 强制重新导入模式"
    exit 0
fi

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT"

# 显示导入信息
echo "=========================================="
echo "游资和游资机构数据导入"
echo "=========================================="
echo "项目根目录: $PROJECT_ROOT"
echo "导入脚本: $IMPORT_SCRIPT"
echo "模式: $([ "$FORCE_REIMPORT" = true ] && echo "强制重新导入" || echo "增量导入")"
echo ""

# 检查数据库连接
echo "🔍 检查数据库连接..."
if python3 -c "from app.database.session import engine; engine.connect(); print('✅ 数据库连接成功')" 2>/dev/null; then
    echo ""
else
    echo "❌ 错误: 无法连接到数据库"
    echo "请检查:"
    echo "  1. DATABASE_URL 环境变量是否正确设置"
    echo "  2. 数据库服务是否运行"
    echo "  3. 数据库表是否已创建（运行: alembic upgrade head）"
    exit 1
fi

# 执行导入
echo "🚀 开始导入数据..."
echo ""

if [ "$FORCE_REIMPORT" = true ]; then
    python3 "$IMPORT_SCRIPT"
else
    # 修改脚本以使用增量模式
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from scripts.import_traders_detailed import main
main(force_reimport=False)
"
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 导入完成！"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ 导入失败！"
    echo "=========================================="
    exit $EXIT_CODE
fi
