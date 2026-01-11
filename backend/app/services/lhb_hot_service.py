"""
龙虎榜机构游资榜服务
数据来源: lhb_institution 表聚合（从龙虎榜机构明细表统计）
"""
from datetime import date
from typing import Optional, List
from decimal import Decimal
import pandas as pd

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, asc, func, distinct

from app.models.lhb import LhbHotInstitution, LhbInstitution, TraderBranch, LhbDetail
from app.schemas.lhb import LhbHotInstitutionDetailResponse
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class LhbHotService:
    """龙虎榜机构游资榜服务"""
    
    @staticmethod
    def get_list(
        db: Session,
        target_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc",
        flag: Optional[str] = None,
        stock_name: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> tuple[List[LhbInstitution], int]:
        """获取机构榜列表（直接从 lhb_institution 表查询，包含股票名称）"""
        import sys
        
        # 如果没有指定日期，使用最新的日期
        if not target_date:
            max_date = db.query(func.max(LhbInstitution.date)).scalar()
            if max_date:
                target_date = max_date
                print(f"[LhbHotService] 未指定日期，使用最新日期: {target_date}")
                sys.stdout.flush()
            else:
                print(f"[LhbHotService] ⚠️  表中无数据，返回空列表")
                sys.stdout.flush()
                return [], 0
        
        print(f"[LhbHotService] 查询日期: {target_date}, page: {page}, page_size: {page_size}, flag: {flag}, stock_name: {stock_name}, stock_code: {stock_code}")
        sys.stdout.flush()
        
        # 直接从 lhb_institution 查询，并关联 lhb_detail 获取股票名称
        query = db.query(LhbInstitution).options(
            joinedload(LhbInstitution.lhb_detail)
        ).filter(LhbInstitution.date == target_date)
        
        # 添加操作方向过滤
        if flag:
            query = query.filter(LhbInstitution.flag == flag)
        
        # 添加股票代码过滤
        if stock_code:
            query = query.filter(LhbInstitution.stock_code == stock_code)
        
        # 添加股票名称模糊查询（需要通过关联的 lhb_detail 表）
        if stock_name:
            query = query.join(
                LhbDetail, 
                LhbInstitution.lhb_detail_id == LhbDetail.id
            ).filter(
                LhbDetail.stock_name.like(f"%{stock_name}%")
            )
        
        # 排序
        if sort_by:
            # 处理字段名映射（前端可能使用net_amount，但数据库字段是net_buy_amount）
            field_mapping = {
                'net_amount': 'net_buy_amount',
                'amount': 'buy_amount',  # 默认使用买入金额
            }
            actual_sort_by = field_mapping.get(sort_by, sort_by)
            
            sort_col = getattr(LhbInstitution, actual_sort_by, None)
            if sort_col is not None:
                if order == "desc":
                    query = query.order_by(desc(LhbInstitution.date), desc(sort_col))
                else:
                    query = query.order_by(desc(LhbInstitution.date), asc(sort_col))
            else:
                print(f"[LhbHotService] ⚠️  排序字段 {sort_by} 不存在，使用默认排序")
                sys.stdout.flush()
                # 默认按金额排序（买入显示买入金额，卖出显示卖出金额）
                from sqlalchemy import nullslast
                query = query.order_by(
                    desc(LhbInstitution.date),
                    nullslast(desc(LhbInstitution.buy_amount)),
                    nullslast(desc(LhbInstitution.sell_amount))
                )
        else:
            # 默认排序：先按日期，再按买入金额和卖出金额
            from sqlalchemy import nullslast
            query = query.order_by(
                desc(LhbInstitution.date),
                nullslast(desc(LhbInstitution.buy_amount)),
                nullslast(desc(LhbInstitution.sell_amount))
            )
        
        total = query.count()
        print(f"[LhbHotService] 查询结果: {total} 条记录")
        sys.stdout.flush()
        
        offset = (page - 1) * page_size
        print(f"[LhbHotService] 分页参数: offset={offset}, limit={page_size}")
        sys.stdout.flush()
        
        items = query.offset(offset).limit(page_size).all()
        print(f"[LhbHotService] 分页查询返回: {len(items)} 条记录")
        if len(items) > 0:
            print(f"[LhbHotService] 第一条记录: id={items[0].id}, stock_code={items[0].stock_code}, institution_name={items[0].institution_name}")
            if items[0].lhb_detail:
                print(f"[LhbHotService] 关联的股票名称: {items[0].lhb_detail.stock_name}")
            else:
                print(f"[LhbHotService] ⚠️  第一条记录没有关联的lhb_detail")
        sys.stdout.flush()
        
        if total == 0:
            print(f"[LhbHotService] ⚠️  日期 {target_date} 无数据，可能需要先同步龙虎榜数据")
            sys.stdout.flush()
        
        return items, total
    
    @staticmethod
    def sync_data(db: Session, target_date: Optional[date] = None) -> bool:
        """
        同步机构榜数据
        从 lhb_institution 表聚合数据，按机构名称统计买入/卖出个股及金额
        """
        if not target_date:
            print("同步机构榜需要指定日期")
            return False
        
        try:
            # 查询指定日期的所有机构明细，使用 joinedload 预加载 lhb_detail 避免 N+1 查询
            query = db.query(LhbInstitution).options(
                joinedload(LhbInstitution.lhb_detail)
            ).filter(LhbInstitution.date == target_date)
            institutions = query.all()
            
            if not institutions:
                print(f"日期 {target_date} 无机构明细数据")
                return False
            
            # 按机构名称分组聚合
            institution_stats = {}
            
            for inst in institutions:
                inst_name = inst.institution_name
                if not inst_name:
                    continue
                
                if inst_name not in institution_stats:
                    institution_stats[inst_name] = {
                        "buy_stocks": set(),  # 买入股票代码集合
                        "sell_stocks": set(),  # 卖出股票代码集合
                        "buy_amount": Decimal(0),
                        "sell_amount": Decimal(0),
                        "buy_stock_names": [],  # 买入股票名称列表
                    }
                
                stats = institution_stats[inst_name]
                
                if inst.flag == "买入":
                    stats["buy_stocks"].add(inst.stock_code)
                    if inst.buy_amount:
                        stats["buy_amount"] += Decimal(str(inst.buy_amount))
                    # 获取股票名称（从 lhb_detail 关联）
                    if inst.lhb_detail:
                        stock_name = inst.lhb_detail.stock_name
                        if stock_name and stock_name not in stats["buy_stock_names"]:
                            stats["buy_stock_names"].append(stock_name)
                
                elif inst.flag == "卖出":
                    stats["sell_stocks"].add(inst.stock_code)
                    if inst.sell_amount:
                        stats["sell_amount"] += Decimal(str(inst.sell_amount))
            
            if not institution_stats:
                print(f"日期 {target_date} 无有效机构数据")
                return False
            
            # 查找机构代码映射（从 TraderBranch 表）
            institution_code_map = {}
            trader_branches = db.query(TraderBranch).filter(
                TraderBranch.institution_code.isnot(None),
                TraderBranch.institution_code != ""
            ).all()
            for branch in trader_branches:
                if branch.institution_name not in institution_code_map:
                    institution_code_map[branch.institution_name] = branch.institution_code
            
            saved = 0
            for inst_name, stats in institution_stats.items():
                buy_stock_count = len(stats["buy_stocks"])
                sell_stock_count = len(stats["sell_stocks"])
                buy_amount = stats["buy_amount"]
                sell_amount = stats["sell_amount"]
                net_amount = buy_amount - sell_amount
                buy_stocks = " ".join(stats["buy_stock_names"]) if stats["buy_stock_names"] else None
                
                # 查找机构代码
                institution_code = institution_code_map.get(inst_name)
                
                # 检查是否已存在
                existing = db.query(LhbHotInstitution).filter(
                    and_(
                        LhbHotInstitution.date == target_date,
                        LhbHotInstitution.institution_name == inst_name
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.institution_code = institution_code
                    existing.buy_stock_count = buy_stock_count
                    existing.sell_stock_count = sell_stock_count
                    existing.buy_amount = buy_amount
                    existing.sell_amount = sell_amount
                    existing.net_amount = net_amount
                    existing.buy_stocks = buy_stocks
                else:
                    # 创建新记录
                    record = LhbHotInstitution(
                        date=target_date,
                        institution_name=inst_name,
                        institution_code=institution_code,
                        buy_stock_count=buy_stock_count,
                        sell_stock_count=sell_stock_count,
                        buy_amount=buy_amount,
                        sell_amount=sell_amount,
                        net_amount=net_amount,
                        buy_stocks=buy_stocks,
                    )
                    db.add(record)
                
                saved += 1
            
            db.commit()
            print(f"[LhbHot] 同步完成，保存 {saved} 条机构数据")
            return saved > 0
            
        except Exception as e:
            print(f"同步机构榜失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False

    @staticmethod
    def get_institution_detail(
        institution_code: str,
        target_date: Optional[date] = None
    ) -> List[LhbHotInstitutionDetailResponse]:
        """
        获取营业部买入股票明细（不落库，直接调用 ak.stock_lhb_yyb_detail_em）
        """
        df = safe_akshare_call(ak.stock_lhb_yyb_detail_em, symbol=institution_code)
        if df is None or df.empty:
            return []
        
        # 重命名并标准化
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
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        if target_date:
            df = df[df["date"] == target_date]
        if df.empty:
            return []
        
        records: List[LhbHotInstitutionDetailResponse] = []
        for _, row in df.iterrows():
            try:
                records.append(
                    LhbHotInstitutionDetailResponse(
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
                )
            except Exception:
                continue
        return records

