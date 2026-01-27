"""
测试 stock_zh_a_hist 接口 - 东财历史行情数据
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import akshare as ak
import pandas as pd
from app.utils.akshare_utils import safe_akshare_call


def test_stock_zh_a_hist_basic():
    """测试基本的 stock_zh_a_hist 接口调用"""
    print("=" * 60)
    print("测试 1: 基本接口调用")
    print("=" * 60)
    
    # 测试参数：使用一个常见的股票代码（例如：000001 平安银行）
    symbol = "000001"
    period = "daily"  # 日线数据
    start_date = "20240101"
    end_date = "20240131"
    adjust = ""  # 不复权
    
    print(f"股票代码: {symbol}")
    print(f"周期: {period}")
    print(f"开始日期: {start_date}")
    print(f"结束日期: {end_date}")
    print(f"复权类型: {adjust} (不复权)")
    print()
    
    try:
        # 使用安全调用函数
        df = safe_akshare_call(
            ak.stock_zh_a_hist,
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        if df is None:
            print("❌ 接口调用失败：返回 None")
            return False
        
        if df.empty:
            print("❌ 接口调用成功但数据为空")
            return False
        
        print(f"✅ 接口调用成功！")
        print(f"数据行数: {len(df)}")
        print(f"数据列数: {len(df.columns)}")
        print()
        print("数据列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        print()
        print("前5行数据:")
        print(df.head().to_string())
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 接口调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_zh_a_hist_direct():
    """直接调用 stock_zh_a_hist 接口（不使用安全包装）"""
    print("=" * 60)
    print("测试 2: 直接接口调用（不使用安全包装）")
    print("=" * 60)
    
    symbol = "000001"
    period = "daily"
    start_date = "20240101"
    end_date = "20240131"
    adjust = ""
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        print(f"✅ 直接调用成功！")
        print(f"数据行数: {len(df)}")
        print(f"数据类型: {type(df)}")
        print()
        print("数据信息:")
        print(df.info())
        print()
        print("数据统计:")
        print(df.describe())
        
        return True
        
    except Exception as e:
        print(f"❌ 直接调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_zh_a_hist_multiple_stocks():
    """测试多个股票代码"""
    print("=" * 60)
    print("测试 3: 多个股票代码测试")
    print("=" * 60)
    
    test_stocks = [
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("600000", "浦发银行"),
    ]
    
    success_count = 0
    for symbol, name in test_stocks:
        print(f"\n测试股票: {name} ({symbol})")
        try:
            df = safe_akshare_call(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date="20240101",
                end_date="20240131",
                adjust=""
            )
            
            if df is not None and not df.empty:
                print(f"  ✅ 成功 - 数据行数: {len(df)}")
                success_count += 1
            else:
                print(f"  ❌ 失败 - 无数据")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n总计: {success_count}/{len(test_stocks)} 成功")
    return success_count == len(test_stocks)


def test_stock_zh_a_hist_different_periods():
    """测试不同的周期类型"""
    print("=" * 60)
    print("测试 4: 不同周期类型测试")
    print("=" * 60)
    
    periods = ["daily", "weekly", "monthly"]
    symbol = "000001"
    
    # 使用更长的日期范围以便测试周线和月线
    start_date = "20240101"
    end_date = "20241231"
    
    success_count = 0
    for period in periods:
        print(f"\n测试周期: {period}")
        try:
            df = safe_akshare_call(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            
            if df is not None and not df.empty:
                print(f"  ✅ 成功 - 数据行数: {len(df)}")
                success_count += 1
            else:
                print(f"  ❌ 失败 - 无数据")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n总计: {success_count}/{len(periods)} 成功")
    return success_count == len(periods)


def test_stock_zh_a_hist_adjust_types():
    """测试不同的复权类型"""
    print("=" * 60)
    print("测试 5: 不同复权类型测试")
    print("=" * 60)
    
    adjust_types = ["", "qfq", "hfq"]  # 不复权、前复权、后复权
    symbol = "000001"
    
    success_count = 0
    for adjust in adjust_types:
        adjust_name = "不复权" if adjust == "" else ("前复权" if adjust == "qfq" else "后复权")
        print(f"\n测试复权类型: {adjust_name} ({adjust})")
        try:
            df = safe_akshare_call(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date="20240101",
                end_date="20240131",
                adjust=adjust
            )
            
            if df is not None and not df.empty:
                print(f"  ✅ 成功 - 数据行数: {len(df)}")
                if "收盘" in df.columns or "收盘价" in df.columns:
                    close_col = "收盘" if "收盘" in df.columns else "收盘价"
                    print(f"  收盘价范围: {df[close_col].min():.2f} - {df[close_col].max():.2f}")
                success_count += 1
            else:
                print(f"  ❌ 失败 - 无数据")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n总计: {success_count}/{len(adjust_types)} 成功")
    return success_count == len(adjust_types)


def test_stock_zh_a_hist_recent_data():
    """测试获取最近的数据"""
    print("=" * 60)
    print("测试 6: 获取最近数据")
    print("=" * 60)
    
    symbol = "000001"
    
    # 获取最近30天的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    print(f"开始日期: {start_str}")
    print(f"结束日期: {end_str}")
    print()
    
    try:
        df = safe_akshare_call(
            ak.stock_zh_a_hist,
            symbol=symbol,
            period="daily",
            start_date=start_str,
            end_date=end_str,
            adjust=""
        )
        
        if df is not None and not df.empty:
            print(f"✅ 成功获取最近数据！")
            print(f"数据行数: {len(df)}")
            print()
            print("最近5个交易日数据:")
            print(df.tail().to_string())
            return True
        else:
            print("❌ 无数据")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("stock_zh_a_hist 接口测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("基本接口调用", test_stock_zh_a_hist_basic()))
    results.append(("直接接口调用", test_stock_zh_a_hist_direct()))
    results.append(("多个股票代码", test_stock_zh_a_hist_multiple_stocks()))
    results.append(("不同周期类型", test_stock_zh_a_hist_different_periods()))
    results.append(("不同复权类型", test_stock_zh_a_hist_adjust_types()))
    results.append(("最近数据", test_stock_zh_a_hist_recent_data()))
    
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
