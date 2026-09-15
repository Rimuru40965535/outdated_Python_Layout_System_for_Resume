"""
================================================================================
简历核心模块 (ResumeCore)
================================================================================
功能概述：
    1. 定义简历数据类：Profiles, Details, Section
    2. 定义 Resume 类，组织一份完整的简历
    3. 封装从数据到 PDF 的完整生成流程
    4. 依赖 ResumeTemplateV2 生成模板并填充数据

使用示例：
    >>> from ResumeCore import Profiles, Details, Section, Resume
    >>> 
    >>> # 创建个人信息
    >>> profile = Profiles()
    >>> profile.name = "张三"
    >>> profile.telephone = "138-0000-0000"
    >>> 
    >>> # 创建简历
    >>> resume = Resume(
    ...     intend_company="腾讯科技",
    ...     intend_job="后端开发工程师",
    ...     profile=profile,
    ...     sections=[...],
    ...     summary="5年全栈开发经验"
    ... )
    >>> 
    >>> # 生成 PDF
    >>> pdf_path = resume.Generate(debug=False)
    >>> print(pdf_path)

================================================================================
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import os
from datetime import datetime

# 导入排版引擎和模板
from LayoutEngineV2 import (
    LayoutObject,
    TextObject,
    ImageObject,
    RectangleObject,
    find_object_by_name,
    AlignX,
    AlignY,
    Padding,
    Color,
    Red,
    White,
    Black,
    Gray,
    Blue,
    Yellow,
    Green,
    RimuruBlue,
    layer_manager,
    objectRegister,
)
from fpdf import FPDF

# 导入模板 V2
from ResumeTemplateV2 import (
    Style,
    STYLES,
    generate_basic_subtemplate,
    generate_profile_template,
    generate_profile_photo_template,
    generate_section_title_template,
    generate_section_details_template,
    generate_summary_template,
    fill_profile_data,
    fill_section_title_data,
    fill_section_details_data,
    fill_summary_data,
)

import time

from functools import wraps

#计时器装饰器
def timer_for_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"🕓 >>> {func.__name__} 运行时间: {end - start:.4f} 秒")
        return result
    return wrapper


# ============================================================================
# 1. 数据类定义
# ============================================================================

@dataclass
class Profiles:
    """
    个人信息类
    
    存储与个人相关的基本信息，所有属性初始化为空字符串。
    同一个人只需要实例化一次。
    """
    photo: str = ""                     # 证件照资源存储路径
    name: str = ""                      # 名字
    telephone: str = ""                 # 电话号码
    locate: str = ""                    # 现居城市
    email: str = ""                     # 邮箱地址（修正：原 e-mail → email）
    social_media_qq: str = ""           # QQ号
    social_media_wechat: str = ""       # 微信号
    contact_address: str = ""           # 联系地址（修正：原 contact_sddress）
    # 可选扩展字段
    title: str = ""                     # 求职头衔/职位
    website: str = ""                   # 个人网站/GitHub
    summary: str = ""                   # 个人简介/自我评价
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "photo": self.photo,
            "name": self.name,
            "telephone": self.telephone,
            "locate": self.locate,
            "email": self.email,
            "social_media_qq": self.social_media_qq,
            "social_media_wechat": self.social_media_wechat,
            "contact_address": self.contact_address,
            "title": self.title,
            "website": self.website,
            "summary": self.summary,
        }
    
    def is_empty(self) -> bool:
        """检查是否为空"""
        return not any([
            self.name, self.telephone, self.email,
            self.social_media_qq, self.social_media_wechat
        ])



class SkillsAwards:
    """
    技能、证书与获奖情况
    """
    def __init__(self,
        skills_title :str = "掌握技能",
        skills :List[str] = [],
        qualifications_title :str = "获得证书",
        qualifications :List[str] = [],
        awards_title :str = "获得荣誉",
        awards :List[str] = [],
    ):
        self.skills_title = skills_title
        self.qualifications_title = qualifications_title
        self.awards_title = awards_title
        self.skills = skills
        self.qualifications = qualifications
        self.awards = awards
        
    def is_empty(self) -> bool:
        """检查是否为空"""
        return not any([
            self.skills,
            self.qualifications,
            self.awards,
        ])

    def get_char_skills(self)->str:
        result = ''
        for i in range(len(self.skills)):
            result += self.skills[i]
            if i < len(self.skills):
                result += '\n'
        return result

    def get_char_qualifications(self)->str:
        result = ''
        for i in range(len(self.qualifications)):
            result += self.qualifications[i]
            if i < len(self.qualifications):
                result += '\n'
        return result

    def get_char_awards(self)->str:
        result = ''
        for i in range(len(self.awards)):
            result += self.awards[i]
            if i < len(self.awards):
                result += '\n'
        return result

@dataclass
class Details:
    """
    单条详情数据类
    
    对应节详情子模板，存储一条具体经历的详细信息。
    """
    key: str = ""                       # 关键词（学校名/项目名/公司名）
    during_time: str = ""               # 起讫时间
    tags: str = ""                      # 补充关键信息（专业/技术栈）
    description: str = ""               # 详情描述
    description_height: float = 12.0    # description 排版高度（手动调参，默认12mm）
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "key": self.key,
            "during_time": self.during_time,
            "tags": self.tags,
            "description": self.description,
            "description_height": self.description_height,
        }
    
    def is_empty(self) -> bool:
        """检查是否为空"""
        return not any([self.key, self.description])


@dataclass
class Section:
    """
    章节类
    
    对应一个节标题和一组节详情，用于组织右栏内容。
    一个 Section 实例可以是"教育背景"、"项目经历"、"实习经历"等。
    """
    icon: str = ""                      # 节标题图标路径
    title: str = ""                     # 节标题文本
    details: List[Details] = field(default_factory=list)  # 节详情列表
    
    def add_detail(self, detail: Details) -> 'Section':
        """添加一条详情（链式调用）"""
        self.details.append(detail)
        return self
    
    def remove_detail(self, index: int) -> bool:
        """移除指定索引的详情"""
        if 0 <= index < len(self.details):
            self.details.pop(index)
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "icon": self.icon,
            "title": self.title,
            "details": [d.to_dict() for d in self.details],
        }
    
    def is_empty(self) -> bool:
        """检查是否为空"""
        return not self.title and not self.details



#间距默认值
__Lead_default_settings__ = {
    "Left_Column_Above_All":                                10,     #左栏上方的留白
    "Left_Column_Below_Photo_Avove_Name":                   5,      #照片下方、名字上方的留白
    "Left_Column_Below_Name_Above_Contacts":                5,      #名字下方、联系方式上方的留白
    "Left_Column_Between_Contacs":                          5,      #联系方式之间的留白
    "Left_Column_Below_Contacts_Above_Skills&Awards":       5,      #联系方式下方、技能与获奖上方留白
    "Left_Column_Between_Skills&Awards":                    5,      #技能与获奖之间留白
    "Left_Column_Below_All":                                5,      #左栏下方的留白

    "Right_Column_Above_All":                               10,     #右栏上方的留白
    "Right_Column_Between_SectionTitle_SectionDetails":     3,      #节内标题与详情之间的间距
    "Right_Column_Between_Sections":                        5,      #节间距
    "Right_Column_Between_Details":                         5,      #节内详情间距
    "Right_Column_Below_All":                               5,      #右栏下方的留白
    
    }




# ============================================================================
# 2. Resume 类
# ============================================================================





class Resume:
    """
    简历类
    
    组织一份完整的简历，包含：
        - 目标信息（公司、职位）
        - 个人信息（Profiles）
        - 右栏内容（Section 列表）
        - 个人总结（Summary）
    
    每个实例代表一个版本的简历。
    """
    
    def __init__(
        self,
        intend_company: str = "",
        intend_job: str = "",
        profile: Optional[Profiles] = None,
        skills_awards :Optional[SkillsAwards] = None,
        sections: Optional[List[Section]] = None,
        summary_icon = "",
        summary: str = "",
        summary_height: float = 30.0,
        Lead: dict = {},
    ):
        """
        初始化简历
        
        Args:
            intend_company: 意向公司
            intend_job: 意向职位
            profile: 个人信息
            sections: 右栏章节列表
            summary: 个人总结
            summary_height: 个人总结排版高度（默认30mm）
        """
        self.intend_company = intend_company
        self.intend_job = intend_job
        self.profile = profile or Profiles()
        self.skills_awards = skills_awards or SkillsAwards()
        self.sections = sections or []

        self.summary_icon = summary_icon
        self.summary_title = "个人总结"
        self.summary = summary
        self.summary_height = summary_height
        
        # 内部状态
        self._root: Optional[LayoutObject] = None
        self._pdf_path: Optional[str] = None
        self._left_column: Optional[LayoutObject] = None
        self._right_column: Optional[LayoutObject] = None

        #边距控制
        self.Lead = Lead

        #边距初始化为默认值，跳过显式指定的键值对。
        
        for (key,value) in __Lead_default_settings__.items():
            if not key in self.Lead:
                self.Lead[key] = value
                print(f"\t>>>⚠未指定间距：{key}，将该间距设定为默认值：{value}。")
        
    
    # ------------------------------------------------------------------------
    # 2.1 数据操作方法
    # ------------------------------------------------------------------------
    
    def add_section(self, section: Section) -> 'Resume':
        """添加一个章节（链式调用）"""
        self.sections.append(section)
        return self
    
    def remove_section(self, index: int) -> bool:
        """移除指定索引的章节"""
        if 0 <= index < len(self.sections):
            self.sections.pop(index)
            return True
        return False
    
    def get_file_name(self) -> str:
        """
        获取简历文件名（不含路径）
        
        格式：{姓名}_{意向职位}_{意向公司}.pdf
        
        Returns:
            str: 完整文件名
        """
        name = self.profile.name if self.profile.name else "未命名"
        job = self.intend_job if self.intend_job else "未定岗"
        company = self.intend_company if self.intend_company else "未定公司"
        
        # 清理文件名中的非法字符
        def clean(s: str) -> str:
            illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for ch in illegal_chars:
                s = s.replace(ch, '_')
            return s.strip()
        
        return f"{clean(name)}_{clean(job)}_{clean(company)}.pdf"
    
    # ------------------------------------------------------------------------
    # 2.2 生成 PDF 方法
    # ------------------------------------------------------------------------
    
    def Generate(self, debug: int = 0, output_dir: str = "./output") -> str:
        """
        生成简历 PDF
        
        Args:
            debug: 是否启用调试模式（显示边框和名称）
            output_dir: 输出目录
        
        Returns:
            str: 生成的 PDF 文件路径
        
        Raises:
            RuntimeError: 如果个人信息为空或缺少必要字段
        """
        # ---- 1. 验证数据 ----
        if self.profile.is_empty():
            raise RuntimeError("个人信息为空，请先填充 Profiles 数据")
        
        # ---- 2. 创建 PDF ----
        pdf = FPDF()
        pdf.add_page()
        
        # ---- 3. 注册字体 ----
        try:
            pdf.add_font("LXGW", "", ".\\Resources\\LXGWWenkai-Regular.ttf")
            pdf.add_font("LXGW", "B", ".\\Resources\\LXGWWenkai-Bold.ttf")
        except:
            try:
                pdf.add_font("LXGW", "", ".\\LXGWWenkai-Regular.ttf", subset=False)
                pdf.add_font("LXGW", "B", ".\\LXGWWenkai-Bold.ttf", subset=False)
            except:
                pass  # 使用 helvetica 作为 fallback
        
        # ---- 4. 设置 PDF 元数据 ----
        pdf.set_title(f"简历_{self.profile.name}_{self.intend_job}_{self.intend_company}")
        pdf.set_author(self.profile.name if self.profile.name else "Unknown")
        pdf.set_creator("ResumeCore")
        pdf.set_keywords(f"简历,{self.profile.name},{self.intend_company},{self.intend_job}")
        
        # ---- 5. 创建根布局 ----
        root = LayoutObject(
            name="Root",
            x=0,
            y=0,
            width=210,
            height=297,
            color=White,
            padding=Padding.all(10),
            layer=0,
        )
        self._root = root
        
        # ---- 6. 生成基础模板 ----
        content = generate_basic_subtemplate(
            root=root,
            ratio=[1.0, 2.5],
            left_padding=Padding.all(0),
            right_padding=Padding.left(8),
            layer=0,
        )
        
        # 获取左右栏
        left_column = root.find_by_name("Root_left_column")
        right_column = root.find_by_name("Root_right_column")
        
        if left_column is None or right_column is None:
            raise RuntimeError("无法获取左右栏")
        
        self._left_column = left_column
        self._right_column = right_column
        
        # ---- 7. 填充左栏（个人信息） ----
        self._fill_left_column()
        
        # ---- 8. 填充右栏（章节 + 总结） ----
        self._fill_right_column()
        
        # ---- 9. 渲染 ----
        if debug == 1:
            root.render_debug(pdf, is_fill=True, has_border=True, show_name=True, show_bounds=True)
        elif debug == 0:
            root.render(pdf, is_fill=False)
        else:
            root.render_debug(pdf, is_fill=True, has_border=True, show_name=True, show_bounds=True)
            root.render(pdf, is_fill=False)
        
        # ---- 10. 保存 ----
        os.makedirs(output_dir, exist_ok=True)
        filename = self.get_file_name()
        output_path = os.path.join(output_dir, filename)
        pdf.output(output_path)
        
        self._pdf_path = output_path
        print(f"   >>>✅ PDF 已生成: {output_path}")
        
        return output_path
    
    # ------------------------------------------------------------------------
    # 2.3 内部填充方法
    # ------------------------------------------------------------------------
    
    def _fill_left_column(self) -> None:
        """填充左栏：头像 + 姓名 + 联系方式"""
        profile = self.profile
        root=self._left_column

        #间距留白
        if self.Lead["Left_Column_Above_All"] > 0:
            root.add_child(LayoutObject(
                name="Lead_Left_Column_Above_All",
                x=0,
                y=0,
                width=0,
                height=self.Lead["Left_Column_Above_All"],
                color=White,
                align_x = AlignX.CENTER,
                align_y = AlignY.FLOW,
                padding=Padding.all(0),
                layer=0,
            ))
        
        if profile.photo:
            photo_template = generate_profile_photo_template(
                root,
                index=0,
                layer = 1
            )
            #print(photo_template.name)#Root_left_column_profile_0_content
            root.find_by_name(f"{root.name}_profile_photo_0_photo").set_image(profile.photo)

        #间距留白
        if self.Lead["Left_Column_Below_Photo_Avove_Name"] > 0:
            root.add_child(LayoutObject(
                name="Lead_Left_Column_Below_Photo_Avove_Name",
                x=0,
                y=0,
                width=0,
                height=self.Lead["Left_Column_Below_Photo_Avove_Name"],
                color=White,
                align_x = AlignX.CENTER,
                align_y = AlignY.FLOW,
                padding=Padding.all(0),
                layer=0,
            ))
        
        # ---- 头像 + 姓名 ----
        index = 0
        if profile.name :
            profile_template = generate_profile_template(
                root,
                index,
                text_style = STYLES["name_text"],
                icon_width = 6
            )
            #print(profile_template.name)#Root_left_column_profile_0_content
            root.find_by_name(f"{root.name}_profile_{index}_icon").set_image(".\\Resources\\woman_student.png")
            root.find_by_name(f"{root.name}_profile_{index}_text").set_text(profile.name)
            index += 1

            #间距留白
            if self.Lead["Left_Column_Below_Name_Above_Contacts"] > 0:
                root.add_child(LayoutObject(
                    name="Lead_Left_Column_Below_Name_Above_Contacts",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Left_Column_Below_Name_Above_Contacts"],
                    color=Black,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(0),
                    layer=0,
                ))
        
        # ---- 联系方式 ----
        # 构建联系人列表
        contacts_icon = []
        contacts_text = []
        if profile.telephone:
            #contacts.append(("📞", profile.telephone))
            contacts_icon.append(".\\Resources\\telephone.png")
            contacts_text.append(profile.telephone)
        if profile.email:
            #contacts.append(("✉️", profile.email))
            contacts_icon.append(".\\Resources\\email.png")
            contacts_text.append(profile.email)
        if profile.locate:
            #contacts.append(("📍", profile.locate))
            contacts_icon.append(".\\Resources\\locate.png")
            contacts_text.append(profile.locate)
        if profile.social_media_qq:
            #contacts.append(("💬", f"QQ: {profile.social_media_qq}"))
            contacts_icon.append(".\\Resources\\social_media.png")
            contacts_text.append(f"QQ：{profile.social_media_qq}")
        if profile.social_media_wechat:
            #contacts.append(("💬", f"微信: {profile.social_media_wechat}"))
            contacts_icon.append(".\\Resources\\social_media.png")
            contacts_text.append(f"微信：{profile.social_media_qq}")
        if profile.contact_address:
            #contacts.append(("🏠", profile.contact_address))
            contacts_icon.append(".\\Resources\\contact_address.png")
            contacts_text.append(profile.contact_address)
        if profile.website:
            #contacts.append(("🌐", profile.website))
            contacts_icon.append(".\\Resources\\website.png")
            contacts_text.append(profile.website)
        
        # 添加联系人文本到左栏
        for i in range(len(contacts_text)):
            a = generate_profile_template(
                root,
                index,
                content_height = STYLES["profile_text"].font_size * 0.5
            )
            root.add_child(a)
            root.find_by_name(f"{root.name}_profile_{index}_icon").set_image(contacts_icon[i])
            root.find_by_name(f"{root.name}_profile_{index}_text").set_text(contacts_text[i])
            index += 1

            #不在最后一个联系方式下添加联系方式之间的间距。
            if i == len(contacts_text):
                break
            
            #间距留白
            if self.Lead["Left_Column_Between_Contacs"] > 0:
                root.add_child(LayoutObject(
                    name=f"Lead_Left_Column_Between_Contacs_{i}",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Left_Column_Between_Contacs"],
                    color=Blue,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(10),
                    layer=0,
                ))

                
        if (len(contacts_text)) > 0:
            #间距留白
            if self.Lead["Left_Column_Below_Contacts_Above_Skills&Awards"] > 0:
                root.add_child(LayoutObject(
                    name="Lead_Left_Column_Below_Contacts_Above_Skills&Awards",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Left_Column_Below_Contacts_Above_Skills&Awards"],
                    color=Green,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(0),
                    layer=0,
                ))

                
        # ---- 掌握技能 ----
        if not self.skills_awards.is_empty():
            title_style = STYLES["skillsawards_title"]
            text_style = STYLES["skillsawards_text"]
            #填充获得技能
            if self.skills_awards.skills:
                title_content = LayoutObject(
                    name=f"{root.name}_skills_title_content",
                    x=0,
                    y=0,
                    width=0,
                    height=title_style.font_size * 0.5,
                    color=Green,
                    parent=root,
                    padding=Padding.left(2),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(title_content)
                
                title_content.add_child(TextObject(
                    name=f"{root.name}_skills_title",
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    text=self.skills_awards.skills_title,  # 由用户填充
                    font_name=title_style.font_name,
                    font_size=title_style.font_size,
                    font_style=title_style.get_font_style(),
                    text_color=title_style.color,
                    color=White,
                    parent=title_content,
                    padding=Padding.all(0),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.VCENTER,
                    multi_line=False,
                    layer=1,
                ))

                text_content = LayoutObject(
                    name=f"{root.name}_skills_text_content",
                    x=0,
                    y=0,
                    width=0,
                    height=len(self.skills_awards.skills) *6,
                    color=Red,
                    parent=root,
                    padding=Padding.left(7),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(text_content)

                text_content.add_child(TextObject(
                    name=f"{root.name}_skills_text",
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    text=self.skills_awards.get_char_skills(),  # 由用户填充
                    font_name=text_style.font_name,
                    font_size=text_style.font_size,
                    font_style=text_style.get_font_style(),
                    text_color=text_style.color,
                    color=White,
                    parent=text_content,
                    padding=Padding.left(6),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.VCENTER,
                    multi_line=True,
                    layer=1,
                ))

                #间距留白
                if self.Lead["Left_Column_Between_Skills&Awards"] > 0:
                    root.add_child(LayoutObject(
                        name="Lead_Left_Column_Between_Skills&Awards_1",
                        x=0,
                        y=0,
                        width=0,
                        height=self.Lead["Left_Column_Between_Skills&Awards"],
                        color=Blue,
                        align_x = AlignX.CENTER,
                        align_y = AlignY.FLOW,
                        padding=Padding.all(10),
                        layer=0,
                        ))

        # ---- 获得证书 ----          

            if self.skills_awards.qualifications:
                title_content = LayoutObject(
                    name=f"{root.name}_qualifications_title_content",
                    x=0,
                    y=0,
                    width=0,
                    height=title_style.font_size * 0.5,
                    color=Green,
                    parent=root,
                    padding=Padding.left(2),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(title_content)
                
                title_content.add_child(TextObject(
                    name=f"{root.name}_qualifications_title",
                    x=0,
                    y=0,
                    width=0,
                    height= title_style.font_size * 0.5,
                    text=self.skills_awards.qualifications_title,  
                    font_name=title_style.font_name,
                    font_size=title_style.font_size,
                    font_style=title_style.get_font_style(),
                    text_color=title_style.color,
                    color=White,
                    parent=root,
                    padding=Padding.all(0),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.VCENTER,
                    multi_line=False,
                    layer=1,
                ))

                text_content = LayoutObject(
                    name=f"{root.name}_qualifications_text_content",
                    x=0,
                    y=0,
                    width=0,
                    height=len(self.skills_awards.qualifications) *6,
                    color=Red,
                    parent=root,
                    padding=Padding.left(7),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(text_content)

                text_content.add_child(TextObject(
                    name=f"{root.name}_qualifications_text",
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    text=self.skills_awards.get_char_qualifications(),  # 由用户填充
                    font_name=text_style.font_name,
                    font_size=text_style.font_size,
                    font_style=text_style.get_font_style(),
                    text_color=text_style.color,
                    color=White,
                    parent=text_content,
                    padding=Padding.left(6),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.VCENTER,
                    multi_line=True,
                    layer=1,
                ))

                #间距留白
                if self.Lead["Left_Column_Between_Skills&Awards"] > 0:
                    root.add_child(LayoutObject(
                        name="Lead_Left_Column_Between_Skills&Awards_2",
                        x=0,
                        y=0,
                        width=0,
                        height=self.Lead["Left_Column_Between_Skills&Awards"],
                        color=Blue,
                        align_x = AlignX.CENTER,
                        align_y = AlignY.FLOW,
                        padding=Padding.all(10),
                        layer=0,
                        ))

        # ---- 获得荣誉 ----           
            if self.skills_awards.awards:
                title_content = LayoutObject(
                    name=f"{root.name}_awards_title_content",
                    x=0,
                    y=0,
                    width=0,
                    height=title_style.font_size * 0.5,
                    color=Green,
                    parent=root,
                    padding=Padding.left(2),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(title_content)
                
                title_content.add_child(TextObject(
                    name=f"{root.name}_awards_title",
                    x=0,
                    y=0,
                    width=0,
                    height= title_style.font_size * 0.5,
                    text=self.skills_awards.awards_title,  
                    font_name=title_style.font_name,
                    font_size=title_style.font_size,
                    font_style=title_style.get_font_style(),
                    text_color=title_style.color,
                    color=White,
                    parent=root,
                    padding=Padding.all(0),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.FLOW,
                    multi_line=False,
                    layer=1,
                ))

                text_content = LayoutObject(
                    name=f"{root.name}_awards_text_content",
                    x=0,
                    y=0,
                    width=0,
                    height=len(self.skills_awards.awards) *6,
                    color=Red,
                    parent=root,
                    padding=Padding.left(7),
                    align_x=AlignX.CENTER,
                    align_y=AlignY.FLOW,
                    layer=0,
                )
                root.add_child(text_content)

                text_content.add_child(TextObject(
                    name=f"{root.name}_awards_text",
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    text=self.skills_awards.get_char_awards(),  # 由用户填充
                    font_name=text_style.font_name,
                    font_size=text_style.font_size,
                    font_style=text_style.get_font_style(),
                    text_color=text_style.color,
                    color=White,
                    parent=text_content,
                    padding=Padding.left(6),
                    align_x=AlignX.LEFT,
                    align_y=AlignY.VCENTER,
                    multi_line=True,
                    layer=1,
                ))

        #间距留白
        if self.Lead["Left_Column_Below_All"] > 0:
            root.add_child(LayoutObject(
                name="Lead_Left_Column_Below_All",
                x=0,
                y=0,
                width=0,
                height=self.Lead["Left_Column_Below_All"],
                color=Yellow,
                align_x = AlignX.CENTER,
                align_y = AlignY.FLOW,
                padding=Padding.all(0),
                layer=0,
            ))

            
    
    def _fill_right_column(self) -> None:
        """填充右栏：章节 + 个人总结"""

        root = self._right_column
        section_title_index = 0
        section_details_index = 0
        section_lead_index = 0
        
        #间距留白
        if self.Lead["Right_Column_Above_All"] > 0:
            root.add_child(LayoutObject(
                name="Lead_Right_Column_Above_All",
                x=0,
                y=0,
                width=0,
                height=self.Lead["Right_Column_Above_All"],
                color=White,
                align_x = AlignX.CENTER,
                align_y = AlignY.FLOW,
                padding=Padding.all(0),
                layer=0,
            ))
        
        # ---- 遍历所有章节 ----
        for section in self.sections:
            if not section.details:
                continue
            
            # 生成节标题
            title_template = generate_section_title_template(
                root=self._right_column,
                index=section_title_index,
                icon_style=STYLES["section_title_image"],
                text_style=STYLES["section_title_text"],
                layer=1,
            )
            root.add_child(title_template)
            fill_section_title_data(
                root=self._right_column,
                index=section_title_index,
                title=section.title,
                image_path=section.icon if section.icon else "",
            )
            section_title_index += 1
            
            #间距留白
            if self.Lead["Right_Column_Between_SectionTitle_SectionDetails"] > 0:
                
                
                root.add_child(LayoutObject(
                    name=f"Lead_Right_Column_Between_SectionTitle_SectionDetails_{section_lead_index}",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Right_Column_Between_SectionTitle_SectionDetails"],
                    color=White,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(0),
                    layer=0,
                ))
                section_lead_index += 1
            
            # 生成节详情
            for detail in section.details:
                detail_template = generate_section_details_template(
                    root=self._right_column,
                    index=section_details_index,
                    key_style=STYLES["detail_key_1"],
                    time_style=STYLES["detail_time_1"],
                    tags_style=STYLES["detail_tags_1"],
                    desc_style=STYLES["detail_description"],
                    brief_ratio=[2.0, 1.0, 2.0],
                    brief_height=10,
                    layer=1,
                )
                
                fill_section_details_data(
                    root=self._right_column,
                    index=section_details_index,
                    key=detail.key,
                    during_time=detail.during_time,
                    tags=detail.tags,
                    description=detail.description,
                    description_height=detail.description_height,
                )
                section_details_index += 1

              
                # 不在最后一个detail下添加间距
                if detail == section.details[-1]:
                    break
                
                if self.Lead["Right_Column_Between_Details"] > 0:
                    root.add_child(LayoutObject(
                        name="Lead_Right_Column_Between_Details",
                        x=0,
                        y=0,
                        width=0,
                        height=self.Lead["Right_Column_Between_Details"],
                        color=Blue,
                        align_x = AlignX.CENTER,
                        align_y = AlignY.FLOW,
                        padding=Padding.all(10),
                        layer=0,
                    ))
                
                section_details_index += 1
            
            
            #间距留白
            if self.Lead["Right_Column_Between_Sections"] > 0:
                root.add_child(LayoutObject(
                    name="Lead_Right_Column_Between_Sections",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Right_Column_Between_Sections"],
                    color=Yellow,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(10),
                    layer=0,
                ))
            
        
        # ---- 个人总结 ----
        if self.summary:
            # 创建总结标题
            summary_title = generate_section_title_template(
                root=self._right_column,
                index=section_title_index,
                icon_style=STYLES["section_title_image"],
                text_style=STYLES["section_title_text"],
                layer=1,
            )
            fill_section_title_data(
                root=self._right_column,
                index=section_title_index,
                title=self.summary_title,
                image_path=self.summary_icon,
            )
            section_title_index += 1

            if self.Lead["Right_Column_Between_SectionTitle_SectionDetails"] > 0:
                
                
                root.add_child(LayoutObject(
                    name=f"Lead_Right_Column_Between_SectionTitle_SectionDetails_{section_lead_index}",
                    x=0,
                    y=0,
                    width=0,
                    height=self.Lead["Right_Column_Between_SectionTitle_SectionDetails"],
                    color=White,
                    align_x = AlignX.CENTER,
                    align_y = AlignY.FLOW,
                    padding=Padding.all(0),
                    layer=0,
                ))
                section_lead_index += 1
            
            # 创建总结内容
            summary_detail = generate_summary_template(
                root=self._right_column,
                index=section_details_index,
                desc_style=STYLES["detail_description"],
                layer=1,
            )
            
            fill_summary_data(
                root=self._right_column,
                index=section_details_index,
                description=self.summary,
                description_height=self.summary_height,
            )
        
        #间距留白
        if self.Lead["Right_Column_Below_All"] > 0:
            root.add_child(LayoutObject(
                name="Lead_Right_Column_Below_All",
                x=0,
                y=0,
                width=0,
                height=self.Lead["Right_Column_Below_All"],
                color=White,
                align_x = AlignX.CENTER,
                align_y = AlignY.FLOW,
                padding=Padding.all(10),
                layer=0,
            ))
        
    # ------------------------------------------------------------------------
    # 2.4 访问方法
    # ------------------------------------------------------------------------
    
    def get_pdf_path(self) -> Optional[str]:
        """获取生成的 PDF 路径"""
        return self._pdf_path
    
    def get_root(self) -> Optional[LayoutObject]:
        """获取根布局对象"""
        return self._root
    
    def find(self, name: str) -> Optional[LayoutObject]:
        """按名称查找排版对象"""
        if self._root:
            return self._root.find_by_name(name)
        return None


# ============================================================================
# 3. 测试入口
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("简历核心模块 - 测试")
    print("=" * 60)
    
    # ---- 1. 创建个人信息 ----
    print("\n【1. 创建个人信息】")
    profile = Profiles()
    profile.photo = ".\\Resources\\photo_1.png"
    profile.name = "利姆露"
    profile.telephone = "114-5141-9810"
    profile.locate = "中央都市利姆露"
    profile.email = "1145141919@qq.com"
    profile.social_media_qq = "1145141919810"
    #profile.social_media_wechat = "WeChat_114514"
    #把联络地址写到简历上会有一些问题。具体表现为联络地址会跑到右边页面外。
    #可能是预留空间不够的问题。
    #联络地址是短文本的前提下可以正常显示
    #不过本来也就不推荐简历上写联络地址，也就没关系了
    #profile.contact_address = "中央都市利姆露"
    #profile.contact_address = "中央都市利姆露\n中央大街29号\n鸠拉联邦国务院329办公室"
    profile.website = ""
    profile.title = "史莱姆转生者"
    profile.summary = "从史莱姆转生为魔王，拥有强大的吞噬和模拟能力。"
    
    print(f"  ✅ 个人信息: {profile.name}")
    
    # ---- 2. 创建教育背景章节 ----
    
    print("\n【2. 创建教育背景】")
    
    edu_section = Section()
    edu_section.icon = ".\\Resources\\icon_Education_History.png"
    edu_section.title = "教育背景"
    
    edu_detail_1 = Details(
        key="鸠拉联邦中央大学",
        during_time="2020.09 - 2024.06",
        tags="马克思主义经济学基本原理 | 本科",
        description="主修课程：数据结构、操作系统、计算机网络、数据库原理、软件工程。\n毕业论文：基于深度学习的图像分类算法研究。",
        description_height=12,
    )
    edu_section.add_detail(edu_detail_1)
    
    edu_detail_2 = Details(
        key="利姆露中央高中",
        during_time="2017.09 - 2020.06",
        tags="理科实验班",
        description="高考成绩：全省前 5%，数学 148/150。",
        description_height=6,
    )
    edu_section.add_detail(edu_detail_2)
    
    
    print(f"  ✅ 教育背景: {len(edu_section.details)} 条详情")
    
    # ---- 3. 创建项目经历章节 ----
    print("\n【3. 创建项目经历】")
    
    proj_section = Section()
    proj_section.icon = ".\\Resources\\icon_Project_History.png"
    proj_section.title = "项目经历"
    
    proj_detail_1 = Details(
        key="基于PDF的简历自动生成系统",
        during_time="2025.03 - 2025.06",
        tags="Python, FPDF, 排版引擎",
        description="设计并实现了一套基于 Python 的 PDF 简历自动生成系统。\n系统采用分层排版引擎，支持样式定制、多模板切换、自动分栏等高级功能。",
        description_height=12,
    )
    proj_section.add_detail(proj_detail_1)
    
    proj_detail_2 = Details(
        key="数据可视化看板开发",
        during_time="2024.09 - 2024.12",
        tags="Vue.js, ECharts, Flask",
        description="为某电商公司开发了实时数据监控看板，展示销售、流量、转化等核心指标。\n使用 WebSocket 实现实时数据更新，日活用户 200+。",
        description_height=12,
    )
    proj_section.add_detail(proj_detail_2)
    
    print(f"  ✅ 项目经历: {len(proj_section.details)} 条详情")
    
    # ---- 4. 创建简历 ----
    print("\n【4. 创建简历】")
    
    resume = Resume(
        intend_company="腾讯科技",
        intend_job="后端开发工程师",
        profile=profile,
        sections=[
            edu_section,
            proj_section,
            ],
        summary="5年全栈开发经验，熟悉 Python、Java、Go 等语言。\n"
                "有丰富的 Web 应用和系统架构设计经验.\n"
                "善于解决复杂技术问题。",
        summary_height=18,
    )
    
    print(f"  ✅ 简历: {resume.get_file_name()}")
    
    # ---- 5. 生成 PDF ----
    print("\n【5. 生成 PDF】")
    
    try:
        pdf_path = resume.Generate(
            debug=0,
            output_dir=".\\output",
            )
        print(f"  ✅ 生成成功: {pdf_path}")
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
