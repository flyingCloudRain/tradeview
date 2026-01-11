"""
直接解析导入涨停板分析数据脚本

使用方法:
    python scripts/import_limit_up_board_data.py

或者指定日期和文件:
    python scripts/import_limit_up_board_data.py --date 2025-01-20 --file data.txt
"""
import argparse
import re
from datetime import date, time, datetime
from pathlib import Path
from typing import Optional
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import SessionLocal
from app.services.limit_up_board_service import LimitUpBoardService
from app.schemas.limit_up_board import LimitUpBoardCreate, parse_keywords_to_tags


def parse_board_name(board_str: str) -> tuple[str, Optional[int]]:
    """
    解析板块名称和数量
    例如: "商业航天 * 29" -> ("商业航天", 29)
    """
    # 匹配格式: "板块名称 * 数量"
    match = re.match(r'^(.+?)\s*\*\s*(\d+)$', board_str.strip())
    if match:
        board_name = match.group(1).strip()
        board_count = int(match.group(2))
        return board_name, board_count
    # 如果没有数量，只返回板块名称
    return board_str.strip(), None


def parse_time(time_str: str) -> Optional[time]:
    """解析时间字符串"""
    if not time_str or not time_str.strip():
        return None
    try:
        # 支持 HH:MM:SS 或 HH:MM 格式
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def parse_float(value: str) -> Optional[float]:
    """解析浮点数"""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def parse_data_text(data_text: str, target_date: date) -> list[LimitUpBoardCreate]:
    """
    解析数据文本（支持多行文本或文件路径）
    """
    items = []
    lines = data_text.strip().split('\n')
    
    # 跳过表头（第一行）
    for line_num, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line:
            continue
        
        # 使用制表符分割
        parts = [part.strip() for part in line.split('\t')]
        if len(parts) < 4:
            print(f"警告: 第 {line_num} 行数据格式不正确，跳过: {line[:50]}...")
            continue
        
        try:
            board_str = parts[0]
            limit_up_days = parts[1] if len(parts) > 1 else None
            stock_code = parts[2] if len(parts) > 2 else None
            stock_name = parts[3] if len(parts) > 3 else None
            limit_up_time_str = parts[4] if len(parts) > 4 else None
            circulation_market_value_str = parts[5] if len(parts) > 5 else None
            turnover_amount_str = parts[6] if len(parts) > 6 else None
            keywords = parts[7] if len(parts) > 7 else None
            
            # 解析板块名称和数量
            board_name, board_count = parse_board_name(board_str)
            
            # 解析时间
            limit_up_time = parse_time(limit_up_time_str) if limit_up_time_str else None
            
            # 解析数值
            circulation_market_value = parse_float(circulation_market_value_str)
            turnover_amount = parse_float(turnover_amount_str)
            
            # 解析关键字为标签和涨停原因
            limit_up_reason, tags = parse_keywords_to_tags(keywords)
            
            item = LimitUpBoardCreate(
                date=target_date,
                board_name=board_name,
                board_stock_count=board_count,
                stock_code=stock_code,
                stock_name=stock_name,
                limit_up_days=limit_up_days,
                limit_up_time=limit_up_time,
                circulation_market_value=circulation_market_value,
                turnover_amount=turnover_amount,
                keywords=keywords,
                limit_up_reason=limit_up_reason,
                tags=tags
            )
            items.append(item)
        except Exception as e:
            print(f"错误: 第 {line_num} 行解析失败: {e}")
            print(f"  内容: {line[:100]}...")
            continue
    
    return items


# 用户提供的数据
USER_DATA = """板块	涨停天数	代码	个股	涨停时间	流通市值（亿元）	成交额（亿元）	涨停关键词
商业航天 * 29	11 天 9 板	600783.SH	鲁信创投	9:25:00	242.6	2.1	参投蓝箭航天 + 参投灵犀科创 + 创投 + 银座股份公司
商业航天 * 29	10 天 6 板	002202.SZ	金风科技	9:33:04	1074.5	7.8	参投蓝箭航天 + 军工 + 机械 + 风电 + 新疆
商业航天 * 29	9 天 5 板	002519.SZ	银河电子	13:51:53	167.7	17.9	参投蓝箭航天 + 军工 + 机器人 + 新能源
商业航天 * 29	9 天 5 板	601698.SH	中国卫通	9:25:00	1447.42	2069.1	太空算力 + 抗干扰卫星 + 卫星通信 + 中字头 + 低空经济
商业航天 * 29	10 天 5 板	600879.SH	航天电子	14:27:31	946.6	17.6	卫星通信 + 新型智慧光电 + 北斗对机（火）+ 特种电缆
商业航天 * 29	7 天 3 板	600776.SH	东方通信	14:24:36	194.5	219.8	卫通航天 + 新卫星制造 + 电子元器件 + 专精特新
商业航天 * 29	2 天 2 板	600475.SH	杭萧钢构	9:25:00	105.8	2.8	中杭元宇宙工装备 + 军工 + 核电 + 风电
商业航天 * 29	2 天 2 板	002342.SZ	巨力索具	9:25:00	84.3	2	商业航天 + 海上吊装 + 军工 + 核电 + 索具中心（杭州）+HJT
商业航天 * 29	2 天 2 板	603017.SH	中衡设计	9:25:00	36.7	0.6	商业航天 + 建筑设计 + 低空经济
商业航天 * 29	2 天 2 板	603010.SZ	旭升集团	9:40:50	243	8.9	卫供特斯拉 + SpaceX + 资产注入猜想
商业航天 * 29	1 板	301325.SZ	超频三	14:50:21	30.7	13.5	卫星供电 + 数模收中 + 资产注入猜想 + 机器人轻量化 + 实控人变更 + 供货特斯拉
商业航天 * 29	1 板	002187.SZ	广东骏亚	9:40:36	60.1	6.5	商业航天 + 百发链 + 黄金 + 全息 + 奥海
商业航天 * 29	1 板	002017.SZ	广信股份	9:51:15	146.9	14.7	卫星雷达 + SIM + 镀金 + 金融 + 商道 + 中电科旗下
商业航天 * 29	1 板	002278.SZ	神开股份	9:57:15	46.8	8.3	商业航天 + 氢能 + 碳纤维 + 深海作业机器人 + 可燃冰
商业航天 * 29	1 板	002246.SZ	达华智能	10:04:51	75.3	9.5	航天通信 + 机器人 + 星技术 + 华为 + 星链钻石
商业航天 * 29	1 板	002015.SZ	国机精工	10:00:24	245.8	18.6	卫星轴承 + 磁悬浮 + 液压 / 军工 + 盾构岩石设备
商业航天 * 29	1 板	300051.SZ	鲁银投资	10:08:07	51.9	6.1	太空航天 + 钠镁电池 + 拟购兴业碳材 + 网游
商业航天 * 29	1 板	600784.SH	鲁胜股份	10:21:58	33.8	2.6	航空航天 + 钒氮 + 光伏
商业航天 * 29	1 板	002835.SZ	趣睡股份	10:30:33	114.9	3.3	航天客机 + 机器人材料 + PEEK + 拟收购宁爱漫想开 + DVA + 钛白粉
商业航天 * 29	1 板	688387.SH	超募移动	11:08:38	519.5	10.1	卫星 + SG + 移动 + 通信 + AMC
商业航天 * 29	1 板	003987.SZ	慈文传媒	11:09:30	308	29.1	卫供中科宇航 + 周度网络设备 + 多元金融
商业航天 * 29	1 板	002428.SZ	云南锗业	13:55:04	254.7	31.4	商业航天 + 6 英寸锗基技术突破 + 材料 + 华为哈勃
商业航天 * 29	1 板	600113.SH	三友联众	13:55:20	110.2	41.3	卫星通信 + AI + 智能 + 镀表等
商业航天 * 29	1 板	002145.SH	金宏科技	13:59:25	551.2	59.5	商业航天 + 间接投资蓝箭 + 人形机器人（材料）+ 可降解料 + 新能源车
商业航天 * 29	1 板	002927.SZ	长亮技术	14:19:24	113.9	6.6	商业航天 + 固态支付 + 军工 + 低空经济
商业航天 * 29	1 板	002625.SZ	永泰长征	14:22:52	591.6	41.2	商业航天 + 隐身材料 +（航空中心）+ 电网设备 + 充电桩
商业航天 * 29	1 板	002296.SZ	紫翔科技	14:27:12	43.2	10.3	商业航天 + 人工智能 + 全钒液流电池 + 储能
商业航天 * 29	1 板	600917.SH	广电传媒	14:48:57	170.9	30.5	卫供授控产品 + 5G + 通信网设备 + 潮玩平台 + 湖南国资
商业航天 * 29	1 板	008815.SH	飞产玻璃	14:50:59	110.3	19.5	卫星核心产品 + 智通 AI（参股）-
AI 应用 * 11	5 天 5 板	300986.SZ	志特新材	9:47:57	114.5	5.6	AI 铝材（AI 材料）+ 铝模 + 装配式建筑 + 商业目标
AI 应用 * 11	2 天 2 板	003007.SZ	直真科技	14:04:15	32.3	7.5	AI + 商业航天 + 华为昇腾 + 异构算力 + 智能体
AI 应用 * 11	5 天 2 板	600880.SH	传化智联	11:03:25	207.4	8.4	AI 物流 + 双碳 Agnet + 轻资产交易 + 云经济 + AI 图文写作
AI 应用 * 11	5 天 2 板	603871.SH	梅花生物	14:51:29	78.7	6	AI 体育 + 权现经济 + 投资 AI 大模型 + 分子诊断
AI 应用 * 11	1 板	601299.SH	中国电信	10:59:11	1184	14.7	AI 媒体 + 商显 + AI 媒体 + 云运会 + 数据服务中心
AI 应用 * 11	1 板	002818.SZ	富森美	11:00:15	33.2	7.1	AI 实体 + 前沿 AI 载体 + 全云 + 数智
AI 应用 * 11	1 板	002029.SZ	七匹狼	13:32:45	93.4	8.4	参投深科技 + 男装（潮牌）+ 参投保险 + 控股股东持有光模块 + 光源系统
AI 应用 * 11	1 板	300476.SZ	恒为科技	13:37:06	49.3	12.5	AI 硬件 + 机器人 + AI + 异算力 + 智心 + 机器人
AI 应用 * 11	1 板	603985.SH	科远智慧	14:00:28	103.3	14.5	拟购 AI 大模型应用 + 华为 + 资产注入 + 机器像人
AI 应用 * 11	1 板	920207.BJ	众诚科技	14:02:39	18	5.7	AI 实体 + 代码 + 华为合数 + 数据安全 + 数据要素
AI 应用 * 11	1 板	300418.SZ	昆仑万维	14:52:36	677.7	102.9	AI 应用 + 大模型 + AI 算力芯片 + 音乐
AI 营销 * 8	5 天 4 板	603598.SH	引力传媒	9:33:14	69.4	41.7	合作火山引擎 + 字节 + 智源 + MCN + 半导体
AI 营销 * 8	6 天 3 板	002131.SZ	利欧股份	9:31:33	438.8	5.5	AI 营销 + 合作字节 + 合作百度 + 风禾 + 半导体
AI 营销 * 8	5 天 2 板	600556.SH	天下秀	14:47:46	141.4	22.7	AI 营销 + TiKTok + 小红书（MCN）+ 网红经济 + 人工智能
AI 营销 * 8	1 板	301186.SH	易点天下	13:02:04	145.2	22.6	AI 营销 + AI 大力（电商）+ 出海 + 营销 AI
AI 营销 * 8	1 板	600977.SH	创文互联	13:02:21	201.4	61.4	AI 整合 + 合作微软 + 电信 AI + 合作（腾讯字节）
AI 营销 * 8	1 板	002400.SZ	省广集团	13:46:53	178	44.1	AI 营销 + 省代 + TiKTok 核心代理商
AI 营销 * 8	1 板	300063.SZ	天龙集团	13:52:37	69	27.6	AI + 抖音 + 华为 + T
AI 营销 * 8	1 板	600410.SH	华胜天成	14:04:20	232.7	59.5	网传合作火山引擎 + 华为昇腾计算 + 智算中心 + AI 实体
AI 医疗 * 7	1 板	002044.SZ	美年健康	9:25:51	237.5	10.2	AI 健康 + AI 健管 + DeepSeek + 健康管理 AI 机器人 + 基因测序
AI 医疗 * 7	1 板	000503.SZ	国新健康	9:33:05	103.9	22	AI 医疗 + 数智医保（AI）+ 华为 + DRG/DIP
AI 医疗 * 7	1 板	300246.SZ	迦南科技	13:09:19	108.3	3.2	合作阿里健康 + 医疗 + 华为 + 为盟医疗 + 医疗器械
AI 医疗 * 7	1 板	002777.SZ	久远银海	13:40:03	82.2	8.5	蚂蚁医疗大模型 + AI 医疗 + 医保数智 + 华为昇腾
AI 医疗 * 7	1 板	603882.SH	金域医学	13:50:10	1849	11	AI 医疗 + DeepSeek + 基因测序 + 第三方 AI
AI 医疗 * 7	1 板	002030.SZ	达安基因	14:44:06	50.3	14.8	医学 AI + 合作医疗 + 大模型 + 健康管理机器人
AI 医疗 * 7	1 板	301230.SZ	泓博医药	14:38:09	51.8	10.2	AI 辅助制药平台 + CXO + 医药中间体 + 合成生物
数据中心 * 6	4 天 4 板	001400.SZ	红联科技	9:49:39	17	4.4	液冷通道 + 航天航空 + 汽车热管理 + 铝型材冲压模具
数据中心 * 6	2 天 2 板	603267.SZ	张北股份	9:34:24	29.5	3.3	数据中心 + 农产品 + 锦纶丝 + 锂电功能
数据中心 * 6	2 天 2 板	002130.SZ	振华股份	10:03:22	149.5	12.2	SOFC + 合作 BWE + 钴盐龙头 + 人工智能 + 特通信
数据中心 * 6	1 板	002849.SZ	威星智能	9:34:39	38.4	1.9	管合保华威尔 + AI + 算力 + 燃气 + 参股电回收企业
数据中心 * 6	1 板	600825.SH	美凯龙	13:20:51	310.8	8.4	数据中心 + 液冷 + HVAC 控制器 + 固态电池 + PET 复合铜箔
数据中心 * 6	1 板	002368.SZ	太极股份	13:24:30	143.3	28.5	数据中心 + 液冷预制 + 整机投资人 + 国产化
机器人 * 5	2 天 2 板	600215.SH	派斯林	9:54:11	38.7	6.1	机器人 + 六足仿生机器人 + 特斯拉（北美业务主）+ 汽车制造
机器人 * 5	3 天 2 板	605288.SH	凯迪股份	13:29:05	75.8	2.4	机器人零部件 + 智能医疗 + 光伏支架
机器人 * 5	1 板	002162.SZ	华心健康	9:57:36	57.8	2.7	智能康复机器人 + 辅具 + 老年医院
机器人 * 5	1 板	002535.SZ	悦心健康	13:25:23	49.4	6.5	转型医美 + 多元金融 + 智 + 参投 DeepSeek（公司否认）
机器人 * 5	1 板	603179.SH	新朋股份	14:22:33	437.9	26.3	可控机器人 + 特斯拉 + 汽车部件
核电 * 3	3 天 3 板	603015.SH	弘讯科技	9:49:52	69.2	9.5	核电 + 电机 + 机器人 + 芯片
核电 * 3	3 天 3 板	601106.SH	中国一重	11:14:07	271	26.9	可控核聚变 + 核电 + 燃气轮机 + 核电 + 机械制造 + 镍
核电 * 3	1 板	600973.SH	宝胜股份	14:02:59	120.1	21	可接核电（变压器）+ 第三代半导 + 稀土永磁
医药 * 4	5 天 2 板	601089.SH	翰元医药	14:37:33	145.3	3.1	小核酸药物 + 减毒 + 仿制药 + 医疗器械
医药 * 4	1 板	300875.SZ	联邦药业	13:26:18	50.9	2.3	创新药 + 特药 + SPAC + 乙肝 + 艾 + 支原体肺炎
医药 * 4	1 板	603018.SH	维康药业	14:04:44	60.3	6.2	中药创新药 + 药品通过 GMP 检查 + 医
医药 * 4	1 板	688221.SH	前沿生物	14:27:31	105.4	7.9	小核酸药物 + 国产抗艾新药 + 多肽
半导体 * 3	3 天 3 板	600637.SH	东方明珠	9:36:36	447.8	23.3	间接参股超聚变 + 参工 + 参股超聚变 + 星 + 合作 minimax
半导体 * 3	1 板	002729.SZ	中科国控	9:41:27	51.5	2.3	拟参国电中国电公司 + 电力 + 半导体 + 数智中心 + 海峡两岸
半导体 * 3	1 板	600962.SH	国机科技	9:51:07	39.4	2.2	省收埃因国产 GPU（算力）+ 平板 + 投资（光伏和海南）+ 国资
有色 * 3	1 板	600397.SH	江特设备	10:30:44	89.7	4	钨矿 + 完成大资产重组 + 控股股东江特控股 + 江西国资
有色 * 3	1 板	600549.SH	厦门钨业	13:18:44	748.8	33.1	钨矿 + 可控核聚变 + 稀土永磁 + 新能源正极 + 福建
有色 * 3	1 板	601958.SH	金钼股份	15:00:00	593	13.8	合作开发钼 + 石墨 + 锂电池 + 电池
其他 * 10	11 天 11 板	002931.SZ	隆盛股份	9:25:00	102.8	0.5	优先泌购入 + 前驱机器人 + 园林机械 + 半导体设备零部件
其他 * 10	2 天 2 板	002795.SZ	永顺泰	9:25:00	39.6	3.6	资产出售 + 光伏 + 河南酒销售 + 园林 + 木门
其他 * 10	1 板	002431.SZ	和胜股份	13:21:18	42.4	0.9	实控人变更 + 超薄铜（宁德）+ 医疗体外循环泵（被处置）
其他 * 10	1 板	920461.BJ	格利尔	13:07:30	10.6	2.8	实控人变更 + 磁性器件 + 光伏逆变器 + 新能源车 + 北交所
公告 * 4	5 天 5 板	002774.SZ	快意电梯	9:30:30	42.1	1.5	城市更新 + 电梯 + 智控一体机 + 一带一路
公告 * 4	13 天 5 板	600759.SH	洲际油气	14:55:58	95.4	27.1	石油 + 海南 + 海洋 + 油气 + 拟控股电子
公告 * 4	2 天 2 板	603288.SH	海天瑞声	14:51:19	146.7	14.3	三石重组 + 商汤 + 祥天 + 拟收购电子公司增资 + 电子电气
公告 * 4	1 板	600676.SH	交运股份	10:22:35	69	5.1	参上普（成）+ 上海鸿道 + 参投 + 持股"""


def main():
    parser = argparse.ArgumentParser(description='直接解析导入涨停板分析数据')
    parser.add_argument('--date', type=str, default=None, help='日期，格式：YYYY-MM-DD（默认使用今天）')
    parser.add_argument('--file', type=str, default=None, help='数据文件路径（如果不指定，使用内置数据）')
    parser.add_argument('--delete-old', action='store_true', help='删除该日期的旧数据')
    parser.add_argument('--no-auto-extract', action='store_true', help='不自动从关键字提取概念板块')
    
    args = parser.parse_args()
    
    # 确定日期
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"错误: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
            return
    else:
        target_date = date.today()
        print(f"使用默认日期: {target_date}")
    
    # 读取数据
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"错误: 文件不存在: {args.file}")
            return
        print(f"正在读取文件: {args.file}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data_text = f.read()
    else:
        print("使用内置数据")
        data_text = USER_DATA
    
    # 解析数据
    print(f"正在解析数据...")
    items = parse_data_text(data_text, target_date)
    print(f"解析完成，共 {len(items)} 条记录")
    
    if not items:
        print("警告: 没有解析到任何数据")
        return
    
    # 连接数据库
    db = SessionLocal()
    try:
        # 如果需要，删除旧数据
        if args.delete_old:
            deleted_count = LimitUpBoardService.delete_by_date(db, target_date)
            print(f"已删除 {deleted_count} 条旧数据")
        
        # 批量导入
        print(f"正在导入数据到数据库（日期: {target_date}）...")
        auto_extract = not args.no_auto_extract
        LimitUpBoardService.batch_create(db, items, auto_extract)
        print(f"✓ 导入成功！共导入 {len(items)} 条记录")
        if auto_extract:
            print("✓ 已自动从关键字提取概念板块关联")
        
    except Exception as e:
        print(f"✗ 错误: 导入失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
