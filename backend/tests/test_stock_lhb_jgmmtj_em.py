"""
测试 stock_lhb_jgmmtj_em 接口 - 龙虎榜机构买卖统计
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import akshare as ak
import pandas as pd
from app.utils.akshare_utils import safe_akshare_call


def test_stock_lhb_jgmmtj_em_basic():
    """测试基本的 stock_lhb_jgmmtj_em 接口调用"""
    print("=" * 60)
    print("测试 1: 基本接口调用")
    print("=" * 60)
    
    try:
        # 调用接口（可能需要日期参数）
        print("调用 stock_lhb_jgmmtj_em 接口...")
        
        # 先尝试不带参数调用
        df = safe_akshare_call(ak.stock_lhb_jgmmtj_em)
        
        if df is None:
            print("❌ 接口调用失败：返回 None")
            # 尝试直接调用查看错误信息
            try:
                df = ak.stock_lhb_jgmmtj_em()
            except Exception as e:
                print(f"直接调用错误: {str(e)}")
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


def test_stock_lhb_jgmmtj_em_with_date():
    """测试带日期参数的接口调用"""
    print("=" * 60)
    print("测试 2: 带日期参数调用")
    print("=" * 60)
    
    # 尝试不同的日期格式
    test_dates = [
        "20240101",  # YYYYMMDD
        "2024-01-01",  # YYYY-MM-DD
        datetime.now().strftime("%Y%m%d"),  # 今天
    ]
    
    success_count = 0
    for date_str in test_dates:
        print(f"\n测试日期参数: {date_str}")
        try:
            df = safe_akshare_call(ak.stock_lhb_jgmmtj_em, date=date_str)
            
            if df is not None and not df.empty:
                print(f"  ✅ 成功 - 数据行数: {len(df)}")
                success_count += 1
            else:
                print(f"  ⚠️ 无数据")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n总计: {success_count}/{len(test_dates)} 成功")
    return success_count > 0


def test_stock_lhb_jgmmtj_em_direct():
    """直接调用接口（不使用安全包装）"""
    print("=" * 60)
    print("测试 3: 直接接口调用（不使用安全包装）")
    print("=" * 60)
    
    try:
        # 先查看接口签名
        import inspect
        sig = inspect.signature(ak.stock_lhb_jgmmtj_em)
        print(f"接口参数: {sig}")
        print()
        
        # 尝试调用
        df = ak.stock_lhb_jgmmtj_em()
        
        print(f"✅ 直接调用成功！")
        print(f"数据行数: {len(df)}")
        print(f"数据类型: {type(df)}")
        print()
        print("数据信息:")
        print(df.info())
        print()
        
        if not df.empty:
            print("数据统计:")
            print(df.describe())
        
        return True
        
    except Exception as e:
        print(f"❌ 直接调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_lhb_jgmmtj_em_recent():
    """测试获取最近的数据"""
    print("=" * 60)
    print("测试 4: 获取最近数据")
    print("=" * 60)
    
    try:
        # 获取今天的日期
        today = datetime.now().strftime("%Y%m%d")
        print(f"使用日期: {today}")
        print()
        
        df = safe_akshare_call(ak.stock_lhb_jgmmtj_em, date=today)
        
        if df is not None and not df.empty:
            print(f"✅ 成功获取数据！")
            print(f"数据行数: {len(df)}")
            print()
            print("前10行数据:")
            print(df.head(10).to_string())
            return True
        else:
            print("⚠️ 无数据")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("stock_lhb_jgmmtj_em 接口测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("基本接口调用", test_stock_lhb_jgmmtj_em_basic()))
    results.append(("带日期参数调用", test_stock_lhb_jgmmtj_em_with_date()))
    results.append(("直接接口调用", test_stock_lhb_jgmmtj_em_direct()))
    results.append(("获取最近数据", test_stock_lhb_jgmmtj_em_recent()))
    
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
