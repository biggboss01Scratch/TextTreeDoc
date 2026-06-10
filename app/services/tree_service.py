"""
@file tree_service.py
@brief 文档结构树生成模块。

该模块根据用户主题和文本库检索结果构建 Python dict 文档树，
并保证输出可直接序列化为 JSON。

@author TextTreeDoc 项目组
@date 2026
"""


def generate_tree(topic: str, related_texts: list[dict]) -> dict:
    """
    @brief 根据主题和相关文本生成文档结构树。

    @param topic 用户输入的文档主题。
    @param related_texts 从文本库检索得到的资料列表。
    @return 文档结构树，包含 title 和 sections 字段。
    """
    if _is_database_topic(topic, related_texts):
        return _generate_database_design_tree(topic, related_texts)
    snippets = _build_snippets(related_texts)
    return {
        "title": topic,
        "sections": [
            {
                "heading": "1. 项目背景",
                "content": f"{topic} 需要结合课程目标、应用场景和实际需求展开分析。{snippets[0]}",
                "children": [],
            },
            {
                "heading": "2. 相关资料分析",
                "content": "本部分对课题相关内容进行归纳，为后续设计与实现提供依据。",
                "children": [
                    {
                        "heading": f"2.{index + 1} {item.get('title', '资料')}",
                        "content": item.get("summary") or item.get("content", "")[:160],
                        "children": [],
                    }
                    for index, item in enumerate(related_texts[:3])
                ],
            },
            {
                "heading": "3. 核心内容整理",
                "content": snippets[1],
                "children": [],
                "blocks": [
                    {
                        "type": "table",
                        "headers": ["资料标题", "关键词", "来源"],
                        "rows": [
                            [
                                item.get("title", ""),
                                item.get("keywords", ""),
                                item.get("source_type", "") or "manual",
                            ]
                            for item in related_texts[:5]
                        ],
                    }
                ],
            },
            {
                "heading": "4. 设计与实现",
                "content": "本部分围绕方案设计、关键模块、实现过程和结果展示进行说明。",
                "children": [],
            },
            {
                "heading": "5. 总结",
                "content": f"围绕“{topic}”，总结整体完成情况、主要收获和后续可改进方向。",
                "children": [],
            },
        ],
    }


def _is_database_topic(topic: str, related_texts: list[dict]) -> bool:
    """
    @brief 判断是否更适合使用数据库课程设计目录。
    """
    text = " ".join(
        [
            topic,
            *[
                f"{item.get('title', '')} {item.get('summary', '')} {item.get('keywords', '')} {item.get('content', '')[:300]}"
                for item in related_texts[:5]
            ],
        ]
    )
    keywords = ["数据库", "ER图", "ER 图", "关系模式", "SQL", "选课", "转账", "课程设计"]
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _generate_database_design_tree(topic: str, related_texts: list[dict]) -> dict:
    """
    @brief 为数据库课程设计生成更细粒度的本地兜底目录。
    """
    snippets = _build_snippets(related_texts)
    return {
        "title": topic,
        "sections": [
            {
                "heading": "1. 项目背景与需求分析",
                "content": f"本课题围绕“{topic}”展开，重点分析业务场景、用户角色和数据库应用需求。{snippets[0]}",
                "children": [
                    {"heading": "1.1 课题背景", "content": "说明课题来源、应用场景和设计意义。", "children": []},
                    {"heading": "1.2 系统目标", "content": "明确系统需要解决的问题和预期达到的功能目标。", "children": []},
                    {"heading": "1.3 用户角色分析", "content": "分析学生、教师、管理员等角色在系统中的使用需求。", "children": []},
                    {"heading": "1.4 功能需求概述", "content": "归纳选课、成绩、好友、消息、转账和预警等主要功能。", "children": []},
                ],
            },
            {
                "heading": "2. 概念结构设计",
                "content": "本部分从业务对象出发，抽象实体、属性和实体之间的联系。",
                "children": [
                    {"heading": "2.1 实体识别", "content": "识别学生、院系、课程、成绩、好友关系、消息和转账记录等核心实体。", "children": []},
                    {"heading": "2.2 属性设计", "content": "说明各实体的关键属性、普通属性和必要的业务字段。", "children": []},
                    {"heading": "2.3 联系与约束", "content": "分析实体之间的一对多、多对多关系及约束条件。", "children": []},
                    {"heading": "2.4 ER 图说明", "content": "结合 ER 图说明系统概念结构和业务关系。", "children": []},
                ],
            },
            {
                "heading": "3. 逻辑结构设计",
                "content": "本部分将概念模型转换为关系模型，并说明表之间的主外键关系。",
                "children": [
                    {"heading": "3.1 关系模式转换", "content": "将实体和联系转换为关系模式。", "children": []},
                    {"heading": "3.2 主键与外键设计", "content": "说明各数据表的主键、外键及引用关系。", "children": []},
                    {"heading": "3.3 完整性约束", "content": "说明实体完整性、参照完整性和用户自定义完整性约束。", "children": []},
                    {"heading": "3.4 表结构汇总", "content": "通过表格汇总主要数据表及字段含义。", "children": []},
                ],
            },
            {
                "heading": "4. 数据库物理实现",
                "content": "本部分说明数据库建表、数据初始化和关键数据库对象的实现过程。",
                "children": [
                    {"heading": "4.1 建表 SQL 设计", "content": "给出主要数据表的创建语句和字段类型。", "children": []},
                    {"heading": "4.2 初始数据插入", "content": "说明测试数据或基础数据的插入方式。", "children": []},
                    {"heading": "4.3 索引与视图设计", "content": "说明为提高查询效率或简化查询而设计的索引和视图。", "children": []},
                    {"heading": "4.4 事务与触发器设计", "content": "说明转账、预警等功能涉及的事务控制或触发器逻辑。", "children": []},
                ],
            },
            {
                "heading": "5. 核心功能实现",
                "content": snippets[1],
                "children": [
                    {"heading": "5.1 学生与院系管理", "content": "说明学生、院系等基础信息的维护方式。", "children": []},
                    {"heading": "5.2 课程与选课成绩管理", "content": "说明课程开设、选课记录和成绩维护逻辑。", "children": []},
                    {"heading": "5.3 好友关系与消息功能", "content": "说明好友关系建立、消息记录和社交互动数据设计。", "children": []},
                    {"heading": "5.4 转账与风险预警功能", "content": "说明转账记录、余额变更和异常预警处理。", "children": []},
                ],
            },
            {
                "heading": "6. 查询测试与结果分析",
                "content": "本部分通过典型查询和功能测试验证数据库设计的正确性。",
                "children": [
                    {"heading": "6.1 单表查询测试", "content": "验证基础信息查询和条件筛选功能。", "children": []},
                    {"heading": "6.2 多表连接查询测试", "content": "验证跨表业务查询，如学生选课、好友消息和转账记录查询。", "children": []},
                    {"heading": "6.3 聚合统计查询测试", "content": "验证成绩统计、课程人数统计和转账金额统计等功能。", "children": []},
                    {"heading": "6.4 异常场景测试", "content": "验证约束、事务和预警逻辑在异常输入下的表现。", "children": []},
                ],
            },
            {
                "heading": "7. 总结与改进",
                "content": f"围绕“{topic}”，总结数据库设计、功能实现和测试验证情况，并分析后续优化方向。",
                "children": [
                    {"heading": "7.1 完成情况", "content": "总结系统已实现的主要功能和数据库设计成果。", "children": []},
                    {"heading": "7.2 存在不足", "content": "分析当前系统在功能、性能或数据完整性方面的不足。", "children": []},
                    {"heading": "7.3 后续优化方向", "content": "提出界面、查询性能、安全性和业务扩展方面的改进思路。", "children": []},
                ],
            },
        ],
    }


def _build_snippets(related_texts: list[dict]) -> list[str]:
    """
    @brief 从相关文本中整理可写入章节的内容片段。

    @param related_texts 相关文本资料列表。
    @return 两个内容片段组成的列表。
    """
    if not related_texts:
        return ["当前可参考资料较少，报告可先围绕课程设计的一般要求展开。", "可结合需求分析、方案设计、实现过程和测试结果进行补充。"]
    summaries = [item.get("summary") or item.get("content", "")[:160] for item in related_texts]
    first = summaries[0] if summaries else ""
    combined = "；".join(summary for summary in summaries[:3] if summary)
    return [first, combined or first]
