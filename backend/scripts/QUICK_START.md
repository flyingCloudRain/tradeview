# 游资机构信息导入 - 快速开始

## 🚀 最简单的方式（推荐）

### 方式一：使用简化Python脚本

```bash
# 在项目根目录执行
python3 backend/scripts/import_traders_simple.py
```

**选项：**
- `--force` 或 `-f`: 强制重新导入（删除并重新创建所有机构关联）
- `--incremental` 或 `-i`: 增量导入（保留现有关联，只添加新的）
- `--stats` 或 `-s`: 仅显示数据统计，不执行导入
- `--help` 或 `-h`: 显示帮助信息

**示例：**
```bash
# 查看数据统计
python3 backend/scripts/import_traders_simple.py --stats

# 强制重新导入（默认）
python3 backend/scripts/import_traders_simple.py --force

# 增量导入
python3 backend/scripts/import_traders_simple.py --incremental
```

### 方式二：使用Shell脚本

```bash
# 在项目根目录执行
./backend/scripts/import_traders.sh
```

**选项：**
- `--force` 或 `-f`: 强制重新导入
- `--incremental` 或 `-i`: 增量导入
- `--help` 或 `-h`: 显示帮助信息

## 📊 数据统计

- **游资主体**: 88 个
- **机构关联**: 296 个

## 🔧 其他导入方式

### 使用原始Python脚本

```bash
PYTHONPATH=. python backend/scripts/import_traders_detailed.py
```

### 使用SQL脚本

```bash
# 1. 生成SQL脚本
PYTHONPATH=. python backend/scripts/generate_traders_sql.py

# 2. 执行SQL脚本
psql $DATABASE_URL -f backend/scripts/import_traders_complete.sql
```

## ⚠️ 注意事项

1. **确保数据库已创建表**：
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **设置数据库连接**：
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database"
   # 或使用
   source backend/setup_env.sh
   ```

3. **导入模式说明**：
   - **强制重新导入**（默认）：删除所有现有关联，重新创建。适用于首次导入或需要完全重置。
   - **增量导入**：保留现有关联，只添加新的。适用于追加数据。

## 📝 验证导入结果

```bash
# 使用Python验证
python3 -c "
from app.database.session import SessionLocal
from app.models.lhb import Trader, TraderBranch
session = SessionLocal()
print(f'游资主体: {session.query(Trader).count()} 个')
print(f'机构关联: {session.query(TraderBranch).count()} 个')
session.close()
"
```

## 📚 更多信息

详细文档请查看：`backend/scripts/IMPORT_TRADERS_README.md`
