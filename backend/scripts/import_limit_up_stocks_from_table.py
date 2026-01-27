"""
从表格格式导入涨停个股数据（包含概念题材和涨停原因）

使用方法:
    python scripts/import_limit_up_stocks_from_table.py --date 2026-01-13 --file data.txt

或者直接使用内置数据:
    python scripts/import_limit_up_stocks_from_table.py --date 2026-01-13
"""
import argparse
import re
from datetime import date, time, datetime
from pathlib import Path
from typing import Optional, List
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import SessionLocal
from app.services.limit_up_board_service import LimitUpBoardService
from app.services.stock_concept_service import StockConceptService
from app.schemas.limit_up_board import LimitUpBoardCreate, parse_keywords_to_tags


def parse_time(time_str: str) -> Optional[time]:
    """解析时间字符串，支持 HH:MM 格式"""
    if not time_str or not time_str.strip():
        return None
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def parse_float(value: str) -> Optional[float]:
    """解析浮点数，去除单位并转换为亿元"""
    if not value or not value.strip():
        return None
    try:
        value_clean = value.strip()
        # 处理"万"单位，转换为亿元（1万 = 0.0001亿）
        if '万' in value_clean:
            value_clean = value_clean.replace('万', '')
            num_value = float(value_clean)
            return num_value * 0.0001  # 转换为亿元
        # 处理"亿"单位
        elif '亿' in value_clean:
            value_clean = value_clean.replace('亿', '')
            return float(value_clean)
        else:
            # 没有单位，直接解析
            return float(value_clean)
    except ValueError:
        return None


def parse_consecutive_board_count(status: str) -> Optional[int]:
    """从状态字符串中提取连板数"""
    if not status or not status.strip():
        return None
    
    status = status.strip()
    # 匹配 "X连板" 格式
    match = re.search(r'(\d+)\s*连板', status)
    if match:
        return int(match.group(1))
    
    # 匹配 "首板"
    if '首板' in status:
        return 1
    
    # 匹配 "X天Y板" 格式，提取Y
    match = re.search(r'(\d+)\s*天\s*(\d+)\s*板', status)
    if match:
        return int(match.group(2))
    
    return None


def ensure_concept_exists(db, concept_name: str) -> Optional[int]:
    """确保概念板块存在，如果不存在则创建，返回概念ID"""
    if not concept_name or not concept_name.strip():
        return None
    
    concept_name = concept_name.strip()
    
    # 查找现有概念
    concept = StockConceptService.get_by_name(db, concept_name)
    if concept:
        return concept.id
    
    # 创建新概念（一级概念）
    concept_data = {
        'name': concept_name,
        'code': None,
        'description': None,
        'parent_id': None,
        'level': 1,
        'sort_order': 0
    }
    
    concept = StockConceptService.create(db, concept_data)
    print(f"  创建新概念板块: {concept_name} (ID: {concept.id})")
    return concept.id


def parse_table_data(data_text: str, target_date: date) -> List[LimitUpBoardCreate]:
    """
    解析表格格式的数据
    格式: | 名称 | 代码 | 涨停时间 | 状态 | 高位成交 | 实际流通 | 所属板块 | 涨停原因 |
    """
    items = []
    lines = data_text.strip().split('\n')
    
    # 跳过表头行（包含 "|" 和表头信息）
    data_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('|--') or '名称' in line and '代码' in line:
            continue
        if line.startswith('|') and line.endswith('|'):
            data_lines.append(line)
    
    for line_num, line in enumerate(data_lines, start=1):
        try:
            # 解析表格行，使用 | 分割，保留空字段
            # 去掉首尾的 |，然后分割
            line_clean = line.strip()
            if line_clean.startswith('|'):
                line_clean = line_clean[1:]
            if line_clean.endswith('|'):
                line_clean = line_clean[:-1]
            parts = [part.strip() for part in line_clean.split('|')]
            
            if len(parts) < 8:
                print(f"警告: 第 {line_num} 行数据字段不足（{len(parts)}个字段），跳过: {line[:50]}...")
                continue
            
            stock_name = parts[0] if len(parts) > 0 else ""  # 名称
            stock_code = parts[1] if len(parts) > 1 else ""  # 代码
            limit_up_time_str = parts[2] if len(parts) > 2 else ""  # 涨停时间
            status = parts[3] if len(parts) > 3 else ""  # 状态（涨停天数）
            turnover_amount_str = parts[4] if len(parts) > 4 else ""  # 高位成交（成交额）
            circulation_market_value_str = parts[5] if len(parts) > 5 else ""  # 实际流通（流通市值）
            board_name = parts[6] if len(parts) > 6 else ""  # 所属板块（概念板块）
            limit_up_reason = parts[7] if len(parts) > 7 else ""  # 涨停原因
            
            # 清理股票代码（去除可能的空格和特殊字符）
            stock_code = stock_code.strip()
            
            # 解析时间
            limit_up_time = parse_time(limit_up_time_str)
            
            # 解析数值
            turnover_amount = parse_float(turnover_amount_str)
            circulation_market_value = parse_float(circulation_market_value_str)
            
            # 解析连板数
            consecutive_board_count = parse_consecutive_board_count(status)
            
            # 涨停原因作为keywords，同时设置limit_up_reason
            keywords = limit_up_reason if limit_up_reason else None
            
            # 解析关键字为标签
            parsed_reason, tags = parse_keywords_to_tags(keywords)
            if parsed_reason and not limit_up_reason:
                limit_up_reason = parsed_reason
            
            # 处理概念板块名称（可能为空）
            concept_names = []
            if board_name and board_name.strip():
                concept_names.append(board_name.strip())
            
            # 从涨停原因中提取概念（如果包含"+"，可能是多个概念）
            if keywords:
                # 提取可能的概念名称（简单匹配，后续会通过服务进行精确匹配）
                keywords_parts = [p.strip() for p in keywords.split('+') if p.strip()]
                for part in keywords_parts:
                    # 如果部分包含概念关键词，尝试提取
                    # 这里主要依赖后续的概念匹配逻辑
                    pass
            
            item = LimitUpBoardCreate(
                date=target_date,
                board_name=board_name if board_name else "其他",  # 如果没有板块，使用"其他"
                board_stock_count=None,
                stock_code=stock_code,
                stock_name=stock_name,
                limit_up_days=status,  # 保存原始状态字符串
                limit_up_time=limit_up_time,
                circulation_market_value=circulation_market_value,
                turnover_amount=turnover_amount,
                keywords=keywords,
                limit_up_reason=limit_up_reason,
                tags=tags,
                consecutive_board_count=consecutive_board_count,
                concept_names=concept_names if concept_names else None
            )
            items.append(item)
            
        except Exception as e:
            print(f"错误: 第 {line_num} 行解析失败: {e}")
            print(f"  内容: {line[:100]}...")
            import traceback
            traceback.print_exc()
            continue
    
    return items


# 用户提供的数据
USER_DATA = """| 名称       | 代码       | 涨停时间 | 状态       | 高位成交   | 实际流通   | 所属板块       | 涨停原因                                                                 |
|------------|------------|----------|------------|------------|------------|----------------|--------------------------------------------------------------------------|
| 视觉中国   | 000681     | 09:25    | 2连板      | 32.07亿    | 156.25亿   | AI       | AIGC+版权；持有MiniMax股份产生公允价值变动损益，拥有海量高质量版权素材库 |
| 美年健康   | 002044     | 09:25    | 3连板      | 3.38亿     | 246.55亿   | AI       | AI医疗+阿里巴巴概念；与港仔机器人联合研发AI主动健康中心，阿里巴巴旗下公司持有股份 |
| 三维通信   | 002115     | 09:25    | 3连板      | 2.01亿     | 120.96亿   | AI       | AI营销+商业航天；子公司打造灵犀智能广告管理等平台，提升投放效率与AI应用水平 |
| 利欧股份   | 002131     | 09:25    | 3连板      | 5.27亿     | 502.50亿   | AI       | AI营销+液冷；利欧数字深化AI智能体布局，实现营销全环节智能化升级           |
| 省广集团   | 002400     | 09:25    | 3连板      | 29.58亿    | 175.34亿   | AI       | AI营销；自主研发灵犀AI创作平台，支持生成行业报告、广告创意素材等内容       |
| 直真科技   | 003007     | 09:25    | 4连板      | 3.78亿     | 20.80亿    | AI       | AI智能体+商业航天；运维大模型产品包含智能体管理能力，可设计和发布运维智能体 |
| 泓博医药   | 301230     | 09:25    | 3天2板     | 3.24亿     | 64.40亿    | AI       | AI医疗；利用开源代码建立AI模型，并与深势科技合作提升药物研发效率           |
| 新华网     | 603888     | 09:25    | 2连板      | 18.73亿    | 70.12亿    | AI       | AI+股权转让；已形成AI+政务与AI+安全两大产品线，政务服务数字人已上线 |
| 引力传媒   | 603598     | 09:25    | 7天6板     | 7.72亿     | 42.32亿    | AI       | AI营销+学节概念；战略级GEO事业部聚焦AI搜索+生成式营销，已与火山引擎建立合作 |
| 东方通信   | 600776     | 09:25    | 3连板      | 24.06亿    | 100.98亿   | AI       | AI智能体+商业航天；推出灵捷智能体，已在智能客服、外呼等核心场景实现落地   |
| 人民网     | 603000     | 09:25    | 2连板      | 6.10亿     | 122.33亿   | AI       | AI+文化传媒；推出AI写稿秘书、社交智能助理等工具，构建生成式AI内容安全测评系统 |
| 新里程     | 002219     | 09:30    | 首板       | 4.84亿     | 61.15亿    | AI       | AI医疗+中药；旗下医疗机构将AI技术应用于心血管等疾病诊疗，提升诊疗效率     |
| 天龙集团   | 300063     | 09:31    | 3连板      | 41.19亿    | 91.21亿    | AI       | AI营销；子公司AIGC工具矩阵整合多平台API，支持多模型协同工作               |
| 博济医药   | 300404     | 09:42    | 首板       | 4.08亿     | 32.45亿    | AI       | AI医疗；持续关注并积极探索AI技术在药物研发中的应用，提高研发效率           |
| 普蕊斯     | 301257     | 09:47    | 首板       | 5084万     | 30.07亿    | AI       | AI医疗；致力于构建高效协同的临床试验研发管理平台，融合AI技术         |
| 兰卫医学   | 301060     | 09:55    | 首板       | 1.73亿     | 26.12亿    | AI       | AI医疗；以自然语言处理等技术为基础，将全面运用生成式AI技术升级产品         |
| 中公教育   | 002607     | 09:56    | 首板       | 9.80亿     | 149.37亿   | AI       | AI+就业概念；加速AI+教育产品创新落地，已推出AI就业学习机等产品       |
| 贝瑞基因   | 000710     | 10:00    | 首板       | 2.29亿     | 36.81亿    | AI       | AI医疗；发布自研医疗智能平台GENOisi智能体，聚焦AI+基因检测融合            |
| 诺思格     | 301333     | 10:01    | 首板       | 1.70亿     | 29.68亿    | AI       | AI医疗；AI平台结合AI大语言模型，构建医药临床研究自有知识库           |
| 国际医学   | 000516     | 10:05    | 首板       | 3.45亿     | 89.45亿    | AI       | AI医疗+脑机接口；旗下医疗机构运用AI辅助诊疗，未来将构建智能化医联体 |
| 锦和商管   | 603682     | 10:09    | 首板       | 4177万     | 15.04亿    | AI       | AI+物业服务；在物业等服务模块加入AI客服进行智慧联动，提升服务效率   |
| 蔚蓝生物   | 603739     | 10:10    | 首板       | 7951万     | 17.66亿    | AI       | AI医疗；积极探索AI技术在酶蛋白优化等领域的应用，已成立相关实验室           |
| 外服控股   | 600662     | 10:12    | 首板       | 1.05亿     | 36.40亿    | AI       | AI智能体+就业概念；推出AI智能体求职助手"凌佳佳"，可提供简历撰写等全方位支持 |
| 普路通     | 002769     | 10:20    | 2连板      | 1.06亿     | 38.51亿    | AI       | AI电商+并购重组；拟收购公司用AI将服务经验转化为智能系统，构筑技术护城河   |
| 居然智家   | 000785     | 10:21    | 2连板      | 3.99亿     | 79.70亿    | AI       | AI+零售；旗下平台接入阿里巴巴通义千问大模型，实现AI设计辅助功能     |
| 思创医惠   | 300078     | 10:26    | 首板       | 4.28亿     | 52.59亿    | AI       | AI医疗；通过数据驱动结合AI进行临床科研，建立科研专病库               |
| 尔康制药   | 300267     | 10:27    | 首板       | 8.64亿     | 47.90亿    | AI       | AI医疗+医药；展示"AI+大健康"战略纵深布局，拥有多项AI技术相关软件著作权   |
| 百花医药   | 600721     | 10:29    | 首板       | 4.39亿     | 33.89亿    | AI       | AI医疗+创新药；有计划引入合作伙伴，将AI技术深度融入药物研发和临床试验     |
| 博纳影业   | 001330     | 13:00    | 首板       | 2.57亿     | 93.05亿    | AI       | AIGC+影视院线；正在重点推进三星堆IP系列内容开发，依托AI生产线打造内容     |
| 健魔信息   | 605186     | 13:05    | 首板       | 4634万     | 15.54亿    | AI       | AI医疗；已实现DeenSeek-R1模型本地化部署，应用于智能发药机等场景           |
| 海量数据   | 603138     | 13:33    | 首板       | 3.80亿     | 27.39亿    | AI       | AI；公司数据库正演进为一款多模融合、智能驱动的通用数据库新范式       |
| 海格通信   | 002465     | 09:25    | 2连板      | 46.51亿    | 447.68亿   | 商业航天       | 商业航天+脑机接口；深度参与卫星互联网重大工程，自主研制的射频基带芯片已通过验证 |
| 电科芯片   | 600877     | 09:25    | 2连板      | 15.63亿    | 160.94亿   | 商业航天       | 商业航天+芯片；产品序列中应用于低轨星座的Ka波段相控阵天线套片已实现量产   |
| 杭萧钢构   | 600477     | 09:25    | 4连板      | 15.79亿    | 63.83亿    | 商业航天       | 商业航天+钙钛矿电池；中标箭元中大型液体运载火箭总装总测及回收复用基地项目 |
| 金隅集团   | 601992     | 09:30    | 2连板      | 3.02亿     | 74.53亿    | 商业航天       | 商业航天+可控核聚变；子公司产品应用于多个卫星发射中心，并间接持有蓝箭鸿擎股权 |
| 巨力索具   | 002342     | 09:42    | 4连板      | 11.17亿    | 94.73亿    | 商业航天       | 商业航天；产品已系统性应用于多个航天工程，并延伸至商业航天前沿领域         |
| 坤泰股份   | 001260     | 10:59    | 首板       | 8266万     | 6.99亿     | 商业航天       | 商业航天；与航天科技集团上海研究所合作，获得航空航天前沿智能制造技术       |
| 鲁信创投   | 600783     | 11:21    | 13天11板   | 4.70亿     | 90.76亿    | 商业航天       | 商业航天+创投；参股基金在航空航天领域投资项目包括蓝箭航天、鸿侠科技等     |
| 海王生物   | 000078     | 10:30    | 首板       | 4.01亿     | 57.54亿    | 医药           | 流感+医药零售；下属子公司有疫苗冷链运输业务，在产治疗感冒的药品           |
| 荣昌生物   | 688331     | 11:25    | 首板       | 12.27亿    | 185.80亿   | 医药           | 创新药；就RC148签署独家授权许可协议，将获得首付款及里程碑付款             |
| 瑞康医药   | 002589     | 13:04    | 首板       | 1.41亿     | 39.95亿    | 医药           | 创新药；自主研发了中药液化智能装备，并合作研发治疗脂肪肝中医新药           |
| 三变科技   | 002112     | 13:43    | 首板       | 1.77亿     | 33.44亿    | 算力     | 变压器+数据中心；公司产品主要为油浸式变压器等，广泛应用于国家电网等企业 |
| 特变电工   | 600089     | 13:48    | 首板       | 47.58亿    | 133.62亿   | 智能电网   | 固态变压器+数据中心；公司已开发多端口电力电子变压器，并有多个工程示范应用项目落地 |
| 摩恩电气   | 002451     | 14:10    | 首板       | 4.02亿     | 33.48亿    | 智能电网      | 变压器；公司漆包线、丝包线等产品可用于油浸式变压器、干式变压器等         |
| 德龙汇能   | 000593     | 09:25    | 2连板      | 4.79亿     | 34.93亿    | 实控人变更     | 实控人变更+芯片；控股股东拟变更，新实控人旗下公司主营高端封装基板产品     |
| 真爱美家   | 003041     | 09:25    | 2连板      | 4.24亿     | 31.17亿    | 实控人变更     | 实控人变更+服装家纺；控股股东变更为探迹科技，该公司专注于数字生产力智能体平台 |
| 友邦吊顶   | 002718     | 09:40    | 9天7板     | 2.72亿     | 21.61亿    | 实控人变更     | 实控人变更；控股股东及实控人发生变更，受让方将发起部分要约收购             |
| 明牌珠宝   | 002574     | 09:31    | 2连板      | 2.32亿     | 17.34亿    | 黄金           | 黄金+TOPCon；公司拥有黄金饰品、铂金饰品与镶嵌饰品三大产品生产线           |
| 上海建工   | 600170     | 11:06    | 首板       | 14.38亿    | 148.84亿   | 黄金           | 黄金+数据中心；拥有厄立特里亚国科卡金矿的开采权和探矿权，承建多项数据中心 |
| 山东墨龙   | 002490     | 10:49    | 首板       | 2.23亿     | 25.14亿    | 石油石化       | 石油石化+一带一路；参加阿布扎比国际石油展并在中东国家签订产品订单         |
| 准油股份   | 002207     | 10:54    | 首板       | 3.05亿     | 16.44亿    | 石油石化       | 石油石化；为石油、天然气开采企业提供石油技术服务的专业化企业             |
| 帝科股份   | 300842     | 11:14    | 首板       | 6.11亿     | 89.66亿    | 光伏           | 钙钛矿电池+存储；全球领先的钙钛矿叠层电池导电浆料供应商                   |
| 钧达股份   | 002865     | 13:01    | 6天3板     | 9.60亿     | 125.07亿   | 光伏           | 钙钛矿电池+商业航天；深耕钙钛矿叠层电池研发，与尚翼光电开拓商业航天市场   |
| 锋龙股份   | 002931     | 09:25    | 13连板     | 8070万     | 64.64亿    | 机器人概念     | 机器人概念+实控人变更；优必选以"协议转让+要约收购"方式成为控股股东       |
| 莱克电气   | 603355     | 10:19    | 首板       | 4647万     | 40.92亿    | 机器人概念     | 机器人概念+家电；多元化发展电机业务，触达协作机器人领域                   |
| 交运股份   | 600676     | 09:25    | 3连板      | 3654万     | 45.31亿    |             | 并购重组；拟与控股股东进行资产置换，置入文体娱乐、旅游业相关资产           |
| 博菲电气   | 001255     | 09:30    | 2连板      | 1.18亿     | 10.31亿    | 核电           | 核电+高铁；主要产品应用于核电领域发电机                                   |
| 三江购物   | 601116     | 09:31    | 2连板      | 1.70亿     | 36.04亿    | 零售           | 零售+阿里巴巴概念；主营社区生鲜超市，第二大股东为阿里巴巴泽泰             |
| 宝莱特     | 300246     | 09:35    | 首板       | 4.39亿     | 25.34亿    | 医疗           | 医疗器械+股权转让；研发血液透析耗材，进行CRRT机型自主研发                 |
| 炬申股份   | 001202     | 09:42    | 2连板      | 2.70亿     | 11.30亿    | 其他           | 物流+有色金属；专注大宗商品物流与仓储，涵盖多种金属品类                   |
| 渤海化学   | 600800     | 09:52    | 首板       | 3.49亿     | 26.97亿    | 化工           | 化工；全资子公司专注丙烷制丙烯业务，年产丙烯60万吨                         |
| 澳洋健康   | 002172     | 10:03    | 首板       | 1.13亿     | 24.39亿    | AI         | 医美；打造骨科重点学科，发展医美、康养服务                               |
| 亚光股份   | 603282     | 10:50    | 首板       | 4982万     | 14.69亿    | 锂电池           | 锂电设备+专用设备；节能环保设备MVR系统客户覆盖碳酸锂制备行业               |
| 东南网架   | 002135     | 14:12    | 首板       | 1.11亿     | 36.82亿    | 光伏           | 绿色电力；拟投资建设萧山农光互补光伏电站项目                             |
| 展鹏科技   | 603488     | 14:28    | 5天4板     | 1.86亿     | 21.58亿    | 军工           | 军工+电梯概念；控股子公司开展军事仿真系统业务，提供空战仿真系统等         |"""


def main():
    parser = argparse.ArgumentParser(description='从表格格式导入涨停个股数据')
    parser.add_argument('--date', type=str, required=True, help='日期，格式：YYYY-MM-DD')
    parser.add_argument('--file', type=str, default=None, help='数据文件路径（如果不指定，使用内置数据）')
    parser.add_argument('--delete-old', action='store_true', help='删除该日期的旧数据')
    parser.add_argument('--no-auto-extract', action='store_true', help='不自动从关键字提取概念板块')
    
    args = parser.parse_args()
    
    # 确定日期
    try:
        target_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"错误: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
        return
    
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
    items = parse_table_data(data_text, target_date)
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
        
        # 确保所有概念板块存在
        print("正在检查概念板块...")
        concept_names_set = set()
        for item in items:
            if item.concept_names:
                concept_names_set.update(item.concept_names)
        
        for concept_name in concept_names_set:
            ensure_concept_exists(db, concept_name)
        
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
