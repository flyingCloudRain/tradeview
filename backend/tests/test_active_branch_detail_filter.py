"""
测试活跃营业部交易详情过滤逻辑
"""
from dataclasses import dataclass

from app.services.active_branch_detail_service import ActiveBranchDetailService


@dataclass
class DummyBranch:
    buy_stock_count: int | None


def test_filter_branches_for_detail():
    """只保留买入个股数>1的营业部"""
    branches = [
        DummyBranch(buy_stock_count=None),
        DummyBranch(buy_stock_count=0),
        DummyBranch(buy_stock_count=1),
        DummyBranch(buy_stock_count=2),
        DummyBranch(buy_stock_count=5),
    ]

    filtered = ActiveBranchDetailService.filter_branches_for_detail(branches)  # type: ignore[arg-type]

    assert len(filtered) == 2
    assert filtered[0].buy_stock_count == 2
    assert filtered[1].buy_stock_count == 5
