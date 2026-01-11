"""
活跃机构（游资）服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date
import pandas as pd

from app.models.capital import CapitalDetail
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class CapitalService:
    """活跃机构服务类"""
    
    @staticmethod
    def get_capital_list(
        db: Session,
        target_date: date,
        capital_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[CapitalDetail], int]:
        """获取活跃机构列表"""
        query = db.query(CapitalDetail).filter(CapitalDetail.date == target_date)
        
        if capital_name:
            query = query.filter(CapitalDetail.capital_name == capital_name)
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def get_capital_detail(
        db: Session,
        capital_name: str,
        target_date: date
    ) -> List[CapitalDetail]:
        """获取活跃机构详情"""
        return db.query(CapitalDetail).filter(
            and_(
                CapitalDetail.capital_name == capital_name,
                CapitalDetail.date == target_date
            )
        ).all()
    
    @staticmethod
    def save_capital_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """保存活跃机构数据"""
        count = 0
        for _, row in df.iterrows():
            capital_name = row.get("营业部名称", "")
            stock_code = str(row.get("代码", "")).zfill(6)
            stock_name = row.get("名称", "")
            
            existing = db.query(CapitalDetail).filter(
                and_(
                    CapitalDetail.date == target_date,
                    CapitalDetail.capital_name == capital_name,
                    CapitalDetail.stock_code == stock_code
                )
            ).first()
            
            if existing:
                existing.stock_name = stock_name
                existing.buy_amount = row.get("买入额")
                existing.sell_amount = row.get("卖出额")
                existing.net_buy_amount = row.get("净买额")
            else:
                capital = CapitalDetail(
                    date=target_date,
                    capital_name=capital_name,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    buy_amount=row.get("买入额"),
                    sell_amount=row.get("卖出额"),
                    net_buy_amount=row.get("净买额"),
                )
                db.add(capital)
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date) -> bool:
        """
        同步活跃机构（游资）数据
        从AKShare获取数据并保存到数据库
        """
        try:
            date_str = target_date.strftime("%Y%m%d")
            df = safe_akshare_call(ak.stock_lhb_detail_em, date=date_str)
            
            if df is None or df.empty:
                print(f"未获取到 {target_date} 的游资数据")
                return False
            
            # 从龙虎榜数据中提取游资数据
            # 注意：需要根据实际AKShare返回的数据格式调整
            count = CapitalService.save_capital_data(db, target_date, df)
            print(f"成功同步 {target_date} 的游资数据，共 {count} 条")
            return True
        except Exception as e:
            print(f"同步游资数据失败: {str(e)}")
            return False

