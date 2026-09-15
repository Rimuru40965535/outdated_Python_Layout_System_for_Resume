"""
================================================================================
简历多版本管理 (ResumeVersions)
================================================================================
功能概述：
    1. 存储基本数据
    1. 定义多个版本的简历，并使用这些数据填充简历
    3. 选择简历版本生成
================================================================================
"""

from ResumeCore import Profiles, SkillsAwards, Details, Section, Resume

# ============================================================================
# 完整填写的示例数据
# ============================================================================
profile = Profiles(
    photo = ".\\Resources\\photo_1.png",
    name = "利姆露",
    telephone = "114-5141-9810",
    locate = "中央都市利姆露",
    email = "1145141919@qq.com",
    social_media_qq = "1145141919810",
    #social_media_wechat = "WeChat_114514",
    #联络地址有点长，但是对于简历是不必要的。因此在现行版本中不急于更新。
    #contact_address = "中央都市利姆露\n中央大街29号\n鸠拉联邦国务院329办公室",
    website = "",
    title = "史莱姆转生者",
    summary = "从史莱姆转生为魔王，拥有强大的吞噬和模拟能力。"
    )

profile_skillsawards = SkillsAwards(
    skills_title = "掌握技能",
    skills = [
            "熟练 | Word",
            "熟练 | Excel",
            "熟练 | PowerPoint",
            "熟练 | Python",
            "熟练 | C++",
            "入门 | AI辅助程序开发",
            ],
    qualifications_title = "获得证书",
    qualifications = [
            "CET_4",
            "CET_6",
            ],
    awards_title = "获得荣誉",
    awards = [
            "治国理政一等奖",
            ],
    )

education_history = Section(
    icon = ".\\Resources\\icon_Education_History.png",
    title = "教育背景",
    details = [
        Details(
            key="鸠拉联邦中央大学",
            during_time="2020.09 - 2024.06",
            tags="马克思主义经济学基本原理 | 本科",
            description="主修课程：数据结构、操作系统、计算机网络、数据库原理、软件工程。\n毕业论文：基于深度学习的图像分类算法研究。",
            description_height=12,#通常一行留6单位。
            ) ,
        Details(
            key="利姆露中央高中",
            during_time="2017.09 - 2020.06",
            tags="理科实验班",
            description="高考成绩：全省前 5%，数学 148/150。",
            description_height=6,
            ) ,
        ]
    )

project_history = Section(
    icon = ".\\Resources\\icon_Project_History.png",
    title = "项目经历",
    details = [
        Details(
            key="基于PDF的简历自动生成系统",
            during_time="2025.03 - 2025.06",
            tags="Python, FPDF, 排版引擎",
            description="设计并实现了一套基于 Python 的 PDF 简历自动生成系统。\n系统采用分层排版引擎，支持样式定制、多模板切换、自动分栏等高级功能。",
            description_height=12,
            ) ,
        Details(
            key="数据可视化看板开发",
            during_time="2024.09 - 2024.12",
            tags="Vue.js, ECharts, Flask",
            description="为某电商公司开发了实时数据监控看板，展示销售、流量、转化等核心指标。\n使用 WebSocket 实现实时数据更新，日活用户 200+。",
            description_height=12,
            ) ,
        ]
    )

Resume(
    intend_company="腾讯科技",
    intend_job="后端开发工程师",
    profile=profile,
    skills_awards = profile_skillsawards,
    sections=[
        education_history,
        project_history,
        ],
    summary_icon = ".\\Resources\\icon.png",
    summary="5年全栈开发经验，熟悉 Python、Java、Go 等语言。\n"
            "有丰富的 Web 应用和系统架构设计经验.\n"
            "善于解决复杂技术问题。",
    summary_height=18,
    Lead = {
        "Left_Column_Above_All":                                10,     #左栏上方的留白
        "Left_Column_Below_Photo_Avove_Name":                   5,      #照片下方、名字上方的留白
        "Left_Column_Below_Name_Above_Contacts":                5,      #名字下方、联系方式上方的留白
        "Left_Column_Between_Contacs":                          5,      #联系方式之间的留白
        "Left_Column_Below_Contacts_Above_Skills&Awards":       5,      #联系方式下方、技能与获奖上方留白
        "Left_Column_Between_Skills&Awards":                    5,      #技能与获奖之间留白
        "Left_Column_Below_All":                                0,      #左栏下方的留白

        "Right_Column_Above_All":                               10,     #右栏上方的留白
        "Right_Column_Between_SectionTitle_SectionDetails":     3,      #节内标题与详情之间的间距
        "Right_Column_Between_Sections":                        5,      #节间距
        "Right_Column_Between_Details":                         5,      #节内详情间距
        "Right_Column_Below_All":                               0,      #右栏下方的留白
        }
)       .Generate(debug = 0,output_dir = ".\\output\\release")
#   ^这里的#可以选择不生成这一版简历


# ============================================================================
# 空模板
# ============================================================================
Resume(
    intend_company="",
    intend_job="",
    profile=None,
    skills_awards = None,
    sections=[],
    summary_icon = "",
    summary= "" ,
    summary_height=18,
    Lead = {
        "Left_Column_Above_All":                                10,     #左栏上方的留白
        "Left_Column_Below_Photo_Avove_Name":                   5,      #照片下方、名字上方的留白
        "Left_Column_Below_Name_Above_Contacts":                5,      #名字下方、联系方式上方的留白
        "Left_Column_Between_Contacs":                          5,      #联系方式之间的留白
        "Left_Column_Below_Contacts_Above_Skills&Awards":       5,      #联系方式下方、技能与获奖上方留白
        "Left_Column_Between_Skills&Awards":                    5,      #技能与获奖之间留白
        "Left_Column_Below_All":                                0,      #左栏下方的留白

        "Right_Column_Above_All":                               10,     #右栏上方的留白
        "Right_Column_Between_SectionTitle_SectionDetails":     3,      #节内标题与详情之间的间距
        "Right_Column_Between_Sections":                        5,      #节间距
        "Right_Column_Between_Details":                         5,      #节内详情间距
        "Right_Column_Below_All":                               0,      #右栏下方的留白
        }
)       .Generate(debug = 0,output_dir = ".\\output\\debug")
