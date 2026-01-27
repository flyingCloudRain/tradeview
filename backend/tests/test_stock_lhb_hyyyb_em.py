"""
测试 stock_lhb_hyyyb_em 接口 - 龙虎榜活跃营业部
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import akshare as ak
import pandas as pd
from app.utils.akshare_utils import safe_akshare_call


def test_stock_lhb_hyyyb_em_basic():
    """测试基本的 stock_lhb_hyyyb_em 接口调用"""
    print("=" * 60)
    print("测试 1: 基本接口调用")
    print("=" * 60)
    
    try:
        # 先检查接口是否存在
        if not hasattr(ak, 'stock_lhb_hyyyb_em'):
            print("❌ 接口不存在：ak.stock_lhb_hyyyb_em")
            return False
        
        print("调用 stock_lhb_hyyyb_em 接口...")
        
        # 先尝试不带参数调用
        df = safe_akshare_call(ak.stock_lhb_hyyyb_em)
        
        if df is None:
            print("❌ 接口调用失败：返回 None")
            # 尝试直接调用查看错误信息
            try:
                df = ak.stock_lhb_hyyyb_em()
            except Exception as e:
                print(f"直接调用错误: {str(e)}")
                import traceback
                traceback.print_exc()
            return False
        
        if df.empty:
            print("⚠️ 接口调用成功但数据为空")
            print("这可能是因为当前没有活跃营业部数据")
            return True  # 空数据不算失败，可能是正常的
        
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


def test_stock_lhb_hyyyb_em_with_date():
    """测试带日期参数的接口调用"""
    print("=" * 60)
    print("测试 2: 带日期参数调用")
    print("=" * 60)
    
    # 尝试不同的日期格式（使用正确的参数名 start_date 和 end_date）
    test_dates = [
        "20240101",  # YYYYMMDD
        "20240115",  # YYYYMMDD
        datetime.now().strftime("%Y%m%d"),  # 今天
    ]
    
    success_count = 0
    for date_str in test_dates:
        print(f"\n测试日期参数: {date_str} (start_date={date_str}, end_date={date_str})")
        try:
            df = safe_akshare_call(ak.stock_lhb_hyyyb_em, start_date=date_str, end_date=date_str)
            
            if df is not None and not df.empty:
                print(f"  ✅ 成功 - 数据行数: {len(df)}")
                success_count += 1
            else:
                print(f"  ⚠️ 无数据（可能是该日期没有活跃营业部数据）")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n总计: {success_count}/{len(test_dates)} 成功")
    return success_count > 0


def test_stock_lhb_hyyyb_em_direct():
    """直接调用接口（不使用安全包装）"""
    print("=" * 60)
    print("测试 3: 直接接口调用（不使用安全包装）")
    print("=" * 60)
    
    try:
        # 先查看接口签名
        import inspect
        if not hasattr(ak, 'stock_lhb_hyyyb_em'):
            print("❌ 接口不存在")
            return False
            
        sig = inspect.signature(ak.stock_lhb_hyyyb_em)
        print(f"接口参数: {sig}")
        print()
        
        # 尝试调用
        df = ak.stock_lhb_hyyyb_em()
        
        print(f"✅ 直接调用成功！")
        print(f"数据行数: {len(df)}")
        print(f"数据类型: {type(df)}")
        print()
        
        if not df.empty:
            print("数据信息:")
            print(df.info())
            print()
            print("数据统计:")
            print(df.describe())
        else:
            print("数据为空")
        
        return True
        
    except Exception as e:
        print(f"❌ 直接调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_lhb_hyyyb_em_recent():
    """测试获取最近的数据"""
    print("=" * 60)
    print("测试 4: 获取最近数据")
    print("=" * 60)
    
    try:
        # 获取今天的日期
        today = datetime.now().strftime("%Y%m%d")
        print(f"使用日期: {today} (start_date={today}, end_date={today})")
        print()
        
        df = safe_akshare_call(ak.stock_lhb_hyyyb_em, start_date=today, end_date=today)
        
        if df is not None and not df.empty:
            print(f"✅ 成功获取数据！")
            print(f"数据行数: {len(df)}")
            print()
            print("前10行数据:")
            print(df.head(10).to_string())
            return True
        else:
            print("⚠️ 无数据（可能是正常的，如果当前没有活跃营业部数据）")
            return True  # 空数据不算失败
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_lhb_hyyyb_em_interface_check():
    """检查接口是否存在以及查看接口信息"""
    print("=" * 60)
    print("测试 0: 接口存在性检查")
    print("=" * 60)
    
    try:
        # 检查接口是否存在
        if hasattr(ak, 'stock_lhb_hyyyb_em'):
            print("✅ 接口存在：ak.stock_lhb_hyyyb_em")
            
            # 查看接口文档
            func = getattr(ak, 'stock_lhb_hyyyb_em')
            if func.__doc__:
                print("\n接口文档:")
                print(func.__doc__)
            
            # 查看接口签名
            import inspect
            sig = inspect.signature(func)
            print(f"\n接口签名: {sig}")
            
            return True
        else:
            print("❌ 接口不存在：ak.stock_lhb_hyyyb_em")
            print("\n可用的类似接口:")
            # 查找类似的接口
            lhb_funcs = [name for name in dir(ak) if 'stock_lhb' in name.lower() and 'hyyyb' not in name.lower()]
            for func_name in sorted(lhb_funcs)[:10]:  # 只显示前10个
                print(f"  - {func_name}")
            return False
            
    except Exception as e:
        print(f"❌ 检查异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("stock_lhb_hyyyb_em 接口测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 先检查接口是否存在
    results.append(("接口存在性检查", test_stock_lhb_hyyyb_em_interface_check()))
    
    # 如果接口存在，运行其他测试
    if results[0][1]:
        results.append(("基本接口调用", test_stock_lhb_hyyyb_em_basic()))
        results.append(("带日期参数调用", test_stock_lhb_hyyyb_em_with_date()))
        results.append(("直接接口调用", test_stock_lhb_hyyyb_em_direct()))
        results.append(("获取最近数据", test_stock_lhb_hyyyb_em_recent()))
    
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
