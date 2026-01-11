"""
清理龙虎榜历史重复数据：
1) lhb_detail：同一日期+股票代码只保留一条，删除其余，并级联删除对应机构明细。
2) lhb_institution：同一 lhb_detail + 机构名称 + flag 只保留一条，删除其余。

执行方式：
    poetry run python backend/scripts/cleanup_lhb_duplicates.py
或：
    python backend/scripts/cleanup_lhb_duplicates.py
"""
from collections import defaultdict
from typing import List, Tuple

from sqlalchemy import and_, func

from app.database.session import SessionLocal
from app.models.lhb import LhbDetail, LhbInstitution


def clean_lhb_detail_duplicates(session) -> Tuple[int, int]:
    """去重 lhb_detail，返回 (删除的detail条数, 删除的institution条数)"""
    deleted_detail = 0
    deleted_institution = 0

    # 找出重复组
    dup_groups = (
        session.query(LhbDetail.date, LhbDetail.stock_code, func.count("*").label("cnt"))
        .group_by(LhbDetail.date, LhbDetail.stock_code)
        .having(func.count("*") > 1)
        .all()
    )
    if not dup_groups:
        print("✅ lhb_detail 未发现重复")
        return deleted_detail, deleted_institution

    print(f"发现 {len(dup_groups)} 组 lhb_detail 重复记录，开始清理...")

    for dt, code, _ in dup_groups:
        # 找出重复记录，按 id 升序，保留第一条
        records: List[LhbDetail] = (
            session.query(LhbDetail)
            .filter(and_(LhbDetail.date == dt, LhbDetail.stock_code == code))
            .order_by(LhbDetail.id.asc())
            .all()
        )
        keep = records[0]
        to_delete = records[1:]
        if not to_delete:
            continue

        delete_ids = [r.id for r in to_delete]

        # 删除对应机构
        del_inst = (
            session.query(LhbInstitution)
            .filter(LhbInstitution.lhb_detail_id.in_(delete_ids))
            .delete(synchronize_session=False)
        )
        deleted_institution += del_inst or 0

        del_detail = (
            session.query(LhbDetail)
            .filter(LhbDetail.id.in_(delete_ids))
            .delete(synchronize_session=False)
        )
        deleted_detail += del_detail or 0

        print(
            f"  [{dt} {code}] 保留 id={keep.id}, 删除 detail {del_detail} 条, 机构 {del_inst} 条"
        )

    session.commit()
    return deleted_detail, deleted_institution


def clean_lhb_institution_duplicates(session) -> int:
    """去重 lhb_institution，返回删除条数"""
    deleted = 0

    # 按 (lhb_detail_id, institution_name, flag) 分组统计
    dup_groups = (
        session.query(
            LhbInstitution.lhb_detail_id,
            LhbInstitution.institution_name,
            LhbInstitution.flag,
            func.count("*").label("cnt"),
        )
        .group_by(LhbInstitution.lhb_detail_id, LhbInstitution.institution_name, LhbInstitution.flag)
        .having(func.count("*") > 1)
        .all()
    )
    if not dup_groups:
        print("✅ lhb_institution 未发现重复")
        return deleted

    print(f"发现 {len(dup_groups)} 组 lhb_institution 重复记录，开始清理...")

    for lhb_id, inst_name, flag, _ in dup_groups:
        records: List[LhbInstitution] = (
            session.query(LhbInstitution)
            .filter(
                and_(
                    LhbInstitution.lhb_detail_id == lhb_id,
                    LhbInstitution.institution_name == inst_name,
                    LhbInstitution.flag == flag,
                )
            )
            .order_by(LhbInstitution.id.asc())
            .all()
        )
        keep = records[0]
        to_delete = records[1:]
        if not to_delete:
            continue

        del_ids = [r.id for r in to_delete]
        del_count = (
            session.query(LhbInstitution)
            .filter(LhbInstitution.id.in_(del_ids))
            .delete(synchronize_session=False)
        )
        deleted += del_count or 0
        print(
            f"  lhb_detail_id={lhb_id}, 机构={inst_name}, flag={flag or '-'} 保留 id={keep.id}, 删除 {del_count} 条"
        )

    session.commit()
    return deleted


def main():
    session = SessionLocal()
    try:
        detail_deleted, inst_deleted_from_detail = clean_lhb_detail_duplicates(session)
        inst_deleted = clean_lhb_institution_duplicates(session)

        print("=== 去重完成 ===")
        print(f"删除 lhb_detail: {detail_deleted} 条")
        print(f"删除 lhb_institution（因detail删除）: {inst_deleted_from_detail} 条")
        print(f"删除 lhb_institution（组内重复）: {inst_deleted} 条")
    finally:
        session.close()


if __name__ == "__main__":
    main()

