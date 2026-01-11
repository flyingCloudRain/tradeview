"""
测试游资CRUD功能
执行：PYTHONPATH=. python backend/scripts/test_trader_crud.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.trader_service import TraderService
from app.models.lhb import Trader, TraderBranch


def test_trader_crud():
    """测试游资CRUD功能"""
    print("="*70)
    print("🧪 测试游资CRUD功能")
    print("="*70)
    
    session = SessionLocal()
    try:
        # 1. 测试创建游资
        print("\n1️⃣ 测试创建游资")
        test_name = "测试游资_" + str(int(__import__('time').time()))
        try:
            trader = TraderService.create_trader(
                db=session,
                name=test_name,
                aka="这是一个测试游资",
                branch_names=["测试机构1", "测试机构2"]
            )
            print(f"   ✅ 创建成功: {trader.name} (ID: {trader.id})")
            print(f"   关联机构数: {len(trader.branches)}")
            trader_id = trader.id
        except Exception as e:
            print(f"   ❌ 创建失败: {str(e)}")
            return
        
        # 2. 测试获取游资
        print("\n2️⃣ 测试获取游资")
        trader = TraderService.get_trader_by_id(session, trader_id)
        if trader:
            print(f"   ✅ 获取成功: {trader.name}")
            print(f"   说明: {trader.aka}")
            print(f"   关联机构数: {len(trader.branches)}")
        else:
            print(f"   ❌ 获取失败")
            return
        
        # 3. 测试更新游资
        print("\n3️⃣ 测试更新游资")
        try:
            updated_trader = TraderService.update_trader(
                db=session,
                trader_id=trader_id,
                name=f"{test_name}_更新",
                aka="这是更新后的说明"
            )
            if updated_trader:
                print(f"   ✅ 更新成功: {updated_trader.name}")
                print(f"   新说明: {updated_trader.aka}")
            else:
                print(f"   ❌ 更新失败")
        except Exception as e:
            print(f"   ❌ 更新失败: {str(e)}")
        
        # 4. 测试添加机构
        print("\n4️⃣ 测试添加机构")
        try:
            branch = TraderService.add_branch(
                db=session,
                trader_id=trader_id,
                institution_name="测试机构3",
                institution_code="TEST001"
            )
            if branch:
                print(f"   ✅ 添加机构成功: {branch.institution_name}")
                trader = TraderService.get_trader_by_id(session, trader_id)
                print(f"   当前关联机构数: {len(trader.branches)}")
            else:
                print(f"   ❌ 添加机构失败")
        except Exception as e:
            print(f"   ❌ 添加机构失败: {str(e)}")
        
        # 5. 测试更新机构
        print("\n5️⃣ 测试更新机构")
        if trader and trader.branches:
            branch_id = trader.branches[0].id
            try:
                updated_branch = TraderService.update_branch(
                    db=session,
                    branch_id=branch_id,
                    institution_name="测试机构1_更新",
                    institution_code="TEST002"
                )
                if updated_branch:
                    print(f"   ✅ 更新机构成功: {updated_branch.institution_name}")
                    print(f"   机构代码: {updated_branch.institution_code}")
                else:
                    print(f"   ❌ 更新机构失败")
            except Exception as e:
                print(f"   ❌ 更新机构失败: {str(e)}")
        
        # 6. 测试删除机构
        print("\n6️⃣ 测试删除机构")
        trader = TraderService.get_trader_by_id(session, trader_id)
        if trader and len(trader.branches) > 0:
            branch_id = trader.branches[0].id
            try:
                success = TraderService.delete_branch(session, branch_id)
                if success:
                    print(f"   ✅ 删除机构成功")
                    trader = TraderService.get_trader_by_id(session, trader_id)
                    print(f"   剩余关联机构数: {len(trader.branches)}")
                else:
                    print(f"   ❌ 删除机构失败")
            except Exception as e:
                print(f"   ❌ 删除机构失败: {str(e)}")
        
        # 7. 测试删除游资
        print("\n7️⃣ 测试删除游资")
        try:
            success = TraderService.delete_trader(session, trader_id)
            if success:
                print(f"   ✅ 删除游资成功")
                # 验证是否已删除
                trader = TraderService.get_trader_by_id(session, trader_id)
                if trader is None:
                    print(f"   ✅ 验证通过：游资已从数据库中删除")
                else:
                    print(f"   ⚠️  警告：游资仍然存在")
            else:
                print(f"   ❌ 删除游资失败")
        except Exception as e:
            print(f"   ❌ 删除游资失败: {str(e)}")
        
        print("\n" + "="*70)
        print("✅ 测试完成")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    test_trader_crud()
