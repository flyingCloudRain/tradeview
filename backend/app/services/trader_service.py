"""
游资-营业部极简映射服务
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

import akshare as ak
import pandas as pd

from app.models.lhb import Trader, TraderBranch, TraderBranchHistory
from app.utils.akshare_utils import safe_akshare_call


class TraderService:
    """游资映射服务（极简）"""
    
    @staticmethod
    def list_traders(db: Session) -> List[Trader]:
        """获取所有游资及其营业部列表"""
        return db.query(Trader).options(joinedload(Trader.branches)).all()
    
    @staticmethod
    def get_trader_by_id(db: Session, trader_id: int) -> Optional[Trader]:
        """根据ID获取游资"""
        return db.query(Trader).options(joinedload(Trader.branches)).filter(Trader.id == trader_id).first()
    
    @staticmethod
    def get_trader_by_name(db: Session, name: str) -> Optional[Trader]:
        """根据名称获取游资"""
        return db.query(Trader).filter(Trader.name == name).first()
    
    @staticmethod
    def get_trader_by_institution(
        db: Session,
        institution_code: Optional[str] = None,
        institution_name: Optional[str] = None
    ) -> Optional[Trader]:
        if not institution_code and not institution_name:
            return None
        query = db.query(Trader).join(TraderBranch)
        if institution_code:
            query = query.filter(TraderBranch.institution_code == institution_code)
        if institution_name:
            query = query.filter(TraderBranch.institution_name == institution_name)
        return query.first()
    
    @staticmethod
    def create_trader(
        db: Session,
        name: str,
        aka: Optional[str] = None,
        branch_names: Optional[List[str]] = None
    ) -> Trader:
        """创建游资"""
        # 检查名称是否已存在
        existing = TraderService.get_trader_by_name(db, name)
        if existing:
            raise ValueError(f"游资名称 '{name}' 已存在")
        
        trader = Trader(name=name, aka=aka)
        db.add(trader)
        db.flush()  # 获取trader.id
        
        # 添加机构关联
        if branch_names:
            for branch_name in branch_names:
                branch_name = branch_name.strip()
                if branch_name:
                    # 检查是否已存在
                    existing_branch = db.query(TraderBranch).filter(
                        TraderBranch.trader_id == trader.id,
                        TraderBranch.institution_name == branch_name
                    ).first()
                    
                    if not existing_branch:
                        branch = TraderBranch(
                            trader_id=trader.id,
                            institution_name=branch_name,
                            institution_code=None
                        )
                        db.add(branch)
        
        db.commit()
        db.refresh(trader)
        return trader
    
    @staticmethod
    def update_trader(
        db: Session,
        trader_id: int,
        name: Optional[str] = None,
        aka: Optional[str] = None
    ) -> Optional[Trader]:
        """更新游资"""
        trader = TraderService.get_trader_by_id(db, trader_id)
        if not trader:
            return None
        
        # 如果更新名称，检查是否与其他游资冲突
        if name and name != trader.name:
            existing = TraderService.get_trader_by_name(db, name)
            if existing:
                raise ValueError(f"游资名称 '{name}' 已存在")
            trader.name = name
        
        if aka is not None:
            trader.aka = aka
        
        db.commit()
        db.refresh(trader)
        return trader
    
    @staticmethod
    def delete_trader(db: Session, trader_id: int) -> bool:
        """删除游资（级联删除关联的branch）"""
        trader = TraderService.get_trader_by_id(db, trader_id)
        if not trader:
            return False
        
        db.delete(trader)
        db.commit()
        return True
    
    @staticmethod
    def add_branch(
        db: Session,
        trader_id: int,
        institution_name: str,
        institution_code: Optional[str] = None
    ) -> Optional[TraderBranch]:
        """为游资添加机构关联"""
        trader = TraderService.get_trader_by_id(db, trader_id)
        if not trader:
            return None
        
        # 检查是否已存在
        existing = db.query(TraderBranch).filter(
            TraderBranch.trader_id == trader_id,
            TraderBranch.institution_name == institution_name
        ).first()
        
        if existing:
            # 更新代码（如果提供了）
            if institution_code and not existing.institution_code:
                existing.institution_code = institution_code
                db.commit()
                db.refresh(existing)
            return existing
        
        branch = TraderBranch(
            trader_id=trader_id,
            institution_name=institution_name,
            institution_code=institution_code
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch
    
    @staticmethod
    def delete_branch(db: Session, branch_id: int) -> bool:
        """删除机构关联"""
        branch = db.query(TraderBranch).filter(TraderBranch.id == branch_id).first()
        if not branch:
            return False
        
        db.delete(branch)
        db.commit()
        return True
    
    @staticmethod
    def update_branch(
        db: Session,
        branch_id: int,
        institution_name: Optional[str] = None,
        institution_code: Optional[str] = None
    ) -> Optional[TraderBranch]:
        """更新机构关联"""
        branch = db.query(TraderBranch).filter(TraderBranch.id == branch_id).first()
        if not branch:
            return None
        
        if institution_name is not None:
            # 检查是否与其他关联冲突
            existing = db.query(TraderBranch).filter(
                TraderBranch.trader_id == branch.trader_id,
                TraderBranch.institution_name == institution_name,
                TraderBranch.id != branch_id
            ).first()
            if existing:
                raise ValueError(f"该游资已存在机构 '{institution_name}'")
            branch.institution_name = institution_name
        
        if institution_code is not None:
            branch.institution_code = institution_code
        
        db.commit()
        db.refresh(branch)
        return branch
    
    @staticmethod
    def sync_branch_history(db: Session, target_date: Optional[date] = None) -> bool:
        """
        同步游资营业部历史交易明细
        遍历所有有 institution_code 的 TraderBranch，调用 stock_lhb_yyb_detail_em 获取历史数据
        """
        try:
            # 获取所有有 institution_code 的营业部
            branches = db.query(TraderBranch).filter(
                TraderBranch.institution_code.isnot(None),
                TraderBranch.institution_code != ""
            ).all()
            
            if not branches:
                print("没有找到有营业部代码的游资营业部")
                return False
            
            total_saved = 0
            total_branches = len(branches)
            
            for idx, branch in enumerate(branches, 1):
                institution_code = branch.institution_code
                if not institution_code:
                    continue
                
                print(f"[{idx}/{total_branches}] 同步 {branch.institution_name} ({institution_code})...")
                
                try:
                    # 调用接口获取历史数据
                    df: pd.DataFrame = safe_akshare_call(ak.stock_lhb_yyb_detail_em, symbol=institution_code)
                    if df is None or df.empty:
                        print(f"  无数据，跳过")
                        continue
                    
                    # 标准化列名
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
                    
                    # 解析日期
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"]).dt.date
                    
                    # 按目标日期过滤（如果指定）
                    if target_date:
                        df = df[df["date"] == target_date]
                        if df.empty:
                            print(f"  目标日期 {target_date} 无数据，跳过")
                            continue
                    
                    # 保存数据
                    saved_count = 0
                    for _, row in df.iterrows():
                        row_date = row.get("date")
                        stock_code = str(row.get("stock_code", "")).strip()
                        if not row_date or not stock_code:
                            continue
                        
                        # 检查是否已存在
                        existing = db.query(TraderBranchHistory).filter(
                            and_(
                                TraderBranchHistory.trader_branch_id == branch.id,
                                TraderBranchHistory.date == row_date,
                                TraderBranchHistory.stock_code == stock_code.zfill(6)
                            )
                        ).first()
                        
                        if existing:
                            # 更新现有记录
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
                            record = TraderBranchHistory(
                                trader_branch_id=branch.id,
                                institution_code=institution_code,
                                institution_name=branch.institution_name,
                                date=row_date,
                                stock_code=stock_code.zfill(6),
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
                            db.add(record)
                        
                        saved_count += 1
                    
                    db.commit()
                    total_saved += saved_count
                    print(f"  保存 {saved_count} 条记录")
                    
                except Exception as e:
                    print(f"  同步失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.rollback()
                    continue
            
            print(f"[TraderBranchHistory] 同步完成，共处理 {total_branches} 个营业部，保存 {total_saved} 条记录")
            return total_saved > 0
            
        except Exception as e:
            print(f"同步游资营业部历史数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False

