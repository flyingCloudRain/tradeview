"""
批量更新个股资金流历史数据的涨停和龙虎榜标志
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import date, datetime
from app.database.session import get_db
from app.models.fund_flow import StockFundFlow
from app.models.zt_pool import ZtPool
from app.models.lhb import LhbDetail


def update_fund_flow_flags(
    db: Session,
    start_date: date = None,
    end_date: date = None,
    batch_size: int = 1000
):
    """
    批量更新个股资金流的涨停和龙虎榜标志
    
    Args:
        db: 数据库会话
        start_date: 开始日期，如果为None则从最早的数据开始
        end_date: 结束日期，如果为None则到最新的数据
        batch_size: 每批处理的记录数
    """
    # 确定日期范围
    if start_date is None:
        min_date = db.query(func.min(StockFundFlow.date)).scalar()
        start_date = min_date if min_date else date.today()
        print(f"未指定开始日期，使用最早数据日期: {start_date}")
    
    if end_date is None:
        max_date = db.query(func.max(StockFundFlow.date)).scalar()
        end_date = max_date if max_date else date.today()
        print(f"未指定结束日期，使用最新数据日期: {end_date}")
    
    print(f"开始更新 {start_date} 到 {end_date} 的资金流标志...")
    
    # 查询需要更新的记录
    query = db.query(StockFundFlow).filter(
        and_(
            StockFundFlow.date >= start_date,
            StockFundFlow.date <= end_date
        )
    )
    
    total_count = query.count()
    print(f"共找到 {total_count} 条记录需要处理")
    
    if total_count == 0:
        print("没有需要处理的记录")
        return
    
    # 分批处理
    updated_limit_up = 0
    updated_lhb = 0
    processed = 0
    
    offset = 0
    while offset < total_count:
        records = query.offset(offset).limit(batch_size).all()
        
        if not records:
            break
        
        for record in records:
            # 查询是否涨停
            is_limit_up = db.query(ZtPool).filter(
                and_(
                    ZtPool.date == record.date,
                    ZtPool.stock_code == record.stock_code
                )
            ).first() is not None
            
            # 查询是否龙虎榜
            is_lhb = db.query(LhbDetail).filter(
                and_(
                    LhbDetail.date == record.date,
                    LhbDetail.stock_code == record.stock_code
                )
            ).first() is not None
            
            # 更新标志（只在有变化时更新）
            if record.is_limit_up != is_limit_up:
                record.is_limit_up = is_limit_up
                updated_limit_up += 1
            
            if record.is_lhb != is_lhb:
                record.is_lhb = is_lhb
                updated_lhb += 1
            
            processed += 1
        
        # 提交当前批次
        db.commit()
        
        offset += batch_size
        print(f"已处理 {processed}/{total_count} 条记录 (涨停: {updated_limit_up}, 龙虎榜: {updated_lhb})")
    
    print(f"\n更新完成！")
    print(f"总计处理: {processed} 条")
    print(f"更新涨停标志: {updated_limit_up} 条")
    print(f"更新龙虎榜标志: {updated_lhb} 条")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量更新个股资金流的涨停和龙虎榜标志')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--batch-size', type=int, help='每批处理的记录数', default=1000)
    
    args = parser.parse_args()
    
    # 解析日期
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        update_fund_flow_flags(
            db=db,
            start_date=start_date,
            end_date=end_date,
            batch_size=args.batch_size
        )
    except Exception as e:
        print(f"更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()

