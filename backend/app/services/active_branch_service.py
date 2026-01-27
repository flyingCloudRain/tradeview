"""
活跃营业部服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func, or_, distinct
from typing import Optional, List
from datetime import date
from collections import Counter
import pandas as pd
import re
import decimal
import math

from app.models.lhb import ActiveBranch
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class ActiveBranchService:
    """活跃营业部服务类"""
    
    @staticmethod
    def get_list(
        db: Session,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc",
        institution_name: Optional[str] = None,
        institution_code: Optional[str] = None,
        buy_stock_name: Optional[str] = None,
    ) -> tuple[List[ActiveBranch], int]:
        """
        获取活跃营业部列表
        
        Args:
            db: 数据库会话
            target_date: 目标日期，None表示使用最新日期
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
            institution_name: 营业部名称（模糊查询）
            institution_code: 营业部代码
            buy_stock_name: 买入股票名称（查询buy_stocks字段包含该股票名称的记录）
        """
        try:
            # 优化：先获取最新日期（如果未指定），使用更高效的查询
            if not target_date:
                # 使用子查询优化，避免全表扫描
                latest_date_subquery = db.query(func.max(ActiveBranch.date)).scalar()
                if not latest_date_subquery:
                    return [], 0
                target_date = latest_date_subquery
            
            # 构建基础查询 - 先应用日期过滤（有索引）
            query = db.query(ActiveBranch).filter(ActiveBranch.date == target_date)
            
            # 营业部代码查询（精确匹配，有索引，优先应用）
            if institution_code and institution_code.strip():
                query = query.filter(ActiveBranch.institution_code == institution_code.strip())
            
            # 营业部名称模糊查询 - 优化：使用ILIKE（PostgreSQL，不区分大小写，更高效）
            if institution_name and institution_name.strip():
                institution_name_clean = institution_name.strip()
                # PostgreSQL支持ilike，比使用func.lower() + like更高效
                query = query.filter(ActiveBranch.institution_name.ilike(f"%{institution_name_clean}%"))
            
            # 买入股票名称查询 - 查询buy_stocks字段包含该股票名称的记录
            # 由于buy_stocks字段可能包含多个股票名称（用逗号、空格等分隔），
            # 需要先查询所有记录，然后在内存中过滤以确保精确匹配
            if buy_stock_name and buy_stock_name.strip():
                buy_stock_name_clean = buy_stock_name.strip()
                # 先使用LIKE进行初步过滤（数据库层面）
                query = query.filter(
                    ActiveBranch.buy_stocks.isnot(None),
                    ActiveBranch.buy_stocks != '',
                    ActiveBranch.buy_stocks.ilike(f"%{buy_stock_name_clean}%")
                )
            
            # 排序 - 先构建排序，再分页
            if sort_by:
                sort_column = getattr(ActiveBranch, sort_by, None)
                if sort_column:
                    if order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                else:
                    # 字段不存在，使用默认排序
                    from sqlalchemy import nullslast
                    query = query.order_by(nullslast(desc(ActiveBranch.net_amount)))
            else:
                # 默认按净额倒序
                from sqlalchemy import nullslast
                query = query.order_by(nullslast(desc(ActiveBranch.net_amount)))
            
            # 如果有买入股票名称过滤，需要在内存中精确匹配
            if buy_stock_name and buy_stock_name.strip():
                # 先获取所有匹配的记录（不分页）
                all_items = query.all()
                
                # 在内存中过滤：确保buy_stocks字段精确包含该股票名称
                buy_stock_name_clean = buy_stock_name.strip()
                filtered_items = []
                for item in all_items:
                    if not item.buy_stocks:
                        continue
                    # 解析buy_stocks字段，检查是否包含该股票名称
                    stocks = re.split(r'[,，\s]+', item.buy_stocks.strip())
                    if buy_stock_name_clean in [s.strip() for s in stocks]:
                        filtered_items.append(item)
                
                # 重新应用排序（如果之前有排序）
                if sort_by:
                    sort_column = getattr(ActiveBranch, sort_by, None)
                    if sort_column:
                        reverse = order == "desc"
                        filtered_items.sort(
                            key=lambda x: getattr(x, sort_by) if getattr(x, sort_by) is not None else (float('-inf') if reverse else float('inf')),
                            reverse=reverse
                        )
                    else:
                        # 默认按净额倒序
                        filtered_items.sort(
                            key=lambda x: x.net_amount if x.net_amount is not None else float('-inf'),
                            reverse=True
                        )
                else:
                    # 默认按净额倒序
                    filtered_items.sort(
                        key=lambda x: x.net_amount if x.net_amount is not None else float('-inf'),
                        reverse=True
                    )
                
                # 分页
                total = len(filtered_items)
                offset = (page - 1) * page_size
                items = filtered_items[offset:offset + page_size]
                
                return items, total
            
            # 优化：先获取总数（在分页前），但使用更高效的方法
            # 对于第一页且没有过滤条件时，可以跳过count
            need_count = True
            if page == 1 and not institution_name and not institution_code:
                # 第一页且无过滤条件，可以先获取数据，再判断是否需要count
                need_count = False
            
            # 分页
            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size + 1).all()
            
            # 判断是否有下一页
            has_next = len(items) > page_size
            if has_next:
                items = items[:page_size]
            
            # 计算总数 - 优化：只在必要时执行count
            if page == 1 and not has_next and not need_count:
                # 第一页，没有下一页，且无过滤条件，总数就是当前结果数
                total = len(items)
            elif page == 1 and not has_next:
                # 第一页，没有下一页，总数就是当前结果数
                total = len(items)
            else:
                # 需要count：使用子查询优化count性能
                # 对于有LIKE查询的情况，count可能较慢，但这是必要的
                try:
                    # 使用独立的count查询，避免重复执行排序等操作
                    count_query = db.query(func.count(ActiveBranch.id)).filter(ActiveBranch.date == target_date)
                    if institution_code and institution_code.strip():
                        count_query = count_query.filter(ActiveBranch.institution_code == institution_code.strip())
                    if institution_name and institution_name.strip():
                        institution_name_clean = institution_name.strip()
                        count_query = count_query.filter(ActiveBranch.institution_name.ilike(f"%{institution_name_clean}%"))
                    total = count_query.scalar() or 0
                except Exception as count_error:
                    # 如果count失败，回退到使用原query的count（可能较慢）
                    print(f"[ActiveBranchService] Count查询优化失败，使用回退方案: {str(count_error)}")
                    total = query.count()
            
            return items, total
            
        except Exception as e:
            print(f"[ActiveBranchService] 查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def save_active_branch_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """
        保存活跃营业部数据到数据库
        
        Args:
            db: 数据库会话
            target_date: 目标日期
            df: 数据DataFrame
            
        Returns:
            保存的记录数
        """
        count = 0
        
        # 列名映射（从AKShare返回的列名到数据库字段）
        column_mapping = {
            '营业部名称': 'institution_name',
            '营业部代码': 'institution_code',
            '买入个股数': 'buy_stock_count',
            '卖出个股数': 'sell_stock_count',
            '买入总金额': 'buy_amount',
            '卖出总金额': 'sell_amount',
            '总买卖净额': 'net_amount',
            '买入股票': 'buy_stocks',
        }
        
        # 先删除该日期的旧数据
        try:
            db.query(ActiveBranch).filter(ActiveBranch.date == target_date).delete()
            db.commit()
        except Exception as delete_error:
            print(f"[ActiveBranchService] 删除旧数据失败: {str(delete_error)}")
            db.rollback()
            # 继续执行，尝试使用 upsert 模式
        
        # 对 DataFrame 进行去重：如果有重复的 institution_code，保留最后一个
        if '营业部代码' in df.columns:
            # 保留每个 institution_code 的最后一条记录
            df = df.drop_duplicates(subset=['营业部代码'], keep='last')
            print(f"[ActiveBranchService] 去重后剩余 {len(df)} 条记录")
        
        # 用于跟踪已处理的 institution_code，避免在同一批次中重复
        processed_codes = set()
        
        for _, row in df.iterrows():
            try:
                # 提取数据
                institution_name = str(row.get('营业部名称', '')).strip()
                if not institution_name:
                    continue
                
                institution_code = str(row.get('营业部代码', '')).strip() if pd.notna(row.get('营业部代码')) else None
                
                # 如果没有 institution_code，跳过（因为唯一约束需要它）
                if not institution_code:
                    print(f"[ActiveBranchService] 跳过无代码的营业部: {institution_name}")
                    continue
                
                # 检查是否在同一批次中已经处理过
                if institution_code in processed_codes:
                    print(f"[ActiveBranchService] 跳过重复的 institution_code: {institution_code} ({institution_name})")
                    continue
                
                buy_stock_count = int(row.get('买入个股数', 0)) if pd.notna(row.get('买入个股数')) else None
                sell_stock_count = int(row.get('卖出个股数', 0)) if pd.notna(row.get('卖出个股数')) else None
                
                # 处理金额字段（可能是科学计数法）
                buy_amount = None
                if pd.notna(row.get('买入总金额')):
                    try:
                        buy_amount = float(row.get('买入总金额'))
                    except (ValueError, TypeError):
                        pass
                
                sell_amount = None
                if pd.notna(row.get('卖出总金额')):
                    try:
                        sell_amount = float(row.get('卖出总金额'))
                    except (ValueError, TypeError):
                        pass
                
                net_amount = None
                if pd.notna(row.get('总买卖净额')):
                    try:
                        net_amount = float(row.get('总买卖净额'))
                    except (ValueError, TypeError):
                        pass
                
                buy_stocks = str(row.get('买入股票', '')).strip() if pd.notna(row.get('买入股票')) else None
                
                # 使用 upsert 模式：先查询是否存在
                existing = db.query(ActiveBranch).filter(
                    ActiveBranch.date == target_date,
                    ActiveBranch.institution_code == institution_code
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.institution_name = institution_name
                    existing.buy_stock_count = buy_stock_count
                    existing.sell_stock_count = sell_stock_count
                    existing.buy_amount = buy_amount
                    existing.sell_amount = sell_amount
                    existing.net_amount = net_amount
                    existing.buy_stocks = buy_stocks
                    # existing 已经在 session 中，不需要 add
                else:
                    # 创建新记录
                    active_branch = ActiveBranch(
                        date=target_date,
                        institution_name=institution_name,
                        institution_code=institution_code,
                        buy_stock_count=buy_stock_count,
                        sell_stock_count=sell_stock_count,
                        buy_amount=buy_amount,
                        sell_amount=sell_amount,
                        net_amount=net_amount,
                        buy_stocks=buy_stocks,
                    )
                    db.add(active_branch)
                
                processed_codes.add(institution_code)
                count += 1
                
            except Exception as e:
                error_msg = str(e)
                # 如果是唯一约束冲突，尝试更新
                if "UniqueViolation" in error_msg or "duplicate key" in error_msg.lower():
                    try:
                        print(f"[ActiveBranchService] 检测到唯一约束冲突，尝试更新: institution_code={institution_code}")
                        # 刷新 session 以确保看到最新数据
                        db.rollback()
                        # 再次查询并更新
                        existing = db.query(ActiveBranch).filter(
                            ActiveBranch.date == target_date,
                            ActiveBranch.institution_code == institution_code
                        ).first()
                        if existing:
                            existing.institution_name = institution_name
                            existing.buy_stock_count = buy_stock_count
                            existing.sell_stock_count = sell_stock_count
                            existing.buy_amount = buy_amount
                            existing.sell_amount = sell_amount
                            existing.net_amount = net_amount
                            existing.buy_stocks = buy_stocks
                            processed_codes.add(institution_code)
                            count += 1
                            continue
                        else:
                            # 如果不存在，可能是并发插入，尝试再次插入
                            active_branch = ActiveBranch(
                                date=target_date,
                                institution_name=institution_name,
                                institution_code=institution_code,
                                buy_stock_count=buy_stock_count,
                                sell_stock_count=sell_stock_count,
                                buy_amount=buy_amount,
                                sell_amount=sell_amount,
                                net_amount=net_amount,
                                buy_stocks=buy_stocks,
                            )
                            db.add(active_branch)
                            processed_codes.add(institution_code)
                            count += 1
                            continue
                    except Exception as update_error:
                        print(f"[ActiveBranchService] 更新失败: {str(update_error)}")
                        db.rollback()
                
                print(f"[ActiveBranchService] 保存数据失败: {error_msg}, row: {row.to_dict()}")
                import traceback
                traceback.print_exc()
                # 不 continue，让错误传播，但先 rollback
                db.rollback()
                continue
        
        try:
            db.commit()
            print(f"成功保存 {count} 条活跃营业部数据到数据库")
        except Exception as e:
            print(f"[ActiveBranchService] 提交失败: {str(e)}")
            db.rollback()
            raise
        
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步活跃营业部数据
        从AKShare获取数据并保存到数据库
        使用接口: stock_lhb_hyyyb_em
        接口支持日期参数: start_date 和 end_date (格式: YYYYMMDD)
        
        注意: 如果目标日期无数据（可能是非交易日），会尝试获取最近有数据的日期
        """
        from app.utils.sync_result import SyncResult
        from datetime import timedelta
        
        try:
            # 将日期转换为接口需要的格式 (YYYYMMDD)
            date_str = target_date.strftime("%Y%m%d")
            
            # 调用 stock_lhb_hyyyb_em 接口，传入日期参数
            df = safe_akshare_call(ak.stock_lhb_hyyyb_em, start_date=date_str, end_date=date_str)
            
            # 如果目标日期无数据，尝试向前查找最近有数据的日期（最多查找7天）
            if df is None or df.empty:
                print(f"目标日期 {target_date} 无数据，尝试查找最近有数据的日期...")
                actual_date = None
                for i in range(1, 8):
                    check_date = target_date - timedelta(days=i)
                    check_date_str = check_date.strftime("%Y%m%d")
                    print(f"  尝试日期: {check_date} ({check_date_str})")
                    df = safe_akshare_call(ak.stock_lhb_hyyyb_em, start_date=check_date_str, end_date=check_date_str)
                    if df is not None and not df.empty:
                        actual_date = check_date
                        print(f"  找到数据日期: {actual_date}")
                        break
                
                if df is None or df.empty:
                    error_msg = f"未获取到 {target_date} 及最近7天的活跃营业部数据，可能该时间段无数据或非交易日"
                    print(error_msg)
                    return SyncResult.failure_result(error_msg, "数据源返回空")
                else:
                    # 使用找到的日期更新 target_date
                    target_date = actual_date
                    print(f"使用找到的日期 {target_date} 进行同步")
            
            # 验证返回的数据是否包含目标日期
            if '上榜日' in df.columns:
                df['上榜日'] = pd.to_datetime(df['上榜日'])
                # 过滤出目标日期的数据
                date_filtered = df[df['上榜日'].dt.date == target_date]
                if date_filtered.empty and not df.empty:
                    # 如果接口返回了数据但日期不匹配，使用返回数据中的最新日期
                    actual_date = df['上榜日'].dt.date.max()
                    print(f"警告: 接口返回的数据日期为 {actual_date}，而非请求的 {target_date}")
                    target_date = actual_date
                    df = df[df['上榜日'].dt.date == target_date]
            
            if df.empty:
                error_msg = f"未获取到 {target_date} 的活跃营业部数据（过滤后为空），可能该日期无数据或非交易日"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据过滤后为空")
            
            # 保存数据
            count = ActiveBranchService.save_active_branch_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的活跃营业部数据，共 {count} 条")
            return SyncResult.success_result(f"活跃营业部数据同步成功", count)
            
        except Exception as e:
            error_msg = f"同步活跃营业部数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)
    
    @staticmethod
    def get_buy_stocks_statistics(
        db: Session,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[dict], int]:
        """
        统计活跃营业部买入股票的出现次数及详细统计
        
        Args:
            db: 数据库会话
            target_date: 目标日期，None表示使用最新日期
            page: 页码
            page_size: 每页数量
            
        Returns:
            (统计结果列表, 总数)
            统计结果格式: [
                {
                    "stock_name": "股票名称", 
                    "appear_count": 出现次数,
                    "buy_branch_count": 买入营业部数,
                    "sell_branch_count": 卖出营业部数,
                    "net_buy_amount": 净买入额,
                    "net_sell_amount": 净卖出额
                }, 
                ...
            ]
        """
        from collections import Counter
        import re
        from app.models.lhb import ActiveBranchDetail
        
        try:
            # 获取目标日期
            if not target_date:
                latest_date_subquery = db.query(func.max(ActiveBranch.date)).scalar()
                if not latest_date_subquery:
                    return [], 0
                target_date = latest_date_subquery
            
            # 查询指定日期的所有活跃营业部记录
            records = db.query(ActiveBranch).filter(
                ActiveBranch.date == target_date,
                ActiveBranch.buy_stocks.isnot(None),
                ActiveBranch.buy_stocks != ''
            ).all()
            
            # 统计股票出现次数
            stock_counter = Counter()
            
            for record in records:
                if not record.buy_stocks:
                    continue
                
                # 解析 buy_stocks 字段（可能是空格、逗号、中文逗号分隔）
                # 支持多种分隔符：空格、逗号、中文逗号
                stocks = re.split(r'[,，\s]+', record.buy_stocks.strip())
                
                for stock in stocks:
                    stock = stock.strip()
                    if stock:  # 过滤空字符串
                        stock_counter[stock] += 1
            
            # 获取所有股票名称列表
            stock_names = [stock_name for stock_name, _ in stock_counter.most_common()]
            
            if not stock_names:
                return [], 0
            
            # 批量查询所有股票的详细统计（性能优化：避免N+1查询）
            import math
            from sqlalchemy import case
            
            # 一次性查询所有股票的所有交易记录
            all_details = db.query(ActiveBranchDetail).filter(
                ActiveBranchDetail.stock_name.in_(stock_names),
                ActiveBranchDetail.date == target_date
            ).all()
            
            # 按股票名称分组统计
            stock_stats = {}
            for stock_name in stock_names:
                stock_stats[stock_name] = {
                    "buy_branch_codes": set(),
                    "sell_branch_codes": set(),
                    "net_buy_amount": 0.0,
                    "net_sell_amount": 0.0,
                }
            
            # 遍历所有记录，统计每个股票的数据
            for detail in all_details:
                stock_name = detail.stock_name
                if stock_name not in stock_stats:
                    continue
                
                stats = stock_stats[stock_name]
                institution_code = detail.institution_code
                
                # 安全地获取买入金额和卖出金额
                try:
                    buy_amount = float(detail.buy_amount) if detail.buy_amount else 0.0
                    if math.isnan(buy_amount) or math.isinf(buy_amount):
                        buy_amount = 0.0
                except (ValueError, TypeError, decimal.InvalidOperation):
                    buy_amount = 0.0
                
                try:
                    sell_amount = float(detail.sell_amount) if detail.sell_amount else 0.0
                    if math.isnan(sell_amount) or math.isinf(sell_amount):
                        sell_amount = 0.0
                except (ValueError, TypeError, decimal.InvalidOperation):
                    sell_amount = 0.0
                
                # 统计买入营业部
                if buy_amount > 0:
                    stats["buy_branch_codes"].add(institution_code)
                    # 计算净买入额（买入金额 - 卖出金额）
                    net_buy = buy_amount - sell_amount
                    if not (math.isinf(net_buy) or math.isnan(net_buy)):
                        stats["net_buy_amount"] += net_buy
                
                # 统计卖出营业部
                if sell_amount > 0:
                    stats["sell_branch_codes"].add(institution_code)
                    # 计算净卖出额（卖出金额 - 买入金额）
                    net_sell = sell_amount - buy_amount
                    if not (math.isinf(net_sell) or math.isnan(net_sell)):
                        stats["net_sell_amount"] += net_sell
            
            # 构建统计结果
            statistics = []
            for stock_name in stock_names:
                stats = stock_stats[stock_name]
                statistics.append({
                    "stock_name": stock_name,
                    "appear_count": stock_counter[stock_name],
                    "buy_branch_count": len(stats["buy_branch_codes"]),
                    "sell_branch_count": len(stats["sell_branch_codes"]),
                    "net_buy_amount": stats["net_buy_amount"],
                    "net_sell_amount": stats["net_sell_amount"],
                })
            
            # 按出现次数倒序排序
            statistics.sort(key=lambda x: x["appear_count"], reverse=True)
            
            # 分页
            total = len(statistics)
            offset = (page - 1) * page_size
            paginated_statistics = statistics[offset:offset + page_size]
            
            return paginated_statistics, total
            
        except Exception as e:
            print(f"[ActiveBranchService] 统计买入股票出现次数失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def get_branches_by_stock_name(
        db: Session,
        stock_name: str,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ActiveBranch], int]:
        """
        根据股票名称查询买入该股票的所有营业部记录
        
        Args:
            db: 数据库会话
            stock_name: 股票名称
            target_date: 目标日期，None表示使用最新日期
            page: 页码
            page_size: 每页数量
            
        Returns:
            (营业部记录列表, 总数)
        """
        try:
            # 获取目标日期
            if not target_date:
                latest_date_subquery = db.query(func.max(ActiveBranch.date)).scalar()
                if not latest_date_subquery:
                    return [], 0
                target_date = latest_date_subquery
            
            # 查询指定日期且buy_stocks字段包含该股票名称的所有营业部记录
            # 先查询所有记录，然后在内存中过滤以确保精确匹配
            all_records = db.query(ActiveBranch).filter(
                ActiveBranch.date == target_date,
                ActiveBranch.buy_stocks.isnot(None),
                ActiveBranch.buy_stocks != ''
            ).all()
            
            # 过滤：确保股票名称精确匹配
            matching_records = []
            for record in all_records:
                if not record.buy_stocks:
                    continue
                # 解析buy_stocks字段，检查是否包含该股票名称
                stocks = re.split(r'[,，\s]+', record.buy_stocks.strip())
                if stock_name in [s.strip() for s in stocks]:
                    matching_records.append(record)
            
            # 按净额排序
            matching_records.sort(key=lambda x: x.net_amount if x.net_amount else 0, reverse=True)
            
            # 计算总数
            total = len(matching_records)
            
            # 分页
            offset = (page - 1) * page_size
            paginated_records = matching_records[offset:offset + page_size]
            
            return paginated_records, total
            
        except Exception as e:
            print(f"[ActiveBranchService] 查询买入股票 {stock_name} 的营业部记录失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise