"""
龙虎榜服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List
from datetime import date
import pandas as pd
import math
import decimal

from app.models.lhb import LhbDetail, LhbInstitution
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class LhbService:
    """龙虎榜服务类"""
    
    @staticmethod
    def get_lhb_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[LhbDetail], int]:
        """
        获取龙虎榜列表（优化版本）
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"查询参数: date={target_date}, stock_code={stock_code}, stock_name={stock_name}, page={page}, page_size={page_size}")
        
        try:
            # 构建基础查询
            query = db.query(LhbDetail).filter(LhbDetail.date == target_date)
            
            # 添加股票代码过滤
            if stock_code and stock_code.strip():
                query = query.filter(LhbDetail.stock_code == stock_code.strip())
            
            # 添加股票名称模糊查询（大小写不敏感）
            if stock_name and stock_name.strip():
                stock_name_clean = stock_name.strip()
                # 使用 func.lower 确保大小写不敏感查询
                query = query.filter(func.lower(LhbDetail.stock_name).like(f"%{stock_name_clean.lower()}%"))
            
            # 排序
            if sort_by:
                sort_column = getattr(LhbDetail, sort_by, None)
                if sort_column:
                    if order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                else:
                    print(f"[LhbService] ⚠️  排序字段 {sort_by} 不存在，使用默认排序")
                    sys.stdout.flush()
            else:
                # 默认按净买额排序，如果为None则放到最后
                from sqlalchemy import nullslast
                query = query.order_by(nullslast(desc(LhbDetail.net_buy_amount)))
            
            # 优化：先获取分页数据，再根据情况决定是否计算总数
            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size + 1).all()  # 多取一条用于判断
            
            # 判断是否有下一页
            has_next = len(items) > page_size
            if has_next:
                items = items[:page_size]  # 只保留当前页的数据
            
            # 计算总数：如果第一页且没有下一页，总数就是当前数据量
            if page == 1 and not has_next:
                total = len(items)
            else:
                # 需要计算总数（但可以优化：如果数据量很大，可以估算）
                total = query.count()
            
            print(f"[LhbService] 查询结果: {len(items)} 条, total: {total} 条")
            if len(items) > 0:
                print(f"[LhbService] 第一条数据: {items[0].stock_name} ({items[0].stock_code})")
            sys.stdout.flush()
            
            # 为每个龙虎榜记录加载概念板块
            from app.services.stock_concept_service import StockConceptService
            for item in items:
                concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
                setattr(item, '_concepts', concepts)
                # 同时更新concept文本字段（兼容旧接口）
                if concepts:
                    concept_names = [c.name for c in concepts]
                    setattr(item, 'concept', ','.join(concept_names))
            
            return items, total
            
        except Exception as e:
            print(f"[LhbService] 查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            # 返回空结果，避免服务崩溃
            return [], 0
    
    @staticmethod
    def get_lhb_detail(
        db: Session,
        stock_code: str,
        target_date: date
    ) -> Optional[LhbDetail]:
        """获取龙虎榜详情"""
        return db.query(LhbDetail).filter(
            and_(
                LhbDetail.stock_code == stock_code,
                LhbDetail.date == target_date
            )
        ).first()
    
    @staticmethod
    def get_institution_detail(
        db: Session,
        stock_code: str,
        target_date: date,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> List[LhbInstitution]:
        """
        获取机构明细
        默认按净买额倒序排序
        """
        query = db.query(LhbInstitution).filter(
            and_(
                LhbInstitution.stock_code == stock_code,
                LhbInstitution.date == target_date
            )
        )
        
        # 排序
        if sort_by:
            sort_column = getattr(LhbInstitution, sort_by, None)
            if sort_column:
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            # 默认按净买额倒序
            from sqlalchemy import nullslast
            query = query.order_by(nullslast(desc(LhbInstitution.net_buy_amount)))
        
        return query.all()
    
    @staticmethod
    def save_lhb_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """
        保存龙虎榜数据
        返回保存的记录数
        """
        count = 0
        
        # 去重：同一日期同一代码只保留一条
        df_to_process = df.copy()
        if "代码" in df_to_process.columns:
            before_len = len(df_to_process)
            df_to_process = df_to_process.drop_duplicates(subset=["代码"])
            after_len = len(df_to_process)
            if before_len != after_len:
                print(f"[LhbService] 去重龙虎榜基础数据: {before_len} -> {after_len}")
        
        for _, row in df_to_process.iterrows():
            stock_code = str(row.get("代码", "")).zfill(6)
            stock_name = row.get("名称", "")
            
            # 从"上榜日"字段获取日期，如果没有则使用target_date
            row_date = target_date
            if "上榜日" in row and pd.notna(row.get("上榜日")):
                try:
                    from datetime import datetime
                    if isinstance(row.get("上榜日"), str):
                        row_date = datetime.strptime(row.get("上榜日"), "%Y-%m-%d").date()
                    else:
                        row_date = row.get("上榜日").date() if hasattr(row.get("上榜日"), "date") else target_date
                except:
                    row_date = target_date
            
            # 检查是否已存在
            existing = db.query(LhbDetail).filter(
                and_(
                    LhbDetail.date == row_date,
                    LhbDetail.stock_code == stock_code
                )
            ).first()
            
            # 尝试多种可能的字段名
            close_price = row.get("收盘价", row.get("最新价", None))
            change_percent = row.get("涨跌幅", row.get("涨跌", None))
            net_buy_amount = row.get("龙虎榜净买额", row.get("净买额", None))
            buy_amount = row.get("龙虎榜买入额", row.get("买入额", None))
            sell_amount = row.get("龙虎榜卖出额", row.get("卖出额", None))
            total_amount = row.get("总成交额", row.get("成交额", None))
            turnover_rate = row.get("换手率", None)
            
            # 获取概念信息（暂时留空，后续可以从其他接口获取）
            concept = None
            
            if existing:
                lhb_detail = existing
                # 更新
                existing.stock_name = stock_name
                if close_price is not None:
                    existing.close_price = close_price
                if change_percent is not None:
                    existing.change_percent = change_percent
                if net_buy_amount is not None:
                    existing.net_buy_amount = net_buy_amount
                if buy_amount is not None:
                    existing.buy_amount = buy_amount
                if sell_amount is not None:
                    existing.sell_amount = sell_amount
                if total_amount is not None:
                    existing.total_amount = total_amount
                if turnover_rate is not None:
                    existing.turnover_rate = turnover_rate
                if concept is not None:
                    existing.concept = concept
                lhb_detail = existing
            else:
                # 新建
                lhb = LhbDetail(
                    date=row_date,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    close_price=close_price,
                    change_percent=change_percent,
                    net_buy_amount=net_buy_amount,
                    buy_amount=buy_amount,
                    sell_amount=sell_amount,
                    total_amount=total_amount,
                    turnover_rate=turnover_rate,
                    concept=concept,
                )
                db.add(lhb)
                db.flush()  # 获取ID
                lhb_detail = lhb
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def save_institution_data(
        db: Session,
        lhb_detail_id: int,
        stock_code: str,
        target_date: date,
        df_buy: pd.DataFrame,
        df_sell: pd.DataFrame
    ) -> int:
        """
        保存机构明细数据
        返回保存的记录数
        注意：买入和卖出数据分别保存，通过flag字段区分
        """
        count = 0
        
        # 保存买入机构数据（flag='买入'）
        if df_buy is not None and not df_buy.empty:
            df_buy_proc = df_buy.drop_duplicates(subset=["交易营业部名称"]) if "交易营业部名称" in df_buy.columns else df_buy
            if len(df_buy_proc) != len(df_buy):
                print(f"[LhbService] 买入机构去重: {len(df_buy)} -> {len(df_buy_proc)}")
            for _, row in df_buy_proc.iterrows():
                institution_name = row.get("交易营业部名称", "")
                if not institution_name:
                    continue
                
                buy_amount = row.get("买入金额", None)
                sell_amount = row.get("卖出金额", None)
                net_buy_amount = row.get("净额", None)
                
                # 检查是否已存在（同一机构、同一flag）
                existing = db.query(LhbInstitution).filter(
                    and_(
                        LhbInstitution.lhb_detail_id == lhb_detail_id,
                        LhbInstitution.institution_name == institution_name,
                        LhbInstitution.flag == '买入'
                    )
                ).first()
                
                if existing:
                    # 更新
                    if buy_amount is not None:
                        existing.buy_amount = buy_amount
                    if sell_amount is not None:
                        existing.sell_amount = sell_amount
                    if net_buy_amount is not None:
                        existing.net_buy_amount = net_buy_amount
                else:
                    # 新建
                    institution = LhbInstitution(
                        lhb_detail_id=lhb_detail_id,
                        date=target_date,
                        stock_code=stock_code,
                        institution_name=institution_name,
                        buy_amount=buy_amount,
                        sell_amount=sell_amount,
                        net_buy_amount=net_buy_amount,
                        flag='买入',
                    )
                    db.add(institution)
                
                count += 1
        
        # 保存卖出机构数据（flag='卖出'）
        if df_sell is not None and not df_sell.empty:
            df_sell_proc = df_sell.drop_duplicates(subset=["交易营业部名称"]) if "交易营业部名称" in df_sell.columns else df_sell
            if len(df_sell_proc) != len(df_sell):
                print(f"[LhbService] 卖出机构去重: {len(df_sell)} -> {len(df_sell_proc)}")
            for _, row in df_sell_proc.iterrows():
                institution_name = row.get("交易营业部名称", "")
                if not institution_name:
                    continue
                
                buy_amount = row.get("买入金额", None)
                sell_amount = row.get("卖出金额", None)
                net_buy_amount = row.get("净额", None)
                
                # 检查是否已存在（同一机构、同一flag）
                existing = db.query(LhbInstitution).filter(
                    and_(
                        LhbInstitution.lhb_detail_id == lhb_detail_id,
                        LhbInstitution.institution_name == institution_name,
                        LhbInstitution.flag == '卖出'
                    )
                ).first()
                
                if existing:
                    # 更新
                    if buy_amount is not None:
                        existing.buy_amount = buy_amount
                    if sell_amount is not None:
                        existing.sell_amount = sell_amount
                    if net_buy_amount is not None:
                        existing.net_buy_amount = net_buy_amount
                else:
                    # 新建
                    institution = LhbInstitution(
                        lhb_detail_id=lhb_detail_id,
                        date=target_date,
                        stock_code=stock_code,
                        institution_name=institution_name,
                        buy_amount=buy_amount,
                        sell_amount=sell_amount,
                        net_buy_amount=net_buy_amount,
                        flag='卖出',
                    )
                    db.add(institution)
                    count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_institution_data(db: Session, target_date: date):
        """
        同步指定日期的所有股票的机构明细数据
        应该在 sync_data 之后调用
        """
        from app.utils.sync_result import SyncResult
        
        try:
            # 获取该日期的所有龙虎榜股票
            lhb_details = db.query(LhbDetail).filter(LhbDetail.date == target_date).all()
            
            if not lhb_details:
                error_msg = f"未找到 {target_date} 的龙虎榜基础数据，请先同步龙虎榜基础数据"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "缺少基础数据")
            
            date_str = target_date.strftime("%Y%m%d")
            success_count = 0
            fail_count = 0
            total_institutions = 0
            
            print(f"开始同步 {target_date} 的机构数据，共 {len(lhb_details)} 只股票...")
            
            for i, lhb_detail in enumerate(lhb_details, 1):
                stock_code = lhb_detail.stock_code
                stock_name = lhb_detail.stock_name
                
                if i % 10 == 0:
                    print(f"  进度: {i}/{len(lhb_details)} ({stock_code} {stock_name})")
                
                try:
                    # 获取买入机构
                    df_buy = safe_akshare_call(
                        ak.stock_lhb_stock_detail_em,
                        symbol=stock_code,
                        date=date_str,
                        flag='买入'
                    )
                    
                    # 获取卖出机构
                    df_sell = safe_akshare_call(
                        ak.stock_lhb_stock_detail_em,
                        symbol=stock_code,
                        date=date_str,
                        flag='卖出'
                    )
                    
                    if df_buy is None and df_sell is None:
                        fail_count += 1
                        continue
                    
                    # 保存机构数据
                    inst_count = LhbService.save_institution_data(
                        db, lhb_detail.id, stock_code, target_date, df_buy, df_sell
                    )
                    
                    if inst_count > 0:
                        success_count += 1
                        total_institutions += inst_count
                    else:
                        fail_count += 1
                    
                    # 避免请求过快
                    import time
                    time.sleep(0.3)
                        
                except Exception as e:
                    print(f"  获取 {stock_code} {stock_name} 机构数据失败: {str(e)[:50]}")
                    fail_count += 1
                    continue
            
            print(f"完成同步 {target_date} 的机构数据: 成功 {success_count} 只, 失败 {fail_count} 只, 总记录 {total_institutions} 条")
            
            if success_count == 0:
                error_msg = f"所有股票机构数据同步失败（共 {len(lhb_details)} 只股票）"
                return SyncResult.failure_result(error_msg, f"成功0只，失败{fail_count}只")
            
            return SyncResult.success_result(
                f"机构数据同步成功: 成功 {success_count} 只, 失败 {fail_count} 只",
                total_institutions
            )
            
        except Exception as e:
            error_msg = f"同步机构数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步龙虎榜数据
        从AKShare获取数据并保存到数据库
        注意: stock_lhb_detail_em 需要 start_date 和 end_date 参数
        """
        from app.utils.sync_result import SyncResult
        
        try:
            date_str = target_date.strftime("%Y%m%d")
            # stock_lhb_detail_em 需要 start_date 和 end_date 参数
            df = safe_akshare_call(ak.stock_lhb_detail_em, start_date=date_str, end_date=date_str)
            
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的龙虎榜数据，接口返回空或网络异常"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            # 过滤出指定日期的数据（因为接口可能返回日期范围内的所有数据）
            if '上榜日' in df.columns:
                df['上榜日'] = pd.to_datetime(df['上榜日'])
                df = df[df['上榜日'].dt.date == target_date]
            
            if df.empty:
                error_msg = f"未获取到 {target_date} 的龙虎榜数据（过滤后为空），可能该日期无龙虎榜数据"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据过滤后为空")
            
            # 保存基础数据
            count = LhbService.save_lhb_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的龙虎榜基础数据，共 {count} 条")
            
            # 注意：机构数据同步已分离到 sync_institution_data 方法
            # 在定时任务中会单独调用，避免在 sync_data 中同步机构数据导致超时
            
            return SyncResult.success_result(f"龙虎榜数据同步成功", count)
        except Exception as e:
            error_msg = f"同步龙虎榜数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)
    
    @staticmethod
    def get_lhb_stocks_statistics(
        db: Session,
        start_date: date,
        end_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[dict], int]:
        """
        获取时间跨度内龙虎榜上榜个股统计
        统计每个股票的上榜次数和净流入总额
        
        Returns:
            tuple[List[dict], int]: (统计结果列表, 总数)
        """
        try:
            # 构建基础查询
            query = db.query(LhbDetail).filter(
                LhbDetail.date >= start_date,
                LhbDetail.date <= end_date
            )
            
            # 添加股票代码过滤
            if stock_code and stock_code.strip():
                query = query.filter(LhbDetail.stock_code == stock_code.strip())
            
            # 添加股票名称模糊查询
            if stock_name and stock_name.strip():
                stock_name_clean = stock_name.strip()
                query = query.filter(func.lower(LhbDetail.stock_name).like(f"%{stock_name_clean.lower()}%"))
            
            # 查询所有符合条件的记录
            all_records = query.all()
            
            # 按股票代码分组统计
            stock_stats = {}
            for record in all_records:
                stock_key = record.stock_code
                if stock_key not in stock_stats:
                    stock_stats[stock_key] = {
                        'stock_code': record.stock_code,
                        'stock_name': record.stock_name,
                        'appear_count': 0,
                        'total_net_buy_amount': 0.0,
                        'total_buy_amount': 0.0,
                        'total_sell_amount': 0.0,
                        'dates': []  # 记录上榜日期
                    }
                
                stock_stats[stock_key]['appear_count'] += 1
                stock_stats[stock_key]['dates'].append(record.date)
                
                # 累加净买入额（安全处理None值）
                if record.net_buy_amount is not None:
                    try:
                        net_amount = float(record.net_buy_amount)
                        if not (math.isnan(net_amount) or math.isinf(net_amount)):
                            stock_stats[stock_key]['total_net_buy_amount'] += net_amount
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass
                
                # 累加买入额
                if record.buy_amount is not None:
                    try:
                        buy_amount = float(record.buy_amount)
                        if not (math.isnan(buy_amount) or math.isinf(buy_amount)):
                            stock_stats[stock_key]['total_buy_amount'] += buy_amount
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass
                
                # 累加卖出额
                if record.sell_amount is not None:
                    try:
                        sell_amount = float(record.sell_amount)
                        if not (math.isnan(sell_amount) or math.isinf(sell_amount)):
                            stock_stats[stock_key]['total_sell_amount'] += sell_amount
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass
            
            # 转换为列表
            statistics_list = []
            for stock_key, stats in stock_stats.items():
                statistics_list.append({
                    'stock_code': stats['stock_code'],
                    'stock_name': stats['stock_name'],
                    'appear_count': stats['appear_count'],
                    'total_net_buy_amount': round(stats['total_net_buy_amount'], 2),
                    'total_buy_amount': round(stats['total_buy_amount'], 2),
                    'total_sell_amount': round(stats['total_sell_amount'], 2),
                    'first_date': min(stats['dates']) if stats['dates'] else None,
                    'last_date': max(stats['dates']) if stats['dates'] else None,
                })
            
            # 排序
            if sort_by == 'appear_count':
                statistics_list.sort(key=lambda x: x['appear_count'], reverse=(order == 'desc'))
            elif sort_by == 'total_net_buy_amount':
                statistics_list.sort(key=lambda x: x['total_net_buy_amount'], reverse=(order == 'desc'))
            elif sort_by == 'stock_code':
                statistics_list.sort(key=lambda x: x['stock_code'], reverse=(order == 'desc'))
            elif sort_by == 'stock_name':
                statistics_list.sort(key=lambda x: x['stock_name'], reverse=(order == 'desc'))
            else:
                # 默认按上榜次数倒序
                statistics_list.sort(key=lambda x: x['appear_count'], reverse=True)
            
            # 分页
            total = len(statistics_list)
            offset = (page - 1) * page_size
            paginated_list = statistics_list[offset:offset + page_size]
            
            return paginated_list, total
            
        except Exception as e:
            print(f"[LhbService] 统计查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return [], 0

