"""
@file database.py
@brief SQLite 数据库初始化与连接管理模块。

该模块负责创建文本库和文档记录表，并插入少量示例文本，
保证项目在首次启动时即可进行完整演示。

@author TextTreeDoc 项目组
@date 2026
"""

import json
import sqlite3
from datetime import datetime
from typing import Iterable

from app.core.config import DB_PATH, ensure_runtime_dirs


def get_connection() -> sqlite3.Connection:
    """
    @brief 获取 SQLite 数据库连接。

    @return SQLite 连接对象，row_factory 已设置为 sqlite3.Row。
    """
    ensure_runtime_dirs()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """
    @brief 初始化数据库表并写入演示数据。

    @return None。

    首次运行时自动创建 texts 和 documents 表，避免用户需要手动准备文本库。
    """
    ensure_runtime_dirs()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS text_libraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT NOT NULL,
                keywords TEXT,
                source_type TEXT,
                source_url TEXT,
                library_id INTEGER,
                created_at TEXT,
                created_by TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                topic TEXT,
                tree_json TEXT,
                docx_path TEXT,
                created_at TEXT,
                created_by TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                caption TEXT,
                description TEXT,
                file_path TEXT NOT NULL,
                content_type TEXT,
                created_at TEXT,
                created_by TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS template_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                config_json TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TEXT
            )
            """
        )
        _ensure_texts_library_id_column(connection)
        default_library_id = _ensure_default_library(connection)
        connection.execute(
            "UPDATE texts SET library_id = ? WHERE library_id IS NULL",
            (default_library_id,),
        )
        _ensure_seed_texts(connection, default_library_id)
        _ensure_default_template_config(connection)
        connection.commit()


def _ensure_texts_library_id_column(connection: sqlite3.Connection) -> None:
    """
    @brief 兼容旧数据库，为 texts 表补充 library_id 字段。

    @param connection SQLite 数据库连接。
    @return None。
    """
    columns = [row["name"] for row in connection.execute("PRAGMA table_info(texts)").fetchall()]
    if "library_id" not in columns:
        connection.execute("ALTER TABLE texts ADD COLUMN library_id INTEGER")


def _ensure_default_library(connection: sqlite3.Connection) -> int:
    """
    @brief 确保默认文本库存在。

    @param connection SQLite 数据库连接。
    @return 默认文本库 id。
    """
    row = connection.execute(
        "SELECT id FROM text_libraries WHERE name = ? ORDER BY id LIMIT 1",
        ("默认文本库",),
    ).fetchone()
    if row:
        return int(row["id"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = connection.execute(
        """
        INSERT INTO text_libraries (name, description, created_at)
        VALUES (?, ?, ?)
        """,
        ("默认文本库", "系统初始化创建的默认资料库。", now),
    )
    return int(cursor.lastrowid)


def _ensure_default_template_config(connection: sqlite3.Connection) -> None:
    """
    @brief 确保默认模板配置存在。

    @param connection SQLite 数据库连接。
    @return None。
    """
    count = connection.execute("SELECT COUNT(*) FROM template_configs").fetchone()[0]
    if count:
        return
    default_config = {
        "length": 70,
        "professionalism": 80,
        "formality": 75,
        "structure": 85,
        "evidence": 70,
        "tables": 50,
        "creativity": 40,
    }
    connection.execute(
        """
        INSERT INTO template_configs (name, config_json, is_default, created_at)
        VALUES (?, ?, 1, ?)
        """,
        (
            "默认模板配置",
            json.dumps(default_config, ensure_ascii=False),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def _ensure_seed_texts(connection: sqlite3.Connection, library_id: int) -> None:
    """
    @brief 确保默认文本库包含演示资料。

    @param connection SQLite 数据库连接。
    @param library_id 默认文本库 id。
    @return None。
    """
    existing_titles = {
        row["title"]
        for row in connection.execute(
            "SELECT title FROM texts WHERE library_id = ? AND source_type = ?",
            (library_id, "seed"),
        ).fetchall()
    }
    seed_texts = [item for item in _build_seed_texts(library_id) if item[0] not in existing_titles]
    if seed_texts:
        connection.executemany(
            """
            INSERT INTO texts (title, summary, content, keywords, source_type, source_url, library_id, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'system')
            """,
            seed_texts,
        )


def _build_seed_texts(library_id: int) -> list[tuple[str, str, str, str, str, str, int, str]]:
    """
    @brief 构建课程演示用的示例文本。

    @param library_id 默认文本库 id。
    @return 示例文本列表。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seed_texts: Iterable[tuple[str, str, str, str, str, str, int, str]] = [
        (
            "开源许可证概述",
            "开源许可证用于规定软件使用、复制、修改和分发的权利与义务。",
            "开源许可证是开源软件生态的重要基础。MIT 许可证较为宽松，允许商业使用和再分发；GPL 许可证强调派生作品也应保持开源；Apache-2.0 许可证额外提供专利授权条款。选择许可证时需要结合项目目标、社区协作方式和合规要求。",
            "开源,许可证,MIT,GPL,Apache",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "课程报告自动生成需求",
            "课程报告通常包含背景、资料分析、实现过程、结果展示和总结。",
            "在课程作业场景中，报告生成系统可以从文本库中提取资料，形成结构化文档树，再根据模板生成 Word 文档。系统重点应保证文本入库、主题检索、结构树生成和 docx 导出流程稳定。",
            "课程报告,文档生成,结构树,Word",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "表格在技术文档中的作用",
            "表格适合展示模块、功能、状态和对比信息。",
            "技术文档中常使用表格呈现模块清单、接口说明和实验结果。自动生成 Word 时，可以在文档结构树中加入 table 类型块，由后端转换为 Word 表格，增强报告的可读性和验收展示效果。",
            "表格,技术文档,Word,模块",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统项目背景",
            "该课程设计以学生为核心用户，围绕选课、成绩、好友关系、消息互动和转账预警构建数据库应用。",
            "学生选课与社交转账系统面向高校课程管理与学生互动场景，目标是在一个小型关系数据库应用中同时体现学业管理和社交行为管理。系统以学生为核心用户，围绕院系、课程、选课成绩、好友关系、站内消息、账户余额、转账记录和风险预警等对象展开设计。传统课程设计往往只覆盖单一的选课或成绩管理，本课题进一步加入好友关系与转账业务，使数据库模型既包含典型教学管理数据，也包含具有时序性和约束性的资金流动数据。通过该课题，可以综合训练需求分析、概念结构设计、逻辑结构设计、SQL 建表、约束设计、查询测试和事务控制等数据库课程核心能力。系统预期支持学生查看课程、完成选课、查询成绩、维护好友、发送消息和进行转账，同时要求管理员能够维护基础数据并观察异常转账行为。",
            "数据库,课程设计,项目背景,选课,转账,社交",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统需求分析",
            "系统需求包括基础信息管理、课程选课、成绩维护、好友消息、转账记录和异常预警等模块。",
            "从功能需求看，系统需要维护院系、学生、教师、课程等基础信息，并支持课程开设、学生选课和成绩记录。学生可以查询可选课程、提交选课记录、查看课程成绩；教师或管理员可以维护课程信息并录入成绩。社交部分要求学生之间可以建立好友关系，好友关系需要记录申请状态、建立时间和双方用户信息；消息模块用于保存发送方、接收方、消息内容和发送时间。转账模块要求记录转出学生、转入学生、转账金额、转账时间和备注信息，并在余额不足、金额异常或短时间频繁转账时产生预警记录。非功能需求方面，系统应保证数据完整性和参照一致性，例如选课记录必须关联真实学生和课程，成绩应限定合理范围，转账金额必须为正数，好友关系不能重复建立。查询需求包括学生课表查询、成绩统计、好友消息查询、转账流水查询、院系课程统计和异常行为分析。",
            "需求分析,功能需求,数据完整性,选课成绩,好友消息,异常预警",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统 ER 图设计",
            "概念结构设计可抽象出学生、院系、课程、选课、好友关系、消息、账户、转账和预警等实体。",
            "概念结构设计阶段需要从业务对象中识别核心实体及其联系。院系实体记录院系编号、院系名称和办公地点；学生实体记录学号、姓名、性别、年级、专业、所属院系和账户余额；教师实体记录教师编号、姓名、职称和所属院系；课程实体记录课程编号、课程名称、学分、开课院系和任课教师。选课记录是学生和课程之间的多对多联系，包含选课时间、成绩和平时表现等属性。好友关系用于描述学生与学生之间的社交联系，包含申请方、接收方、关系状态和建立时间。消息实体记录发送者、接收者、消息内容、发送时间和已读状态。转账记录实体连接两个学生账户，记录金额、时间、备注和处理状态。预警实体与转账记录或学生账户关联，用于记录异常类型、风险等级和处理结果。ER 图中需要明确一对多和多对多关系，例如一个院系拥有多个学生和课程，一个学生可以选择多门课程，一门课程也可以被多个学生选择。",
            "ER图,概念结构设计,实体,属性,联系,数据库设计",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统关系模式设计",
            "逻辑结构设计将 ER 模型转换为关系表，并明确主键、外键和完整性约束。",
            "将概念模型转换为关系模型时，可以设计 Department(dept_id, dept_name, location)、Student(student_id, name, gender, grade, major, dept_id, balance)、Teacher(teacher_id, name, title, dept_id)、Course(course_id, course_name, credit, dept_id, teacher_id)、Enrollment(student_id, course_id, enroll_time, score)、Friendship(friendship_id, requester_id, receiver_id, status, created_at)、Message(message_id, sender_id, receiver_id, content, sent_at, is_read)、Transfer(transfer_id, from_student_id, to_student_id, amount, transfer_time, remark)、Warning(warning_id, student_id, transfer_id, warning_type, level, handled) 等关系模式。每张表需要设置清晰的主键，跨表引用通过外键约束维护参照完整性。Enrollment 表可以使用 student_id 与 course_id 的组合主键，防止同一学生重复选择同一课程。Friendship 表应避免同一对学生重复建立关系，可通过唯一约束或业务逻辑控制。Transfer 表中的 amount 应设置正数约束，Student 表中的 balance 应避免出现非法负值。逻辑结构设计还应说明范式分析，避免学生姓名、课程名称等信息在多个业务表中重复存储导致更新异常。",
            "关系模式,主键,外键,完整性约束,范式,表结构",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统 SQL 实现",
            "物理实现阶段需要完成建表语句、约束定义、初始数据插入、视图和索引设计。",
            "数据库物理实现主要包括表结构创建、数据类型选择、约束定义和辅助对象设计。建表时，学生编号、课程编号、教师编号等字段可使用字符串或整数作为主键；姓名、课程名称、消息内容等字段使用变长字符类型；金额字段使用 decimal 类型以避免浮点误差；时间字段使用 datetime 或 timestamp 类型保存业务发生时间。外键约束用于保证学生、课程、教师和院系之间的引用关系。为了提升常用查询效率，可以在 Enrollment(student_id)、Enrollment(course_id)、Message(receiver_id)、Transfer(from_student_id)、Transfer(to_student_id)、Transfer(transfer_time) 等字段上创建索引。视图可以用于封装学生课表、成绩单、好友消息列表和转账流水等常见查询。初始数据应覆盖多个院系、多个学生、多门课程和若干转账记录，便于测试连接查询、聚合统计和异常预警功能。对于转账场景，可以通过事务保证扣款、收款和流水记录三步操作同时成功或同时失败。",
            "SQL,建表,索引,视图,事务,初始数据",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统查询测试",
            "测试部分可围绕单表查询、多表连接、聚合统计、事务一致性和异常约束进行验证。",
            "数据库测试需要从多个角度验证系统设计是否正确。单表查询可以测试学生基础信息、课程列表、院系列表和转账记录筛选。多表连接查询可以测试学生课表查询，通过 Student、Enrollment、Course、Teacher 等表连接得到课程名称、任课教师、学分和成绩；也可以通过 Message 与 Student 表连接得到消息发送者和接收者姓名。聚合查询可以统计每门课程的选课人数、平均成绩、各院系学生数量、学生转账总额和异常预警数量。事务测试应重点验证转账功能，例如当转出账户余额不足时，系统应拒绝转账并保持双方余额不变；当转账成功时，转出方余额减少、转入方余额增加、Transfer 表新增流水记录。约束测试包括重复选课、非法成绩、无效外键、负数转账金额和重复好友关系等场景。测试结果可以用表格列出测试编号、测试目的、SQL 示例、预期结果和实际结果。",
            "查询测试,连接查询,聚合统计,事务测试,约束测试",
            "seed",
            "",
            library_id,
            now,
        ),
        (
            "学生选课与社交转账系统总结与改进",
            "课程设计总结应说明完成情况、设计收获、存在不足和后续优化方向。",
            "通过学生选课与社交转账系统的设计与实现，可以较完整地覆盖数据库课程中的需求分析、ER 建模、关系模式转换、SQL 实现、约束设计和查询测试等内容。系统在业务上融合了学业数据和社交转账数据，能够体现多实体、多关系和多约束的数据库应用特点。设计过程中需要重点处理学生与课程之间的多对多关系、学生与学生之间的自关联关系，以及转账业务中的事务一致性问题。当前系统仍可以继续优化，例如增加更完善的权限控制，区分学生、教师和管理员的操作范围；进一步细化风险预警规则，识别短时间高频转账、大额转账和异常账户余额变化；优化索引设计和查询性能；完善前端展示和数据导入功能；增加更多测试数据和边界场景验证。总结部分还可以说明本次课程设计对数据库规范化设计、SQL 编写和实际业务建模能力的提升。",
            "总结,改进,权限控制,风险预警,性能优化,课程设计",
            "seed",
            "",
            library_id,
            now,
        ),
    ]
    return list(seed_texts)
