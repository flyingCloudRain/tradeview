"""
活跃营业部交易详情服务
从 stock_lhb_yyb_detail_em 获取数据并存储到数据库（2026年1月开始）
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from app.database.session import SessionLocal
from app.models.lhb import ActiveBranchDetail, ActiveBranch
from app.utils.akshare_utils import safe_akshare_call
from app.utils.sync_result import SyncResult
import akshare as ak


class ActiveBranchDetailService:
    """活跃营业部交易详情服务类"""
    
    # 数据存储起始日期：2026年1月1日
    STORAGE_START_DATE = date(2026, 1, 1)
    
    @staticmethod
    def should_store_data(target_date: date) -> bool:
        """判断是否应该存储数据（2026年1月1日及之后）"""
        return target_date >= ActiveBranchDetailService.STORAGE_START_DATE
    
    @staticmethod
    def get_list(
        db: Session,
        institution_code: Optional[str] = None,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc",
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
    ) -> tuple[List[ActiveBranchDetail], int]:
        """
        获取营业部交易详情列表
        
        Args:
            db: 数据库会话
            institution_code: 营业部代码（可选，如果提供则只查询该营业部的数据）
            target_date: 目标日期，None表示获取所有日期
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
            stock_code: 股票代码过滤
            stock_name: 股票名称过滤（模糊查询）
        """
        try:
            query = db.query(ActiveBranchDetail)
            
            # 营业部代码过滤（可选）
            if institution_code:
                query = query.filter(ActiveBranchDetail.institution_code == institution_code)
            
            # 日期过滤
            if target_date:
                query = query.filter(ActiveBranchDetail.date == target_date)
            
            # 股票代码过滤
            if stock_code:
                query = query.filter(ActiveBranchDetail.stock_code == stock_code.strip())
            
            # 股票名称过滤（精确匹配）
            if stock_name:
                query = query.filter(ActiveBranchDetail.stock_name == stock_name.strip())
            
            # 排序
            if sort_by:
                sort_column = getattr(ActiveBranchDetail, sort_by, None)
                if sort_column is not None:
                    if order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                else:
                    # 默认按日期倒序
                    query = query.order_by(desc(ActiveBranchDetail.date))
            else:
                # 默认按日期倒序
                query = query.order_by(desc(ActiveBranchDetail.date))
            
            # 总数
            total = query.count()
            
            # 分页
            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size).all()
            
            return items, total
            
        except Exception as e:
            print(f"[ActiveBranchDetailService] 查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return [], 0
    
    @staticmethod
    def get_statistics(
        db: Session,
        institution_code: Optional[str] = None,
        target_date: Optional[date] = None,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
    ) -> dict:
        """
        获取营业部交易详情统计信息
        
        Args:
            db: 数据库会话
            institution_code: 营业部代码（可选）
            target_date: 目标日期，None表示获取所有日期
            stock_code: 股票代码过滤
            stock_name: 股票名称过滤（精确匹配）
        
        Returns:
            统计信息字典，包含：
            - buy_branch_count: 买入营业部个数（有买入金额的营业部）
            - sell_branch_count: 卖出营业部个数（有卖出金额的营业部）
            - total_buy_amount: 买入总金额
            - total_sell_amount: 卖出总金额
        """
        try:
            from sqlalchemy import func, distinct
            
            query = db.query(ActiveBranchDetail)
            
            # 营业部代码过滤（可选）
            if institution_code:
                query = query.filter(ActiveBranchDetail.institution_code == institution_code)
            
            # 日期过滤
            if target_date:
                query = query.filter(ActiveBranchDetail.date == target_date)
            
            # 股票代码过滤
            if stock_code:
                query = query.filter(ActiveBranchDetail.stock_code == stock_code.strip())
            
            # 股票名称过滤（精确匹配）
            if stock_name:
                query = query.filter(ActiveBranchDetail.stock_name == stock_name.strip())
            
            # 统计买入营业部个数（有买入金额且大于0的营业部）
            buy_branches = query.filter(
                ActiveBranchDetail.buy_amount.isnot(None),
                ActiveBranchDetail.buy_amount > 0
            ).with_entities(
                distinct(ActiveBranchDetail.institution_code)
            ).all()
            buy_branch_count = len(buy_branches)
            
            # 统计卖出营业部个数（有卖出金额且大于0的营业部）
            sell_branches = query.filter(
                ActiveBranchDetail.sell_amount.isnot(None),
                ActiveBranchDetail.sell_amount > 0
            ).with_entities(
                distinct(ActiveBranchDetail.institution_code)
            ).all()
            sell_branch_count = len(sell_branches)
            
            # 统计买入总金额
            total_buy_result = query.with_entities(
                func.sum(ActiveBranchDetail.buy_amount)
            ).scalar()
            total_buy_amount = float(total_buy_result) if total_buy_result else 0.0
            
            # 统计卖出总金额
            total_sell_result = query.with_entities(
                func.sum(ActiveBranchDetail.sell_amount)
            ).scalar()
            total_sell_amount = float(total_sell_result) if total_sell_result else 0.0
            
            return {
                "buy_branch_count": buy_branch_count,
                "sell_branch_count": sell_branch_count,
                "total_buy_amount": total_buy_amount,
                "total_sell_amount": total_sell_amount,
            }
            
        except Exception as e:
            print(f"[ActiveBranchDetailService] 统计失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "buy_branch_count": 0,
                "sell_branch_count": 0,
                "total_buy_amount": 0.0,
                "total_sell_amount": 0.0,
            }
    
    @staticmethod
    def sync_institution_data(
        db: Session,
        institution_code: str,
        institution_name: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> int:
        """
        同步单个营业部的交易详情数据
        
        Args:
            db: 数据库会话
            institution_code: 营业部代码
            institution_name: 营业部名称（可选，用于填充）
            target_date: 目标日期，None表示同步所有数据（但只存储2026年1月1日及之后的数据）
        
        Returns:
            保存的记录数
        """
        try:
            print(f"[ActiveBranchDetailService] 开始同步营业部 {institution_code} 的交易详情...")
            
            # 调用 akshare API 获取数据
            df = safe_akshare_call(ak.stock_lhb_yyb_detail_em, symbol=institution_code)
            if df is None or df.empty:
                print(f"[ActiveBranchDetailService] 营业部 {institution_code} 无数据")
                return 0
            
            # 重命名并标准化列名
            rename_map = {
                "交易日期": "date",
                "股票代码": "stock_code",
                "股票名称": "stock_name",
                "涨跌幅": "change_percent",
                "买入金额": "buy_amount",
                "卖出金额": "sell_amount",
                "净额": "net_amount",
                "上榜原因": "reason",
                "1日后涨跌幅": "after_1d",
                "2日后涨跌幅": "after_2d",
                "3日后涨跌幅": "after_3d",
                "5日后涨跌幅": "after_5d",
                "10日后涨跌幅": "after_10d",
                "20日后涨跌幅": "after_20d",
                "30日后涨跌幅": "after_30d",
            }
            df = df.rename(columns=rename_map)
            
            # 转换日期格式
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # 日期过滤（如果指定了目标日期）
            if target_date:
                df = df[df["date"] == target_date]
            
            # 只保留2026年1月1日及之后的数据
            df = df[df["date"] >= ActiveBranchDetailService.STORAGE_START_DATE]
            
            if df.empty:
                print(f"[ActiveBranchDetailService] 营业部 {institution_code} 在指定日期范围内无数据需要存储")
                return 0
            
            # 对数据进行去重：同一营业部、同一日期、同一股票代码只保留一条记录
            # 如果有多条记录（不同上榜原因），保留第一条，但合并上榜原因
            if len(df) > 0:
                # 按日期和股票代码分组，合并上榜原因
                df_grouped = df.groupby(["date", "stock_code"]).agg({
                    "stock_name": "first",
                    "change_percent": "first",
                    "buy_amount": "first",
                    "sell_amount": "first",
                    "net_amount": "first",
                    "reason": lambda x: "；".join([str(r) for r in x.unique() if pd.notna(r)]),  # 合并多个上榜原因
                    "after_1d": "first",
                    "after_2d": "first",
                    "after_3d": "first",
                    "after_5d": "first",
                    "after_10d": "first",
                    "after_20d": "first",
                    "after_30d": "first",
                }).reset_index()
                df = df_grouped
                print(f"[ActiveBranchDetailService] 营业部 {institution_code} 数据去重: {len(df)} 条记录")
            
            # 获取营业部名称（如果未提供，尝试从数据库获取）
            if not institution_name:
                active_branch = db.query(ActiveBranch).filter(
                    ActiveBranch.institution_code == institution_code
                ).first()
                if active_branch:
                    institution_name = active_branch.institution_name
            
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    # 检查是否已存在
                    existing = db.query(ActiveBranchDetail).filter(
                        and_(
                            ActiveBranchDetail.institution_code == institution_code,
                            ActiveBranchDetail.date == row.get("date"),
                            ActiveBranchDetail.stock_code == str(row.get("stock_code") or "").zfill(6)
                        )
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.institution_name = institution_name
                        existing.stock_name = row.get("stock_name")
                        existing.change_percent = row.get("change_percent")
                        existing.buy_amount = row.get("buy_amount")
                        existing.sell_amount = row.get("sell_amount")
                        existing.net_amount = row.get("net_amount")
                        existing.reason = row.get("reason")
                        existing.after_1d = row.get("after_1d")
                        existing.after_2d = row.get("after_2d")
                        existing.after_3d = row.get("after_3d")
                        existing.after_5d = row.get("after_5d")
                        existing.after_10d = row.get("after_10d")
                        existing.after_20d = row.get("after_20d")
                        existing.after_30d = row.get("after_30d")
                    else:
                        # 创建新记录
                        detail = ActiveBranchDetail(
                            institution_code=institution_code,
                            institution_name=institution_name,
                            date=row.get("date"),
                            stock_code=str(row.get("stock_code") or "").zfill(6),
                            stock_name=row.get("stock_name"),
                            change_percent=row.get("change_percent"),
                            buy_amount=row.get("buy_amount"),
                            sell_amount=row.get("sell_amount"),
                            net_amount=row.get("net_amount"),
                            reason=row.get("reason"),
                            after_1d=row.get("after_1d"),
                            after_2d=row.get("after_2d"),
                            after_3d=row.get("after_3d"),
                            after_5d=row.get("after_5d"),
                            after_10d=row.get("after_10d"),
                            after_20d=row.get("after_20d"),
                            after_30d=row.get("after_30d"),
                        )
                        db.add(detail)
                    
                    saved_count += 1
                    
                except Exception as e:
                    # 如果是唯一约束冲突，尝试更新现有记录
                    if "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                        try:
                            # 再次查询并更新
                            existing = db.query(ActiveBranchDetail).filter(
                                and_(
                                    ActiveBranchDetail.institution_code == institution_code,
                                    ActiveBranchDetail.date == row.get("date"),
                                    ActiveBranchDetail.stock_code == str(row.get("stock_code") or "").zfill(6)
                                )
                            ).first()
                            if existing:
                                existing.institution_name = institution_name
                                existing.stock_name = row.get("stock_name")
                                existing.change_percent = row.get("change_percent")
                                existing.buy_amount = row.get("buy_amount")
                                existing.sell_amount = row.get("sell_amount")
                                existing.net_amount = row.get("net_amount")
                                existing.reason = row.get("reason")
                                existing.after_1d = row.get("after_1d")
                                existing.after_2d = row.get("after_2d")
                                existing.after_3d = row.get("after_3d")
                                existing.after_5d = row.get("after_5d")
                                existing.after_10d = row.get("after_10d")
                                existing.after_20d = row.get("after_20d")
                                existing.after_30d = row.get("after_30d")
                                saved_count += 1
                                continue
                        except Exception as update_error:
                            print(f"[ActiveBranchDetailService] 更新记录也失败: {str(update_error)}")
                    
                    print(f"[ActiveBranchDetailService] 保存记录失败: {str(e)[:200]}")
                    continue
            
            try:
                db.commit()
            except Exception as commit_error:
                print(f"[ActiveBranchDetailService] 提交失败: {str(commit_error)}")
                db.rollback()
                raise
            print(f"[ActiveBranchDetailService] 营业部 {institution_code} 同步完成，保存 {saved_count} 条记录")
            return saved_count
            
        except Exception as e:
            print(f"[ActiveBranchDetailService] 同步营业部 {institution_code} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return 0
    
    @staticmethod
    def sync_date_data(
        db: Session,
        target_date: date
    ) -> SyncResult:
        """
        同步指定日期的活跃营业部交易详情
        只同步卖出个股数量前10的活跃营业部，按照卖出个数降序排序，优先处理卖出最多的营业部
        
        Args:
            db: 数据库会话
            target_date: 目标日期
        
        Returns:
            SyncResult: 同步结果，包含保存的总记录数
        """
        # 只同步2026年1月1日及之后的数据
        if not ActiveBranchDetailService.should_store_data(target_date):
            print(f"[ActiveBranchDetailService] 日期 {target_date} 早于存储起始日期 {ActiveBranchDetailService.STORAGE_START_DATE}，跳过")
            return SyncResult.success_result(
                message=f"日期 {target_date} 早于存储起始日期，跳过",
                count=0,
            )
        
        try:
            # 获取该日期的活跃营业部，按照卖出个股数降序排序，只取前10个
            # 优先处理卖出个股数量最多的营业部
            active_branches = db.query(ActiveBranch).filter(
                ActiveBranch.date == target_date,
                ActiveBranch.institution_code.isnot(None),
                ActiveBranch.institution_code != "",
                ActiveBranch.sell_stock_count.isnot(None),
                ActiveBranch.sell_stock_count > 0,  # 卖出个股数必须大于0
            ).order_by(
                desc(ActiveBranch.sell_stock_count)  # 按卖出个股数降序排序
            ).limit(10).all()  # 只取前10个
            
            if not active_branches:
                print(f"[ActiveBranchDetailService] 日期 {target_date} 无满足条件的活跃营业部数据（卖出个股数>0）")
                return SyncResult.success_result(
                    message=f"日期 {target_date} 无满足条件的活跃营业部数据（卖出个股数>0）",
                    count=0,
                )
            
            # 打印选中的营业部信息
            print(f"[ActiveBranchDetailService] 选中 {len(active_branches)} 个营业部（按卖出个股数排序，前10名）:")
            for i, branch in enumerate(active_branches, 1):
                print(f"  {i}. {branch.institution_name} ({branch.institution_code}): 卖出个股数={branch.sell_stock_count}")
            
            def sync_branch(branch: ActiveBranch) -> int:
                """线程内同步单个营业部，使用独立数据库会话"""
                thread_db = SessionLocal()
                try:
                    return ActiveBranchDetailService.sync_institution_data(
                        db=thread_db,
                        institution_code=branch.institution_code,
                        institution_name=branch.institution_name,
                        target_date=target_date
                    )
                finally:
                    thread_db.close()
            
            total_saved = 0
            # 自动估算并发度：按CPU核心数，限制上限避免过多并发
            cpu_workers = max(2, (os.cpu_count() or 4))
            max_workers = min(cpu_workers, len(active_branches))
            print(f"[ActiveBranchDetailService] 使用线程池并发同步，workers={max_workers}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(sync_branch, branch) for branch in active_branches]
                for future in as_completed(futures):
                    try:
                        total_saved += future.result()
                    except Exception as e:
                        print(f"[ActiveBranchDetailService] 并发同步失败: {str(e)}")
            
            print(f"[ActiveBranchDetailService] 日期 {target_date} 同步完成，共保存 {total_saved} 条记录")
            return SyncResult.success_result(
                message=f"日期 {target_date} 同步完成",
                count=total_saved,
            )
            
        except Exception as e:
            print(f"[ActiveBranchDetailService] 同步日期 {target_date} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(
                error=str(e),
                message=f"同步日期 {target_date} 失败",
            )
