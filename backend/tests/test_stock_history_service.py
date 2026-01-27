"""
测试股票历史行情服务
"""
import sys
import os
from datetime import date, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.session import SessionLocal
from app.services.stock_history_service import StockHistoryService
from app.models.limit_up_board import LimitUpBoard


def test_sync_limit_up_stocks_history():
    """测试同步涨停股历史行情数据"""
    print("=" * 60)
    print("测试同步涨停股历史行情数据")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 查找最近有涨停股数据的日期
        latest_limit_up = db.query(LimitUpBoard).order_by(
            LimitUpBoard.date.desc()
        ).first()
        
        if not latest_limit_up:
            print("❌ 数据库中没有涨停股数据，无法测试")
            return False
        
        target_date = latest_limit_up.date
        print(f"使用日期: {target_date}")
        print(f"涨停股数量: {db.query(LimitUpBoard).filter(LimitUpBoard.date == target_date).count()}")
        print()
        
        # 测试同步（使用1个月的数据以减少测试时间）
        print("开始同步历史数据（测试使用1个月数据）...")
        result = StockHistoryService.sync_limit_up_stocks_history(
            db, target_date, months=1
        )
        
        if result.success:
            print(f"✅ 同步成功: {result.message}")
            print(f"   共保存 {result.count} 条记录")
            
            # 验证数据
            from app.models.stock_history import StockHistory
            saved_count = db.query(StockHistory).count()
            print(f"   数据库中共有 {saved_count} 条历史行情记录")
            
            # 查看前几条数据
            recent_records = db.query(StockHistory).order_by(
                StockHistory.date.desc()
            ).limit(5).all()
            
            if recent_records:
                print("\n最近5条记录:")
                for record in recent_records:
                    print(f"  {record.date} | {record.stock_code} | {record.stock_name} | "
                          f"收盘: {record.close_price} | 涨跌幅: {record.change_percent}%")
            
            return True
        else:
            print(f"❌ 同步失败: {result.error}")
            if result.message:
                print(f"   详情: {result.message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_get_stock_history():
    """测试获取股票历史行情数据"""
    print("\n" + "=" * 60)
    print("测试获取股票历史行情数据")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 查找有历史数据的股票
        from app.models.stock_history import StockHistory
        stock_history = db.query(StockHistory).first()
        
        if not stock_history:
            print("❌ 数据库中没有历史行情数据，无法测试")
            return False
        
        stock_code = stock_history.stock_code
        print(f"测试股票代码: {stock_code}")
        
        # 获取最近30天的数据
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        history_list = StockHistoryService.get_stock_history(
            db, stock_code, start_date, end_date
        )
        
        print(f"✅ 获取到 {len(history_list)} 条历史数据")
        
        if history_list:
            print("\n最近5条数据:")
            for record in history_list[:5]:
                print(f"  {record.date} | 开盘: {record.open_price} | "
                      f"收盘: {record.close_price} | 涨跌幅: {record.change_percent}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("股票历史行情服务测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("同步涨停股历史数据", test_sync_limit_up_stocks_history()))
    results.append(("获取股票历史数据", test_get_stock_history()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
