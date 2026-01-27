# 定时任务性能优化说明

## 问题描述

在后台执行定时任务时，会影响API接口的响应时间，导致用户体验下降。

## 优化方案

### 1. 使用线程池执行器隔离任务执行

**问题**：定时任务在主线程中执行，会阻塞API请求处理。

**解决方案**：
- 使用 `ThreadPoolExecutor` 创建独立的线程池执行定时任务
- 配置 `max_workers=3`，限制并发任务数量
- 任务在独立线程中执行，不会阻塞主线程和API请求

**代码位置**：`backend/app/tasks/scheduler.py`

```python
# 任务执行器配置
TASK_EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="scheduler_task")
```

### 2. 优化数据库连接池配置

**问题**：定时任务和API请求共享连接池，可能导致连接不足。

**解决方案**：
- 增加基础连接池大小：从 10 增加到 15
- 增加最大溢出连接数：从 20 增加到 25
- 添加连接回收机制：`pool_recycle=3600`（1小时）

**代码位置**：`backend/app/database/session.py`

```python
engine = create_engine(
    db_url,
    pool_size=15,  # 增加基础连接池大小
    max_overflow=25,  # 增加最大溢出连接数
    pool_recycle=3600,  # 连接回收时间（1小时）
    ...
)
```

### 3. 添加任务执行超时控制

**问题**：任务执行时间过长，可能占用资源过久。

**解决方案**：
- 设置任务执行超时时间：`TASK_TIMEOUT = 3600`（1小时）
- 使用 `concurrent.futures` 实现超时控制
- 超时后自动终止任务，释放资源

**代码位置**：`backend/app/tasks/scheduler.py`

```python
TASK_TIMEOUT = 3600  # 1小时超时

def _execute_task_with_timeout(task_func, timeout: int = TASK_TIMEOUT):
    """在独立线程中执行任务，带超时控制"""
    ...
```

### 4. 配置任务调度器参数

**优化点**：
- `coalesce=True`：合并多个待执行的任务，避免重复执行
- `max_instances=1`：同一任务最多1个实例同时运行
- `misfire_grace_time=300`：任务错过执行时间后，5分钟内仍可执行

**代码位置**：`backend/app/tasks/scheduler.py`

```python
job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 300,
}
```

### 5. 添加日志记录和监控

**优化点**：
- 添加线程名称到日志，便于追踪任务执行
- 记录任务执行时间和结果
- 使用 Python logging 模块记录详细日志

**代码位置**：`backend/app/tasks/scheduler.py`

```python
import logging
logger = logging.getLogger(__name__)

# 在任务执行时记录日志
logger.info(f"[{thread_name}] 开始同步 {target_date} 的数据...")
```

## 性能改进效果

### 优化前
- ❌ 定时任务在主线程执行，阻塞API请求
- ❌ 数据库连接池不足，导致请求等待
- ❌ 任务执行时间过长，占用资源
- ❌ 无法追踪任务执行情况

### 优化后
- ✅ 定时任务在独立线程池执行，不阻塞API请求
- ✅ 数据库连接池充足，支持更多并发
- ✅ 任务执行有超时控制，避免资源占用过久
- ✅ 完善的日志记录，便于监控和调试

## 使用建议

1. **监控任务执行**：定期查看日志文件，监控任务执行情况
2. **调整线程池大小**：根据实际负载调整 `max_workers` 参数
3. **调整连接池大小**：根据数据库性能调整 `pool_size` 和 `max_overflow`
4. **设置合理的超时时间**：根据任务类型调整 `TASK_TIMEOUT`

## 相关文件

- `backend/app/tasks/scheduler.py` - 定时任务调度器
- `backend/app/database/session.py` - 数据库连接池配置
- `backend/logs/scheduler.log` - 调度器日志文件（如果配置了日志）

## 注意事项

1. **线程安全**：确保任务函数是线程安全的
2. **数据库连接**：每个任务使用独立的数据库连接
3. **资源限制**：合理设置线程池和连接池大小，避免资源浪费
4. **错误处理**：任务执行失败不会影响其他任务和API请求
