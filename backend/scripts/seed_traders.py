"""
种子导入：游资与营业部映射（含营业部代码）
执行：PYTHONPATH=. python backend/scripts/seed_traders.py
"""
from typing import List, Dict

from app.database.session import SessionLocal
from app.models.lhb import Trader, TraderBranch


# 每个 item: name, aka, branches=[{name, code}]
SEEDS: List[Dict] = [
    {
        "name": "章盟主(章建平)",
        "aka": "章盟主,章建平",
        "branches": [
            {"name": "国泰君安上海江苏路", "code": "10050001"},
            {"name": "国泰君安上海海阳西路", "code": "10050002"},
            {"name": "国泰君安宁波广福街", "code": "10050003"},
            {"name": "国泰君安宁波彩虹北路", "code": "10050004"},
            {"name": "海通证券上海徐汇建国西路", "code": "10010005"},
            {"name": "中信证券杭州延安路", "code": "10020006"},
            {"name": "中信证券杭州富春路", "code": "10020007"},
            {"name": "申万宏源上海闵行东川路", "code": "10030008"},
        ],
    },
    {
        "name": "孙哥(孙煜/孙国栋)",
        "aka": "孙哥,孙煜,孙国栋",
        "branches": [
            {"name": "中信证券上海溧阳路", "code": "10020009"},
            {"name": "中信证券上海淮海中路", "code": "10020010"},
            {"name": "中信证券上海瑞金南路", "code": "10020011"},
            {"name": "中信证券上海张杨路", "code": "10020012"},
            {"name": "国泰君安上海福山路", "code": "10050005"},
        ],
    },
    {
        "name": "赵老哥(赵强)",
        "aka": "赵老哥,赵强",
        "branches": [
            {"name": "中国银河证券绍兴", "code": "10030001"},
            {"name": "中国银河证券杭州庆春路", "code": "10030002"},
            {"name": "浙商证券绍兴解放北路", "code": "10040001"},
            {"name": "华泰证券浙江分公司", "code": "10060001"},
            {"name": "中信证券杭州凤起路", "code": "10020013"},
            {"name": "方正证券杭州延安路", "code": "10070001"},
        ],
    },
    {
        "name": "方新侠",
        "aka": "方新侠",
        "branches": [
            {"name": "兴业证券陕西分公司", "code": "10080001"},
            {"name": "中信证券西安朱雀大街", "code": "10020014"},
            {"name": "开源证券西安西大街", "code": "10090001"},
            {"name": "华鑫证券西安科技路", "code": "10100001"},
        ],
    },
    {
        "name": "炒股养家",
        "aka": "炒股养家",
        "branches": [
            {"name": "华鑫证券上海红宝石路", "code": "10100002"},
            {"name": "华鑫证券宁波分公司", "code": "10100003"},
            {"name": "华鑫证券上海宛平南路", "code": "10100004"},
            {"name": "华鑫证券上海茅台路", "code": "10100005"},
            {"name": "华鑫证券上海松江营业部", "code": "10100006"},
            {"name": "华鑫证券上海浦雪路", "code": "10100007"},
            {"name": "华鑫证券上海自贸试验区分公司", "code": "10100008"},
        ],
    },
    {
        "name": "作手新一(舒泰峰)",
        "aka": "作手新一,舒泰峰",
        "branches": [
            {"name": "国泰君安南京太平南路", "code": "10050006"},
            {"name": "国泰君安南京洪武路", "code": "10050007"},
            {"name": "华泰证券南京长江路", "code": "10060002"},
        ],
    },
    {
        "name": "小鳄鱼(90后标杆)",
        "aka": "小鳄鱼",
        "branches": [
            {"name": "南京证券南京大钟亭", "code": "10110001"},
            {"name": "华泰证券上海武定路", "code": "10060003"},
            {"name": "华泰证券南京江宁天元东路", "code": "10060004"},
            {"name": "中信证券南京洪武北路", "code": "10020015"},
            {"name": "国泰君安南京江宁营业部", "code": "10050008"},
        ],
    },
    {
        "name": "消闲派",
        "aka": "消闲派",
        "branches": [
            {"name": "国泰君安宜昌沿江大道", "code": "10050009"},
            {"name": "国泰君安宜昌珍珠路", "code": "10050010"},
            {"name": "东方证券上海浦东银城中路", "code": "10070002"},
            {"name": "浙商证券宜昌东山大道", "code": "10040002"},
        ],
    },
    {
        "name": "毛老板",
        "aka": "毛老板",
        "branches": [
            {"name": "国泰君安北京光华路", "code": "10050011"},
            {"name": "方正证券乐山龙游路", "code": "10070003"},
            {"name": "广发证券上海浦东东方路", "code": "10080002"},
            {"name": "申万宏源深圳金田路", "code": "10030009"},
            {"name": "东亚前海证券上海分公司", "code": "10120001"},
            {"name": "东莞证券湖北分公司", "code": "10130001"},
        ],
    },
    {
        "name": "宁波桑田路",
        "aka": "宁波桑田路",
        "branches": [
            {"name": "国盛证券宁波桑田路", "code": "10140001"},
            {"name": "国盛证券宁波彩虹北路", "code": "10140002"},
            {"name": "国泰君安宁波中山东路", "code": "10050012"},
            {"name": "中信证券宁波解放南路", "code": "10020016"},
        ],
    },
    {
        "name": "上塘路(扫板之王)",
        "aka": "上塘路",
        "branches": [
            {"name": "财通证券杭州上塘路", "code": "10063083"},
            {"name": "联储证券浙江分公司", "code": "10150001"},
            {"name": "财通证券杭州解放东路", "code": "10060005"},
            {"name": "财通证券杭州文二西路", "code": "10060006"},
        ],
    },
    {
        "name": "成都系",
        "aka": "成都系",
        "branches": [
            {"name": "国泰君安成都北一环路", "code": "10050013"},
            {"name": "华泰证券成都南一环路", "code": "10060007"},
            {"name": "华泰证券成都蜀金路", "code": "10060008"},
            {"name": "中信证券成都天府大道", "code": "10020017"},
            {"name": "国金证券成都东城根街", "code": "10090002"},
        ],
    },
    {
        "name": "佛山系(无影脚)",
        "aka": "佛山系,无影脚",
        "branches": [
            {"name": "光大证券佛山绿景路", "code": "10100009"},
            {"name": "光大证券佛山季华六路", "code": "10100010"},
            {"name": "华泰证券佛山灯湖东路", "code": "10060009"},
            {"name": "广发证券佛山汾江中路", "code": "10080003"},
        ],
    },
    {
        "name": "深圳系(深南哥)",
        "aka": "深圳系,深南哥",
        "branches": [
            {"name": "招商证券深圳深南东路", "code": "10110002"},
            {"name": "华泰证券深圳益田路荣超商务中心", "code": "10060010"},
            {"name": "中信证券深圳福田金田路", "code": "10020018"},
            {"name": "广发证券深圳民田路", "code": "10080004"},
        ],
    },
    {
        "name": "福州系(六一中路)",
        "aka": "福州系,六一中路",
        "branches": [
            {"name": "招商证券福州六一中路", "code": "10110003"},
            {"name": "华泰证券天津东丽开发区二纬路", "code": "10060011"},
            {"name": "兴业证券福州湖东路", "code": "10080005"},
        ],
    },
    {
        "name": "陈小群(95后黑马)",
        "aka": "陈小群",
        "branches": [
            {"name": "财通证券舟山普陀山", "code": "10060012"},
            {"name": "中国银河证券大连黄河路", "code": "10030003"},
            {"name": "甬兴证券慈溪新城大道北路", "code": "10150002"},
            {"name": "华鑫证券上海莲花路", "code": "10100011"},
            {"name": "国泰君安上海江苏路", "code": "10050001"},
        ],
    },
    {
        "name": "92科比",
        "aka": "92科比",
        "branches": [
            {"name": "华泰证券无锡金融一街", "code": "10060013"},
            {"name": "中信证券无锡清扬路", "code": "10020019"},
            {"name": "国联证券无锡中山路", "code": "10160001"},
        ],
    },
    {
        "name": "余哥",
        "aka": "余哥",
        "branches": [
            {"name": "华泰证券台州中心大道", "code": "10060014"},
            {"name": "浙商证券台州环城东路", "code": "10040003"},
            {"name": "光大证券宁波解放南路", "code": "10100012"},
        ],
    },
    {
        "name": "越王大道",
        "aka": "越王大道",
        "branches": [
            {"name": "财通证券绍兴越王大道", "code": "10060015"},
            {"name": "浙商证券绍兴解放北路", "code": "10040001"},
        ],
    },
    {
        "name": "中山东路",
        "aka": "中山东路",
        "branches": [
            {"name": "国泰君安上海松江中山东路", "code": "10050014"},
            {"name": "中信证券宁波中山东路", "code": "10020020"},
        ],
    },
    {
        "name": "拉萨天团(散户集中营)",
        "aka": "拉萨天团,散户集中营",
        "branches": [
            {"name": "东方财富证券拉萨团结路第一", "code": "80542852"},
            {"name": "东方财富证券拉萨金融城南环路", "code": "80542853"},
            {"name": "东方财富证券拉萨东环路第二", "code": "80542854"},
            {"name": "东方财富证券拉萨团结路第二", "code": "80542855"},
            {"name": "东方财富证券拉萨东环路第一", "code": "80542856"},
            {"name": "东方财富证券拉萨柳梧察古大道", "code": "80542857"},
            {"name": "东方财富证券昌都两江大道", "code": "80542858"},
            {"name": "东方财富证券日喀则珠峰路", "code": "80542859"},
            {"name": "东方财富证券林芝察隅路", "code": "80542860"},
            {"name": "东方财富证券山南乃东路", "code": "80542861"},
        ],
    },
    {
        "name": "量化游资核心",
        "aka": "量化游资核心",
        "branches": [
            {"name": "华鑫证券上海分公司", "code": "10100012"},
            {"name": "中金公司上海分公司", "code": "10170001"},
            {"name": "国泰君安证券总部", "code": "10050015"},
            {"name": "中信证券上海分公司", "code": "10020021"},
            {"name": "华泰证券总部", "code": "10060016"},
        ],
    },
    {
        "name": "Asking(邱宝裕)",
        "aka": "Asking,邱宝裕",
        "branches": [
            {"name": "兴业证券福州湖东路", "code": "10080005"},
        ],
    },
    {
        "name": "瑞鹤仙",
        "aka": "瑞鹤仙",
        "branches": [
            {"name": "申万宏源上海东川路", "code": "10030008"},
            {"name": "中国银河宜昌新世纪", "code": "10030004"},
        ],
    },
    {
        "name": "交易猿",
        "aka": "交易猿",
        "branches": [
            {"name": "华泰证券天津东丽开发区二纬路", "code": "10060011"},
        ],
    },
    {
        "name": "徐晓",
        "aka": "徐晓",
        "branches": [
            {"name": "华泰证券厦门厦禾路", "code": "10060017"},
            {"name": "华泰证券苏州何山路", "code": "10060018"},
        ],
    },
    {
        "name": "温州帮",
        "aka": "温州帮",
        "branches": [
            {"name": "东吴证券江阴滨江东路", "code": "10180001"},
            {"name": "平安证券河南分公司", "code": "10190001"},
        ],
    },
]


def upsert_trader(session, name: str, aka: str | None, branches: List[Dict[str, str]]):
    trader = session.query(Trader).filter(Trader.name == name).first()
    if not trader:
        trader = Trader(name=name, aka=aka)
        session.add(trader)
        session.flush()
    else:
        trader.aka = aka
        session.query(TraderBranch).filter(TraderBranch.trader_id == trader.id).delete()

    for inst in branches:
        inst_name = (inst.get("name") or "").strip()
        inst_code = (inst.get("code") or "").strip() or None
        if not inst_name:
            continue
        branch = TraderBranch(
            trader_id=trader.id,
            institution_name=inst_name,
            institution_code=inst_code,
        )
        session.add(branch)
    session.flush()


def main():
    session = SessionLocal()
    try:
        for item in SEEDS:
            upsert_trader(
                session,
                name=item["name"],
                aka=item.get("aka"),
                branches=item.get("branches", []),
            )
        session.commit()
        print(f"导入完成，共 {len(SEEDS)} 个游资主体")
    finally:
        session.close()


if __name__ == "__main__":
    main()

