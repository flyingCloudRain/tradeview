"""
机构交易统计服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List, Tuple
from datetime import date, datetime, timedelta
import pandas as pd

from app.models.lhb import InstitutionTradingStatistics
from app.utils.akshare_utils import safe_akshare_call
from app.utils.sync_result import SyncResult
import akshare as ak


class InstitutionTradingService:
    """机构交易统计服务类"""
    
    @staticmethod
    def sync_data(db: Session, target_date: date) -> SyncResult:
        """
        同步机构交易统计数据（从 stock_lhb_jgmmtj_em 获取）
        
        Args:
            db: 数据库会话
            target_date: 目标日期
            
        Returns:
            SyncResult: 同步结果
        """
        try:
            # 计算日期范围（默认获取最近两周的数据）
            end_date = target_date
            start_date = end_date - timedelta(days=14)
            
            # 转换为字符串格式 YYYYMMDD
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")
            
            print(f"[InstitutionTradingService] 开始同步机构交易统计数据: {start_date_str} - {end_date_str}")
            
            # 调用 akshare 接口
            df = safe_akshare_call(ak.stock_lhb_jgmmtj_em, start_date=start_date_str, end_date=end_date_str)
            
            if df is None or df.empty:
                return SyncResult.failure_result("数据为空", "未获取到机构交易统计数据")
            
            print(f"[InstitutionTradingService] 获取到 {len(df)} 条数据")
            
            # 保存数据
            count = InstitutionTradingService.save_data(db, df, target_date)
            
            return SyncResult.success_result(f"成功同步 {count} 条机构交易统计数据")
            
        except Exception as e:
            error_msg = f"同步机构交易统计数据失败: {str(e)}"
            print(f"[InstitutionTradingService] {error_msg}")
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(error_msg, str(e))
    
    @staticmethod
    def save_data(db: Session, df: pd.DataFrame, target_date: date) -> int:
        """
        保存机构交易统计数据到数据库
        
        Args:
            db: 数据库会话
            df: 数据DataFrame
            target_date: 目标日期（只保存该日期的数据）
            
        Returns:
            int: 保存的记录数
        """
        count = 0
        
        # 确保日期列为日期格式
        if "上榜日期" in df.columns:
            df["上榜日期"] = pd.to_datetime(df["上榜日期"]).dt.date
        
        # 只保存目标日期的数据
        df_filtered = df[df["上榜日期"] == target_date]
        
        if df_filtered.empty:
            print(f"[InstitutionTradingService] 日期 {target_date.strftime('%Y-%m-%d')} 无数据")
            return 0
        
        print(f"[InstitutionTradingService] 保存 {len(df_filtered)} 条数据（日期: {target_date.strftime('%Y-%m-%d')}）")
        
        # 对同一股票的多条记录进行合并（合并上榜原因）
        # 按股票代码分组，合并上榜原因
        df_grouped = df_filtered.groupby("代码").agg({
            "名称": "first",
            "收盘价": "first",
            "涨跌幅": "first",
            "买方机构数": "first",
            "卖方机构数": "first",
            "机构买入总额": "first",
            "机构卖出总额": "first",
            "机构买入净额": "first",
            "市场总成交额": "first",
            "机构净买额占总成交额比": "first",
            "换手率": "first",
            "流通市值": "first",
            "上榜原因": lambda x: "；".join([str(r) for r in x if pd.notna(r) and str(r).strip()])
        }).reset_index()
        
        print(f"[InstitutionTradingService] 合并后 {len(df_grouped)} 条数据（去重后）")
        
        for _, row in df_grouped.iterrows():
            try:
                # 解析数据
                stock_code = str(row.get("代码", "")).strip()
                stock_name = str(row.get("名称", "")).strip()
                
                if not stock_code or not stock_name:
                    continue
                
                # 检查是否已存在
                existing = db.query(InstitutionTradingStatistics).filter(
                    and_(
                        InstitutionTradingStatistics.date == target_date,
                        InstitutionTradingStatistics.stock_code == stock_code
                    )
                ).first()
                
                # 解析数值字段
                close_price = row.get("收盘价", None)
                change_percent = row.get("涨跌幅", None)
                buyer_institution_count = row.get("买方机构数", None)
                seller_institution_count = row.get("卖方机构数", None)
                institution_buy_amount = row.get("机构买入总额", None)
                institution_sell_amount = row.get("机构卖出总额", None)
                institution_net_buy_amount = row.get("机构买入净额", None)
                market_total_amount = row.get("市场总成交额", None)
                net_buy_ratio_raw = row.get("机构净买额占总成交额比", None)
                turnover_rate = row.get("换手率", None)
                circulation_market_value = row.get("流通市值", None)
                reason = str(row.get("上榜原因", "")).strip() if pd.notna(row.get("上榜原因")) else None
                
                # 验证和清理净买额占比数据
                net_buy_ratio = None
                if net_buy_ratio_raw is not None and pd.notna(net_buy_ratio_raw):
                    try:
                        net_buy_ratio_value = float(net_buy_ratio_raw)
                        # 检查是否为有效数值
                        import math
                        if not math.isnan(net_buy_ratio_value) and not math.isinf(net_buy_ratio_value):
                            # 原始数据中的占比已经是百分比形式，验证范围是否合理（-100% 到 100%）
                            # 允许稍微超出范围以处理数据异常情况
                            if -200 <= net_buy_ratio_value <= 200:
                                net_buy_ratio = round(net_buy_ratio_value, 4)
                            else:
                                print(f"[InstitutionTradingService] 警告: 股票 {stock_code} 原始净买额占比异常: {net_buy_ratio_value}%，将重新计算")
                                # 如果原始占比异常，尝试重新计算
                                if institution_net_buy_amount is not None and market_total_amount is not None and market_total_amount > 0:
                                    recalculated = (institution_net_buy_amount / market_total_amount) * 100
                                    if -200 <= recalculated <= 200:
                                        net_buy_ratio = round(recalculated, 4)
                    except (ValueError, TypeError) as e:
                        print(f"[InstitutionTradingService] 解析净买额占比失败: {str(e)}, 股票: {stock_code}, 原始值: {net_buy_ratio_raw}")
                        # 如果解析失败，尝试重新计算
                        if institution_net_buy_amount is not None and market_total_amount is not None and market_total_amount > 0:
                            try:
                                recalculated = (institution_net_buy_amount / market_total_amount) * 100
                                if -200 <= recalculated <= 200:
                                    net_buy_ratio = round(recalculated, 4)
                            except Exception:
                                pass
                
                # 如果净买额占比仍为None，但有净买入和市场成交额数据，尝试计算
                if net_buy_ratio is None and institution_net_buy_amount is not None and market_total_amount is not None and market_total_amount > 0:
                    try:
                        recalculated = (institution_net_buy_amount / market_total_amount) * 100
                        import math
                        if not math.isnan(recalculated) and not math.isinf(recalculated) and -200 <= recalculated <= 200:
                            net_buy_ratio = round(recalculated, 4)
                    except Exception:
                        pass
                
                if existing:
                    # 更新
                    existing.stock_name = stock_name
                    if close_price is not None:
                        existing.close_price = close_price
                    if change_percent is not None:
                        existing.change_percent = change_percent
                    if buyer_institution_count is not None:
                        existing.buyer_institution_count = int(buyer_institution_count)
                    if seller_institution_count is not None:
                        existing.seller_institution_count = int(seller_institution_count)
                    if institution_buy_amount is not None:
                        existing.institution_buy_amount = institution_buy_amount
                    if institution_sell_amount is not None:
                        existing.institution_sell_amount = institution_sell_amount
                    if institution_net_buy_amount is not None:
                        existing.institution_net_buy_amount = institution_net_buy_amount
                    if market_total_amount is not None:
                        existing.market_total_amount = market_total_amount
                    if net_buy_ratio is not None:
                        existing.net_buy_ratio = net_buy_ratio
                    if turnover_rate is not None:
                        existing.turnover_rate = turnover_rate
                    if circulation_market_value is not None:
                        existing.circulation_market_value = circulation_market_value
                    if reason:
                        existing.reason = reason
                else:
                    # 新建
                    stats = InstitutionTradingStatistics(
                        date=target_date,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        close_price=close_price,
                        change_percent=change_percent,
                        buyer_institution_count=int(buyer_institution_count) if buyer_institution_count is not None else None,
                        seller_institution_count=int(seller_institution_count) if seller_institution_count is not None else None,
                        institution_buy_amount=institution_buy_amount,
                        institution_sell_amount=institution_sell_amount,
                        institution_net_buy_amount=institution_net_buy_amount,
                        market_total_amount=market_total_amount,
                        net_buy_ratio=net_buy_ratio,
                        turnover_rate=turnover_rate,
                        circulation_market_value=circulation_market_value,
                        reason=reason,
                    )
                    db.add(stats)
                
                count += 1
                
            except Exception as e:
                print(f"[InstitutionTradingService] 保存数据失败: {str(e)}, row: {row.to_dict()}")
                import traceback
                traceback.print_exc()
                continue
        
        db.commit()
        return count
    
    @staticmethod
    def get_list(
        db: Session,
        target_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> Tuple[List[InstitutionTradingStatistics], int]:
        """
        获取机构交易统计列表
        
        Args:
            db: 数据库会话
            target_date: 目标日期，None表示使用最近的数据（与start_date/end_date互斥）
            start_date: 开始日期（时间段查询）
            end_date: 结束日期（时间段查询）
            stock_code: 股票代码过滤
            stock_name: 股票名称过滤（模糊查询）
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
            
        Returns:
            Tuple[List[InstitutionTradingStatistics], int]: (数据列表, 总数)
        """
        try:
            # 构建基础查询
            query = db.query(InstitutionTradingStatistics)
            
            # 日期过滤：优先使用时间段查询，其次使用单日查询
            if start_date or end_date:
                # 时间段查询
                if start_date:
                    query = query.filter(InstitutionTradingStatistics.date >= start_date)
                if end_date:
                    query = query.filter(InstitutionTradingStatistics.date <= end_date)
            elif target_date:
                # 单日查询
                query = query.filter(InstitutionTradingStatistics.date == target_date)
            else:
                # 如果没有指定日期，使用最近的日期
                latest_date = db.query(func.max(InstitutionTradingStatistics.date)).scalar()
                if latest_date:
                    query = query.filter(InstitutionTradingStatistics.date == latest_date)
            
            # 股票代码过滤
            if stock_code and stock_code.strip():
                query = query.filter(InstitutionTradingStatistics.stock_code == stock_code.strip())
            
            # 股票名称模糊查询
            if stock_name and stock_name.strip():
                stock_name_clean = stock_name.strip()
                query = query.filter(
                    func.lower(InstitutionTradingStatistics.stock_name).like(f"%{stock_name_clean.lower()}%")
                )
            
            # 排序
            if sort_by:
                sort_column = getattr(InstitutionTradingStatistics, sort_by, None)
                if sort_column:
                    if order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
            else:
                # 默认按机构买入净额排序
                from sqlalchemy import nullslast
                query = query.order_by(nullslast(desc(InstitutionTradingStatistics.institution_net_buy_amount)))
            
            # 分页
            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size).all()
            total = query.count()
            
            return items, total
            
        except Exception as e:
            print(f"[InstitutionTradingService] 查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return [], 0
    
    @staticmethod
    def get_aggregated_statistics(
        db: Session,
        start_date: date,
        end_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        min_appear_count: Optional[int] = None,
        max_appear_count: Optional[int] = None,
        min_total_net_buy_amount: Optional[float] = None,
        max_total_net_buy_amount: Optional[float] = None,
        min_total_buy_amount: Optional[float] = None,
        max_total_buy_amount: Optional[float] = None,
        min_total_sell_amount: Optional[float] = None,
        max_total_sell_amount: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> Tuple[List[dict], int]:
        """
        获取时间段内的机构交易统计汇总（按股票代码聚合）
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            stock_code: 股票代码过滤
            stock_name: 股票名称过滤（模糊查询）
            min_appear_count: 最小上榜次数
            max_appear_count: 最大上榜次数
            min_total_net_buy_amount: 最小累计净买入金额
            max_total_net_buy_amount: 最大累计净买入金额
            min_total_buy_amount: 最小累计买入金额
            max_total_buy_amount: 最大累计买入金额
            min_total_sell_amount: 最小累计卖出金额
            max_total_sell_amount: 最大累计卖出金额
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段（支持：institution_net_buy_amount, institution_buy_amount, institution_sell_amount等）
            order: 排序方向
            
        Returns:
            Tuple[List[dict], int]: (汇总数据列表, 总数)
        """
        try:
            # 构建基础查询，保存label对象用于排序
            appear_count_label = func.count(InstitutionTradingStatistics.id).label('appear_count')
            total_buy_amount_label = func.sum(InstitutionTradingStatistics.institution_buy_amount).label('total_buy_amount')
            total_sell_amount_label = func.sum(InstitutionTradingStatistics.institution_sell_amount).label('total_sell_amount')
            total_net_buy_amount_label = func.sum(InstitutionTradingStatistics.institution_net_buy_amount).label('total_net_buy_amount')
            
            query = db.query(
                InstitutionTradingStatistics.stock_code,
                InstitutionTradingStatistics.stock_name,
                appear_count_label,  # 上榜次数
                total_buy_amount_label,
                total_sell_amount_label,
                total_net_buy_amount_label,
                func.sum(InstitutionTradingStatistics.market_total_amount).label('total_market_amount'),  # 累计市场总成交额
                func.avg(InstitutionTradingStatistics.close_price).label('avg_close_price'),
                func.avg(InstitutionTradingStatistics.circulation_market_value).label('avg_circulation_market_value'),  # 平均流通市值
                func.avg(InstitutionTradingStatistics.turnover_rate).label('avg_turnover_rate'),  # 平均换手率
                func.max(InstitutionTradingStatistics.change_percent).label('max_change_percent'),
                func.min(InstitutionTradingStatistics.change_percent).label('min_change_percent'),
                func.max(InstitutionTradingStatistics.date).label('latest_date'),
                func.min(InstitutionTradingStatistics.date).label('earliest_date'),
            ).filter(
                and_(
                    InstitutionTradingStatistics.date >= start_date,
                    InstitutionTradingStatistics.date <= end_date
                )
            )
            
            # 股票代码过滤
            if stock_code and stock_code.strip():
                query = query.filter(InstitutionTradingStatistics.stock_code == stock_code.strip())
            
            # 股票名称模糊查询
            if stock_name and stock_name.strip():
                stock_name_clean = stock_name.strip()
                query = query.filter(
                    func.lower(InstitutionTradingStatistics.stock_name).like(f"%{stock_name_clean.lower()}%")
                )
            
            # 按股票代码和名称分组
            query = query.group_by(
                InstitutionTradingStatistics.stock_code,
                InstitutionTradingStatistics.stock_name
            )
            
            # 多条件过滤（需要在分组后使用HAVING子句）
            # 注意：在SQLAlchemy中，having()可以直接使用label对象
            if min_appear_count is not None:
                query = query.having(appear_count_label >= min_appear_count)
            if max_appear_count is not None:
                query = query.having(appear_count_label <= max_appear_count)
            if min_total_net_buy_amount is not None:
                query = query.having(total_net_buy_amount_label >= min_total_net_buy_amount)
            if max_total_net_buy_amount is not None:
                query = query.having(total_net_buy_amount_label <= max_total_net_buy_amount)
            if min_total_buy_amount is not None:
                query = query.having(total_buy_amount_label >= min_total_buy_amount)
            if max_total_buy_amount is not None:
                query = query.having(total_buy_amount_label <= max_total_buy_amount)
            if min_total_sell_amount is not None:
                query = query.having(total_sell_amount_label >= min_total_sell_amount)
            if max_total_sell_amount is not None:
                query = query.having(total_sell_amount_label <= max_total_sell_amount)
            
            # 排序 - 使用label对象
            # 注意：total_market_amount已经在query中定义了，这里需要重新定义label用于排序
            total_market_amount_label_for_sort = func.sum(InstitutionTradingStatistics.market_total_amount).label('total_market_amount_for_sort')
            sort_mapping = {
                'institution_net_buy_amount': total_net_buy_amount_label,
                'institution_buy_amount': total_buy_amount_label,
                'institution_sell_amount': total_sell_amount_label,
                'appear_count': appear_count_label,
                'total_market_amount': total_market_amount_label_for_sort,
            }
            
            # net_buy_ratio 是计算字段，需要在Python层面排序，先获取所有数据
            need_python_sort = (sort_by == 'net_buy_ratio')
            
            if sort_by and sort_by in sort_mapping:
                sort_column = sort_mapping[sort_by]
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            elif not need_python_sort:
                # 默认排序：按上榜次数倒序（从多到少）
                query = query.order_by(desc(appear_count_label))
            
            # 安全转换浮点数的辅助函数
            def safe_float(value):
                """安全地将值转换为float，处理NaN和Infinity"""
                if value is None:
                    return None
                try:
                    result = float(value)
                    # 检查是否为NaN或Infinity
                    import math
                    if math.isnan(result) or math.isinf(result):
                        return None
                    return result
                except (ValueError, TypeError):
                    return None
            
            # 获取总数
            total = query.count()
            
            # 如果需要按net_buy_ratio排序，需要先获取所有数据，然后在Python中排序
            if need_python_sort:
                # 获取所有数据（不分页）
                all_results = query.all()
                
                # 转换为字典列表并计算net_buy_ratio
                all_items = []
                for row in all_results:
                    total_net_buy = safe_float(row.total_net_buy_amount)
                    total_market = safe_float(row.total_market_amount)
                    
                    # 计算机构净买额占总成交额比（百分比）
                    net_buy_ratio = None
                    if total_net_buy is not None and total_market is not None:
                        if total_market > 0:
                            try:
                                ratio = (total_net_buy / total_market) * 100
                                import math
                                if not math.isnan(ratio) and not math.isinf(ratio):
                                    if -200 <= ratio <= 200:
                                        net_buy_ratio = round(ratio, 4)
                            except (ZeroDivisionError, ValueError, TypeError):
                                pass
                    
                    # 对于None值，使用极值以便排序（None值会排到最后）
                    # 无论升序还是降序，None值都应该排在最后，所以统一使用float('inf')
                    sort_value = net_buy_ratio if net_buy_ratio is not None else float('inf')
                    
                    all_items.append({
                        'row': row,
                        'net_buy_ratio': sort_value,
                    })
                
                # 在Python中按net_buy_ratio排序
                all_items.sort(key=lambda x: x['net_buy_ratio'], reverse=(order == "desc"))
                
                # 分页
                offset = (page - 1) * page_size
                paginated_items = all_items[offset:offset + page_size]
                results = [item['row'] for item in paginated_items]
            else:
                # 分页
                offset = (page - 1) * page_size
                results = query.offset(offset).limit(page_size).all()
            
            # 转换为字典列表
            items = []
            for row in results:
                total_net_buy = safe_float(row.total_net_buy_amount)
                total_market = safe_float(row.total_market_amount)
                
                # 计算机构净买额占总成交额比（百分比）
                net_buy_ratio = None
                if total_net_buy is not None and total_market is not None:
                    # 检查市场总成交额是否有效（必须大于0）
                    if total_market > 0:
                        try:
                            ratio = (total_net_buy / total_market) * 100
                            # 确保比率也是有效的
                            import math
                            if not math.isnan(ratio) and not math.isinf(ratio):
                                # 验证占比是否在合理范围内（-100% 到 100%之间，但允许稍微超出）
                                # 因为净买入可能超过市场成交额（理论上不应该，但数据可能有误）
                                if -200 <= ratio <= 200:  # 允许一定的容错范围
                                    net_buy_ratio = round(ratio, 4)
                                else:
                                    # 如果占比超出合理范围，记录警告但不设置值
                                    print(f"[InstitutionTradingService] 警告: 股票 {row.stock_code} 净买额占比异常: {ratio}% (净买入: {total_net_buy}, 市场成交: {total_market})")
                        except (ZeroDivisionError, ValueError, TypeError) as e:
                            print(f"[InstitutionTradingService] 计算净买额占比失败: {str(e)}, 股票: {row.stock_code}, 净买入: {total_net_buy}, 市场成交: {total_market}")
                    elif total_market == 0:
                        # 市场成交额为0，无法计算占比
                        print(f"[InstitutionTradingService] 警告: 股票 {row.stock_code} 市场总成交额为0，无法计算净买额占比")
                    else:
                        # 市场成交额为负数，数据异常
                        print(f"[InstitutionTradingService] 警告: 股票 {row.stock_code} 市场总成交额为负数: {total_market}")
                
                items.append({
                    'stock_code': row.stock_code,
                    'stock_name': row.stock_name,
                    'appear_count': row.appear_count,
                    'total_buy_amount': safe_float(row.total_buy_amount),
                    'total_sell_amount': safe_float(row.total_sell_amount),
                    'total_net_buy_amount': total_net_buy,  # 净买入额
                    'total_market_amount': total_market,  # 累计市场总成交额
                    'net_buy_ratio': net_buy_ratio,  # 机构净买额占总成交额比（%）
                    'avg_close_price': safe_float(row.avg_close_price),
                    'avg_circulation_market_value': safe_float(row.avg_circulation_market_value),  # 平均流通市值
                    'avg_turnover_rate': safe_float(row.avg_turnover_rate),  # 平均换手率
                    'max_change_percent': safe_float(row.max_change_percent),
                    'min_change_percent': safe_float(row.min_change_percent),
                    'earliest_date': row.earliest_date,
                    'latest_date': row.latest_date,
                })
            
            return items, total
            
        except Exception as e:
            print(f"[InstitutionTradingService] 聚合统计查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise