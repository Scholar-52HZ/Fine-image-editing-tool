"""
Matting Studio - 电商语义策划与文案裂变引擎 (E-Commerce Copywriter)
基于产品名称、用途/功效、受众定位与品牌调性，智能裂变出适合不同电商平台的标题、卖点标签与背书角标。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class EcommerceCopyBundle:
    """电商商用文案集合"""
    product_name: str
    headline: str                 # 痛点大标题 (用于小红书、主图顶栏)
    sub_headline: str             # 核心卖点副标题
    marketing_tags: list[str]     # 卖点小标签清单 (2~4个)
    benefit_badge: str            # 利益点角标 (如 "拍1发2", "爆款直降")
    detail_bullets: list[str]     # 详情页特征打钩列表
    clinical_claim: str           # 权威背书或用户口碑口号


def generate_copy_bundle(
    product_name: str,
    product_usage: str = "",
    target_audience: str = "",
    brand_tone: str = "极简轻奢",
) -> EcommerceCopyBundle:
    """
    智能文案裂变生成 (规则推理 + 语义模板)
    :param product_name: 产品名称 (如 "极光赋活紧致修护精华")
    :param product_usage: 核心用途功效 (如 "深层补水 · 熬夜暗沉急救")
    :param target_audience: 目标客户群体 (如 "25-35岁都市白领 / 熬夜党")
    :param brand_tone: 品牌风格基调
    :return: EcommerceCopyBundle 结构化文案包
    """
    p_name = product_name.strip() if product_name else "高定品质优选"
    usage = product_usage.strip() if product_usage else "日常高品质生活优选"
    audience = target_audience.strip() if target_audience else "品质生活家"

    # 1. 生成痛点大标题 (Headline)
    if "熬夜" in usage or "暗沉" in usage:
        headline = "熬夜垮脸救星！实测快速透光提亮"
    elif "补水" in usage or "水润" in usage or "保湿" in usage:
        headline = "澎湃水润透现！深层锁水不拔干"
    elif "紧致" in usage or "抗衰" in usage or "修护" in usage:
        headline = "紧致淡纹奇迹！筑牢肌肤抵御屏障"
    elif "洁净" in usage or "控油" in usage:
        headline = "净爽透气零负担！平衡水油通透洁净"
    elif "数码" in p_name or "耳机" in p_name or "音响" in p_name:
        headline = "沉浸硬核音质！声临其境澎湃听感"
    else:
        headline = f"品质之选！{p_name[:10]} 甄选新体验"

    # 2. 核心副标题 (Sub-Headline)
    sub_headline = usage if usage else "匠心质感 · 经久耐用"

    # 3. 提炼卖点标签 (Marketing Tags)
    raw_tags = [t.strip() for t in re.split(r"[,，·/|、\s]+", usage) if t.strip()]
    if not raw_tags:
        raw_tags = ["精选原料", "匠心工艺", "品质承诺"]
        
    tags = []
    for t in raw_tags[:3]:
        if len(t) <= 8:
            tags.append(t)
        else:
            tags.append(t[:8])
            
    # 补充品质背书标签
    if len(tags) < 3:
        if "白领" in audience or "敏感" in audience:
            tags.append("温和安心用")
        else:
            tags.append("官方正品保障")

    # 4. 利益点促销角标
    if "轻奢" in brand_tone or "高端" in brand_tone:
        benefit_badge = "官方尊享礼遇"
    elif "活力" in brand_tone:
        benefit_badge = "热卖爆款进行中"
    else:
        benefit_badge = "限时买1享更多"

    # 5. 详情页打钩要点 (Detail Bullets)
    detail_bullets = []
    for t in tags[:3]:
        detail_bullets.append(f"✔ 核心专研: {t}")
    while len(detail_bullets) < 3:
        detail_bullets.append("✔ 严苛品控检测合格")

    # 6. 权威背书口号
    clinical_claim = f"专为【{audience}】定制开发 · 真实口碑认证好评"

    return EcommerceCopyBundle(
        product_name=p_name,
        headline=headline,
        sub_headline=sub_headline,
        marketing_tags=tags,
        benefit_badge=benefit_badge,
        detail_bullets=detail_bullets,
        clinical_claim=clinical_claim,
    )
