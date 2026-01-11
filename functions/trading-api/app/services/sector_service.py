"""
概念板块服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from typing import Optional, List
from datetime import date
import pandas as pd

from app.models.sector import SectorHistory
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class SectorService:
    """概念板块服务类"""
    
    @staticmethod
    def get_sector_list(
        db: Session,
        target_date: date,
        sector_code: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> List[SectorHistory]:
        """获取板块列表"""
        query = db.query(SectorHistory).filter(SectorHistory.date == target_date)
        
        if sector_code:
            query = query.filter(SectorHistory.sector_code == sector_code)
        
        # 排序
        if sort_by:
            sort_column = getattr(SectorHistory, sort_by, None)
            if sort_column:
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(SectorHistory.change_percent))
        
        return query.all()
    
    @staticmethod
    def get_sector_detail(
        db: Session,
        sector_code: str,
        target_date: date
    ) -> Optional[SectorHistory]:
        """获取板块详情"""
        return db.query(SectorHistory).filter(
            and_(
                SectorHistory.sector_code == sector_code,
                SectorHistory.date == target_date
            )
        ).first()
    
    @staticmethod
    def save_sector_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """保存板块数据"""
        count = 0
        for _, row in df.iterrows():
            sector_code = str(row.get("板块代码", ""))
            sector_name = row.get("板块名称", "")
            
            existing = db.query(SectorHistory).filter(
                and_(
                    SectorHistory.date == target_date,
                    SectorHistory.sector_code == sector_code
                )
            ).first()
            
            if existing:
                existing.sector_name = sector_name
                existing.change_percent = row.get("涨跌幅")
                existing.rise_count = row.get("上涨家数")
                existing.fall_count = row.get("下跌家数")
                existing.total_count = row.get("总家数")
                existing.total_amount = row.get("总成交额")
            else:
                sector = SectorHistory(
                    date=target_date,
                    sector_code=sector_code,
                    sector_name=sector_name,
                    change_percent=row.get("涨跌幅"),
                    rise_count=row.get("上涨家数"),
                    fall_count=row.get("下跌家数"),
                    total_count=row.get("总家数"),
                    total_amount=row.get("总成交额"),
                )
                db.add(sector)
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date) -> bool:
        """
        同步概念板块数据
        从AKShare获取数据并保存到数据库
        """
        try:
            date_str = target_date.strftime("%Y%m%d")
            df = safe_akshare_call(ak.stock_board_concept_name_em)
            
            if df is None or df.empty:
                print(f"未获取到 {target_date} 的板块数据")
                return False
            
            # 获取板块涨跌数据
            # 注意：需要根据实际AKShare API调整
            count = SectorService.save_sector_data(db, target_date, df)
            print(f"成功同步 {target_date} 的板块数据，共 {count} 条")
            return True
        except Exception as e:
            print(f"同步板块数据失败: {str(e)}")
            return False

