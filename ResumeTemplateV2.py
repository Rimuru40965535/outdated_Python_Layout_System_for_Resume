"""
================================================================================
简历模板生成器 V2 (Resume Template Generator V2)
================================================================================
功能概述：
    - 基于 LayoutEngine 排版引擎生成简历模板
    - 样式与布局分离，支持灵活定制
    - 左右分栏布局，左栏为容器，右栏为内容区
    - 支持子模板：个人信息、节标题、节详情
    - 支持多行文本、分栏嵌套

依赖：
    - LayoutEngine.py (排版引擎)

================================================================================
"""

from LayoutEngineV2 import (
    LayoutObject,
    TextObject,
    ImageObject,
    RectangleObject,
    objectRegister,
    find_object_by_name,
    AlignX,
    AlignY,
    Padding,
    Color,
    White,
    Black,
    Gray,
    RimuruBlue,
    Red,
    Green,
    Blue,
    Yellow,
    LightGray,
    create_columns,
    layer_manager,
)
import os


# ============================================================================
# 1. 样式类 (Style)
# ============================================================================

class Style:
    """
    样式类 - 纯数据类，用于存储排版样式属性
    
    所有属性均为公有，除构造函数和调试方法外无任何方法。
    样式类不包含位置信息，只包含"长什么样"的属性。
    
    属性列表：
        font_name: 字体名称 (str)
        font_size: 字号 (float)
        bold: 是否粗体 (bool)
        italic: 是否斜体 (bool)
        color: 文字颜色 (Color)
        fill_color: 填充颜色 (Color)
        image_path: 图片路径 (str)
    """
    
    def __init__(
        self,
        font_name: str = "helvetica",
        font_size: float = 12,
        bold: bool = False,
        italic: bool = False,
        color: Color = Black,
        fill_color: Color = White,
        image_path: str = "",
        padding: Padding = Padding.all(0),
        fit_mode = "cover"
    ):
        """
        初始化样式对象
        
        Args:
            font_name: 字体名称
            font_size: 字号 (mm)
            bold: 是否粗体
            italic: 是否斜体
            color: 文字颜色
            fill_color: 填充颜色
            image_path: 图片路径 (仅用于 ImageObject)
        """
        self.font_name = font_name
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.color = color
        self.fill_color = fill_color
        self.image_path = image_path
        self.padding = padding
        self.fit_mode = fit_mode
    
    def get_font_style(self) -> str:
        """
        获取 FPDF 兼容的字体样式字符串
        
        Returns:
            str: "B" 粗体, "I" 斜体, "BI" 粗斜体, "" 常规
        """
        style = ""
        if self.bold:
            style += "B"
        if self.italic:
            style += "I"
        return style
    
    def __repr__(self) -> str:
        return (f"Style(font='{self.font_name}', size={self.font_size}, "
                f"bold={self.bold}, italic={self.italic})")


# ============================================================================
# 2. 预定义样式实例 (STYLES)
# ============================================================================

STYLES = {
    # ---- 左栏样式 ----
    "left_column": Style(
        fill_color=RimuruBlue,
    ),

    # ---- 证件照样式 ----
    "profile_photo":Style(
        fit_mode = "cover",
    ),
    
    # ---- 姓名相关样式 ----
    "name_image": Style(
        image_path="",  # 由用户填充
    ),
    "name_text": Style(
        font_name="LXGW",
        font_size=22,
        bold=True,
        color=Black,
    ),

    "profile_text" : Style(
        font_name="LXGW",
        font_size=12,
        bold=True,
        color=Black,
    ),
    
    # ---- 联系方式样式 ----
    "contact_text": Style(
        font_name="LXGW",
        font_size=10,
        color=Color(60, 60, 60, 0),
    ),

    "skillsawards_title": Style(
        font_name="LXGW",
        font_size=14,
        color=Color(60, 60, 60, 0),
    ),

    "skillsawards_text": Style(
        font_name="LXGW",
        font_size=10,
        color=Color(60, 60, 60, 0),
    ),
    
    
    # ---- 右栏节标题样式 ----
    "section_title_image": Style(
        image_path="",  # 由用户填充
    ),
    "section_title_text": Style(
        font_name="LXGW",
        font_size=22,
        bold=True,
        color=Color(0, 80, 160, 0),
    ),
    
    # ---- 节详情样式组 1 (默认) ----
    "detail_key_1": Style(
        font_name="LXGW",
        font_size=13,
        bold=True,
        color=Black,
    ),
    "detail_time_1": Style(
        font_name="LXGW",
        font_size=7,
        color=Color(100, 100, 100, 0),
        padding = Padding.top(5),
    ),
    "detail_tags_1": Style(
        font_name="LXGW",
        font_size=8,
        color=Color(80, 80, 80, 0),
    ),
    
    # ---- 节详情样式组 2 (备选/紧凑) ----
    "detail_key_2": Style(
        font_name="LXGW",
        font_size=12,
        bold=True,
        color=Color(0, 50, 100, 0),
    ),
    "detail_time_2": Style(
        font_name="LXGW",
        font_size=8,
        color=Color(120, 120, 120, 0),
    ),
    "detail_tags_2": Style(
        font_name="LXGW",
        font_size=8,
        color=Color(100, 100, 100, 0),
    ),
    
    # ---- 节详情描述样式 ----
    #实验值显示，可以尝试在使用这个样式排布的details对象中按排版行数*6留出高度。
    "detail_description": Style(
        font_name="LXGW",
        font_size=10,
        color=Black,
    ),
}


# ============================================================================
# 3. 进阶分栏函数 (split_column_advanced)
# ============================================================================

def split_column_advanced(
    parent: LayoutObject,
    left_obj: LayoutObject,
    right_obj: LayoutObject,
    ratio: list = None,
    gap: float = 0,
    padding: Padding = None,
    layer: int = 0,
) -> LayoutObject:
    """
    进阶分栏函数 - 支持传入已构造好的左右对象
    
    与 create_columns 的区别：
        - 传入的是已构造好的对象，而不是类
        - 支持左右对象不同类型 (LayoutObject / RectangleObject / 任意子类)
        - 左右对象直接挂载到分栏容器下，无需额外包装
    
    Args:
        parent: 父容器 (LayoutObject)
        left_obj: 已构造好的左栏对象
        right_obj: 已构造好的右栏对象
        ratio: 左右比例列表，如 [1.0, 2.5]，默认 [1.0, 2.5]
        gap: 栏间距 (mm)，默认 0
        padding: 分栏容器的内边距，默认 Padding.all(0)
        layer: 图层索引
    
    Returns:
        LayoutObject: 传入的 parent 对象 (支持链式调用)
    
    Example:
        >>> left = RectangleObject(name="Left", color=Blue)
        >>> right = LayoutObject(name="Right")
        >>> split_column_advanced(root, left, right, ratio=[1.0, 2.5])
    """
    if ratio is None:
        ratio = [1.0, 2.5]
    
    if len(ratio) != 2:
        raise ValueError(f"ratio must have exactly 2 elements, got {len(ratio)}")
    
    if padding is None:
        padding = Padding.all(0)
    
    # ---- 获取父容器的内容区域 ----
    _, content_y, content_w, content_h = parent.get_content_area()
    
    if content_w <= 0 or content_h <= 0:
        raise ValueError(f"Parent '{parent.name}' has no available space")
    
    # ---- 计算左右栏宽度 ----
    total_ratio = sum(ratio)
    total_width = content_w - gap
    left_width = total_width * (ratio[0] / total_ratio)
    right_width = total_width * (ratio[1] / total_ratio)
    
    # ---- 创建分栏容器 ----
    container = LayoutObject(
        name=f"{parent.name}_split_container",
        x=0,
        y=0,
        width=content_w,
        height=content_h,
        color=White,
        parent=parent,
        padding=padding,
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    parent.add_child(container)
    
    # ---- 设置左右对象的尺寸和位置 ----
    # 左栏
    left_obj.parent = container
    left_obj._x = 0
    left_obj._y = 0
    left_obj._width = left_width
    left_obj._height = content_h
    left_obj.align_x = AlignX.NONE
    left_obj.align_y = AlignY.NONE
    container.children.append(left_obj)
    
    # 右栏
    right_obj.parent = container
    right_obj._x = left_width + gap
    right_obj._y = 0
    right_obj._width = right_width
    right_obj._height = content_h
    right_obj.align_x = AlignX.NONE
    right_obj.align_y = AlignY.NONE
    container.children.append(right_obj)
    
    # ---- 使缓存失效 ----
    parent.invalidate_wrap_cache()
    
    return parent


# ============================================================================
# 4. 基础模板 (generate_basic_subtemplate)
# ============================================================================

def generate_basic_subtemplate(
    root: LayoutObject,
    ratio: list = None,
    left_padding: Padding = None,
    right_padding: Padding = None,
    layer: int = 0,
) -> LayoutObject:
    """
    生成简历基础模板 - 左右分栏
    
    模板结构：
        root
        └── content:LayoutObject (分栏容器)
            ├── left_column:RectangleObject (左栏，空容器)
            └── right_column:LayoutObject (右栏，空容器)
    
    在同一份简历中此模板只应调用一次。
    左栏后续挂载头像、姓名、联系方式等内容。
    右栏后续挂载节标题、节详情等内容。
    
    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        ratio: 左右分栏比例，默认 [1.0, 2.5]
        left_padding: 左栏内边距，默认 Padding.all(3)
        right_padding: 右栏内边距，默认 Padding.left(5)
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象 (分栏容器)
    """
    if ratio is None:
        ratio = [1.0, 2.5]
    
    if left_padding is None:
        left_padding = Padding.all(0)
    if right_padding is None:
        right_padding = Padding.left(5)
    
    # ---- 创建左右对象 ----
    left_column = RectangleObject(
        name=f"{root.name}_left_column",
        x=0,
        y=0,
        width=0,
        height=0,
        color=STYLES["left_column"].fill_color,
        padding=left_padding,
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    
    right_column = LayoutObject(
        name=f"{root.name}_right_column",
        x=0,
        y=0,
        width=0,
        height=0,
        color=Green,
        padding=right_padding,
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    
    # ---- 分栏 ----
    split_column_advanced(
        parent=root,
        left_obj=left_column,
        right_obj=right_column,
        ratio=ratio,
        gap=0,
        padding=Padding.all(0),
        layer=layer,
    )
    
    # ---- 返回分栏容器 (方便后续查找) ----
    content = root.find_by_name(f"{root.name}_split_container")
    return content


# ============================================================================
# 5. 个人信息模板
# ============================================================================

def generate_profile_template(
    root: LayoutObject,
    index: int,
    icon_style: Style = None,
    text_style: Style = None,
    icon_width: float = 4,
    gap: float = 0,
    layer: int = 0,
    content_height = 20,
) -> LayoutObject:
    """
    生成个人信息子模板 (头像 + 姓名) - 使用左右分栏
    
    模板结构：
        root
        └── {root.name}_profile_content_{index}:LayoutObject
            └── {root.name}_profile_split_{index}:LayoutObject (分栏容器)
                ├── {root.name}_profile_icon_range_{index}:LayoutObject (左栏，宽度固定)
                │   └── {root.name}_profile_icon_{index}:ImageObject
                └── {root.name}_profile_text_range_{index}:LayoutObject (右栏，填满剩余空间)
                    └── {root.name}_profile_text_{index}:TextObject
    
    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        index: 子模板索引，用于区分多个相同类型的子模板
        icon_style: 图标样式，默认使用 STYLES["name_image"]
        text_style: 文本样式，默认使用 STYLES["name_text"]
        icon_width: 左栏宽度 (mm)，默认 10
        gap: 左右栏间距 (mm)，默认 3
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象
    """

    if icon_style is None:
        icon_style = STYLES["name_image"]
    if text_style is None:
        text_style = STYLES["profile_text"]
        
    
    prefix = f"{root.name}_profile_{index}"
    
    # ---- content (挂载到 root) ----
    content = LayoutObject(
        name=f"{prefix}_content",
        x=0,
        y=0,
        width=0,
        height=content_height,
        color=Yellow,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    root.add_child(content)
    
    # ---- 创建左右分栏容器 ----
    # 先获取 content 的内容区域
    content_content = content.get_content_area()
    _, content_y, content_w, content_h = content_content
    
    # 如果 content_w 为 0，说明父容器还没有布局，使用一个合理的默认值
    if content_w <= 0:
        # 尝试从父容器获取宽度
        parent_content = root.get_content_area()
        _, _, parent_w, _ = parent_content
        content_w = parent_w if parent_w > 0 else 150
    
    # 计算左右栏宽度
    left_width = icon_width
    right_width = content_w - left_width - gap
    
    if right_width < 0:
        right_width = 0
        gap = 0
    
    # 创建分栏容器
    split_container = LayoutObject(
        name=f"{prefix}_split",
        x=0,
        y=0,
        width=content_w,
        height=content_h if content_h > 0 else 20,
        #color=Color(245, 245, 250, 0),
        color=Yellow,
        parent=content,
        #padding=Padding.all(0),
        padding = Padding.left(3),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    content.add_child(split_container)
    
    # ---- 左栏: icon_range ----
    icon_range = LayoutObject(
        name=f"{prefix}_icon_range",
        x=0,
        y=0,
        width=icon_width,
        height=0,
        color=Color(240, 248, 255, 0),
        parent=split_container,
        padding=Padding.all(0),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    split_container.add_child(icon_range)
    
    # ---- icon (ImageObject) ----
    icon = ImageObject(
        name=f"{prefix}_icon",
        x=0,
        y=0,
        width=icon_width,
        height=icon_width,
        image_path=icon_style.image_path,
        keep_aspect_ratio=True,
        fit_mode="cover",
        color=White,
        parent=icon_range,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.VCENTER,
        layer=layer + 1,
    )
    icon_range.add_child(icon)
    
    # ---- 右栏: text_range ----
    text_range = LayoutObject(
        name=f"{prefix}_text_range",
        x=left_width + gap,
        y=0,
        width=right_width,
        height=split_container._height,
        color=Color(248, 248, 248, 0),
        parent=split_container,
        padding=Padding.all(0),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    split_container.add_child(text_range)
    
    # ---- text (TextObject) ----
    text = TextObject(
        name=f"{prefix}_text",
        x=0,
        y=0,
        width=0,
        height=0,
        text="",  # 由用户填充
        font_name=text_style.font_name,
        font_size=text_style.font_size,
        font_style=text_style.get_font_style(),
        text_color=text_style.color,
        color=White,
        parent=text_range,
        padding=Padding.all(0),
        align_x=AlignX.LEFT,
        align_y=AlignY.VCENTER,
        multi_line=False,
        layer=layer + 1,
    )
    text_range.add_child(text)
    
    return content

# ============================================================================
# 5. 1 追加照片子模板
# ============================================================================

def generate_profile_photo_template(
    root: LayoutObject,
    index: int,
    icon_style: Style = None,
    photo_width: float = 30,
    layer: int = 0,
) -> LayoutObject:
    """
    生成个人证件照子模板 (头像 + 姓名) - 使用左右分栏
    
    模板结构：
        root
        └── {root.name}_profile_content_{index}:LayoutObject
                └── {root.name}_profile_photo_{index}:ImageObject

    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        index: 子模板索引，用于区分多个相同类型的子模板
        icon_style: 图标样式，默认使用 STYLES["name_image"]
        photo_width: 图片宽度 (mm)，默认 30
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象
    """
    if icon_style is None:
        icon_style = STYLES["profile_photo"]
    
    prefix = f"{root.name}_profile_photo_{index}"

    
    
    # ---- content (挂载到 root) ----
    content = LayoutObject(
        name=f"{prefix}_content",
        x=0,
        y=0,
        width=0,
        height=photo_width,
        color=Yellow,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    root.add_child(content)
    
    # ---- photo (ImageObject) ----
    photo = ImageObject(
        name=f"{prefix}_photo",
        x=0,
        y=0,
        width=photo_width,
        height=0,
        image_path=icon_style.image_path,
        keep_aspect_ratio=True,
        fit_mode=icon_style.fit_mode,
        color=White,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.VCENTER,
        layer=layer + 1,
    )
    content.add_child(photo)

    return content

# ============================================================================
# 6. 节标题模板 (generate_section_title_template) - 分栏版
# ============================================================================

def generate_section_title_template(
    root: LayoutObject,
    index: int,
    icon_style: Style = None,
    text_style: Style = None,
    icon_width: float = 10,
    gap: float = 0,
    layer: int = 0,
) -> LayoutObject:
    """
    生成节标题子模板 (图标 + 标题文字) - 使用左右分栏
    
    模板结构：
        root
        └── {root.name}_section_title_content_{index}:LayoutObject
            └── {root.name}_section_title_split_{index}:LayoutObject (分栏容器)
                ├── {root.name}_section_title_icon_range_{index}:LayoutObject (左栏，宽度固定)
                │   └── {root.name}_section_title_icon_{index}:ImageObject
                └── {root.name}_section_title_text_range_{index}:LayoutObject (右栏，填满剩余空间)
                    └── {root.name}_section_title_text_{index}:TextObject
    
    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        index: 子模板索引
        icon_style: 图标样式，默认使用 STYLES["section_title_image"]
        text_style: 文本样式，默认使用 STYLES["section_title_text"]
        icon_width: 左栏宽度 (mm)，默认 8
        gap: 左右栏间距 (mm)，默认 3
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象
    """
    deviding_line_wide = 0.5
    
    if icon_style is None:
        icon_style = STYLES["section_title_image"]
    if text_style is None:
        text_style = STYLES["section_title_text"]
    
    prefix = f"{root.name}_section_title_{index}"
    
    # ---- content (挂载到 root) ----
    content = LayoutObject(
        name=f"{prefix}_content",
        x=0,
        y=0,
        width=0,
        height=15,
        color=Red,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    root.add_child(content)
    
    # ---- 创建左右分栏容器 ----
    # 获取 content 的内容区域
    content_content = content.get_content_area()
    _, content_y, content_w, content_h = content_content
    
    # 如果 content_w 为 0，使用默认值
    if content_w <= 0:
        parent_content = root.get_content_area()
        _, _, parent_w, _ = parent_content
        content_w = parent_w if parent_w > 0 else 150
    
    # 计算左右栏宽度
    left_width = icon_width
    right_width = content_w - left_width - gap
    
    if right_width < 0:
        right_width = 0
        gap = 0
    
    # 创建分栏容器
    split_container = LayoutObject(
        name=f"{prefix}_split",
        x=0,
        y=0,
        width=content_w,
        height=(content_h if content_h > 0 else 15) - deviding_line_wide,
        color=Color(245, 248, 255, 0),
        parent=content,
        padding=Padding.all(0),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    content.add_child(split_container)
    
    # ---- 左栏: icon_range ----
    icon_range = LayoutObject(
        name=f"{prefix}_icon_range",
        x=0,
        y=0,
        width=left_width,
        height=0,
        color=Color(240, 248, 255, 0),
        parent=split_container,
        padding=Padding.bottom(3),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    split_container.add_child(icon_range)
    
    # ---- icon (ImageObject) ----
    icon = ImageObject(
        name=f"{prefix}_icon",
        x=0,
        y=0,
        width=left_width,
        height=left_width,
        image_path=icon_style.image_path,
        keep_aspect_ratio=True,
        fit_mode="contain",
        color=White,
        parent=icon_range,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.BOTTOM,
        layer=layer + 1,
    )
    icon_range.add_child(icon)
    
    # ---- 右栏: text_range ----
    text_range = LayoutObject(
        name=f"{prefix}_text_range",
        x=left_width + gap,
        y=0,
        width=right_width,
        height=split_container._height,
        color=Color(248, 248, 248, 0),
        parent=split_container,
        padding=Padding.all(0),
        align_x=AlignX.NONE,
        align_y=AlignY.NONE,
        layer=layer,
    )
    split_container.add_child(text_range)
    
    # ---- text (TextObject) ----
    text = TextObject(
        name=f"{prefix}_text",
        x=0,
        y=0,
        width=0,
        height=0,
        text="",  # 由用户填充
        font_name=text_style.font_name,
        font_size=text_style.font_size,
        font_style=text_style.get_font_style(),
        text_color=text_style.color,
        color=White,
        parent=text_range,
        padding=Padding.all(0),
        align_x=AlignX.LEFT,
        align_y=AlignY.BOTTOM,
        multi_line=False,
        layer=layer + 1,
    )
    text_range.add_child(text)

    dividing_line = RectangleObject(
        name=f"{root.name}_dividing_line",
        x=0,
        y=0,
        width=0,
        height=deviding_line_wide,
        color=Black,
        padding=Padding.all(0),
        align_x=AlignX.NONE,
        align_y=AlignY.BOTTOM,
        layer=layer
    )
    content.add_child(dividing_line)
    
    
    return content

# ============================================================================
# 7. 节详情模板 (generate_section_details_template) - 修复版
# ============================================================================

def generate_section_details_template(
    root: LayoutObject,
    index: int,
    key_style: Style = None,
    time_style: Style = None,
    tags_style: Style = None,
    desc_style: Style = None,
    brief_ratio: list = None,
    brief_height: float = 10,
    layer: int = 0,
) -> LayoutObject:
    """
    生成节详情子模板 (关键词 + 时间 + 标签 + 描述)
    
    模板结构：
        root
        └── {root.name}_section_details_content_{index}:LayoutObject
            ├── {root.name}_section_details_brief_{index}:LayoutObject (三栏 2:1:2)
            │   ├── {root.name}_section_details_key_{index}:TextObject
            │   ├── {root.name}_section_details_during_time_{index}:TextObject
            │   └── {root.name}_section_details_tags_{index}:TextObject
            └── {root.name}_section_details_details_{index}:LayoutObject
                └── {root.name}_section_details_description_{index}:TextObject (支持多行)
    
    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        index: 子模板索引
        key_style: 关键词样式，默认 STYLES["detail_key_1"]
        time_style: 时间样式，默认 STYLES["detail_time_1"]
        tags_style: 标签样式，默认 STYLES["detail_tags_1"]
        desc_style: 描述样式，默认 STYLES["detail_description"]
        brief_ratio: brief 三栏比例，默认 [2.0, 1.0, 2.0]
        brief_height: brief 区域固定高度 (mm)，默认 10
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象
    """
    if key_style is None:
        key_style = STYLES["detail_key_1"]
    if time_style is None:
        time_style = STYLES["detail_time_1"]
    if tags_style is None:
        tags_style = STYLES["detail_tags_1"]
    if desc_style is None:
        desc_style = STYLES["detail_description"]
    if brief_ratio is None:
        brief_ratio = [2.0, 1.0, 2.0]
    
    prefix = f"{root.name}_section_details_{index}"
    
    # ---- content ----
    content = LayoutObject(
        name=f"{prefix}_content",
        x=0,
        y=0,
        width=0,
        height=0,
        color=White,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    root.add_child(content)
    
    # ---- brief (固定高度，直接手动布局，不使用 create_columns) ----
    brief = LayoutObject(
        name=f"{prefix}_brief",
        x=0,
        y=0,
        width=0,
        height=brief_height,  # 固定高度
        color=Color(248, 248, 250, 0),
        parent=content,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    content.add_child(brief)
    
    # ---- 手动计算三栏宽度 ----
    # 先获取 brief 的内容区域
    brief_content = brief.get_content_area()
    _, _, brief_w, brief_h = brief_content
    
    # 如果 brief_w 为 0，说明父容器还没有布局，使用一个合理的默认值
    if brief_w <= 0:
        # 尝试从父容器获取宽度
        parent_content = root.get_content_area()
        _, _, parent_w, _ = parent_content
        brief_w = parent_w if parent_w > 0 else 150  #  fallback
    
    total_ratio = sum(brief_ratio)
    gap_total = 0  # 无间距
    total_width = brief_w - gap_total
    
    col_widths = [total_width * (r / total_ratio) for r in brief_ratio]
    
    # ---- 创建三栏 ----
    col_names = ["col_0", "col_1", "col_2"]
    col_objs = []
    cumulative_x = 0
    
    for i in range(3):
        col = LayoutObject(
            name=f"{prefix}_brief_{col_names[i]}",
            x=cumulative_x,
            y=0,
            width=col_widths[i],
            height=brief_h,
            color=White,
            parent=brief,
            padding=Padding.all(0),
            align_x=AlignX.NONE,
            align_y=AlignY.NONE,
            layer=layer,
        )
        brief.add_child(col)
        col_objs.append(col)
        cumulative_x += col_widths[i]

    col_objs[2].padding = Padding.right(1.5)
    
    # ---- key (TextObject) ----
    key = TextObject(
        name=f"{prefix}_key",
        x=0,
        y=0,
        width=0,
        height=0,
        text="",  # 由用户填充
        font_name=key_style.font_name,
        font_size=key_style.font_size,
        font_style=key_style.get_font_style(),
        text_color=key_style.color,
        color=White,
        parent=col_objs[0],
        padding=Padding.all(0),
        align_x=AlignX.LEFT,
        align_y=AlignY.VCENTER,
        multi_line=False,
        layer=layer + 1,
    )
    col_objs[0].add_child(key)
    
    # ---- during_time (TextObject) ----
    during_time = TextObject(
        name=f"{prefix}_during_time",
        x=0,
        y=0,
        width=0,
        height=0,
        text="",  # 由用户填充
        font_name=time_style.font_name,
        font_size=time_style.font_size,
        font_style=time_style.get_font_style(),
        text_color=time_style.color,
        color=White,
        parent=col_objs[1],
        #padding=Padding.all(0),
        padding = time_style.padding,
        align_x=AlignX.CENTER,
        align_y=AlignY.VCENTER,
        multi_line=False,
        layer=layer + 1,
    )
    col_objs[1].add_child(during_time)
    
    # ---- tags (TextObject) ----
    tags = TextObject(
        name=f"{prefix}_tags",
        x=0,
        y=0,
        width=0,
        height=0,
        text="",  # 由用户填充
        font_name=tags_style.font_name,
        font_size=tags_style.font_size,
        font_style=tags_style.get_font_style(),
        text_color=tags_style.color,
        color=White,
        parent=col_objs[2],
        padding=Padding.all(0),
        align_x=AlignX.RIGHT,
        align_y=AlignY.VCENTER,
        multi_line=False,
        layer=layer + 1,
    )
    col_objs[2].add_child(tags)
    
    # ---- details ----
    details = LayoutObject(
        name=f"{prefix}_details",
        x=0,
        y=0,
        width=0,
        height=0,
        color=Color(250, 250, 252, 0),
        parent=content,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    content.add_child(details)
    
    # ---- description (TextObject, 支持多行) ----
    description = TextObject(
        name=f"{prefix}_description",
        x=0,
        y=0,
        width=0,
        height=50,
        text="",  # 由用户填充
        font_name=desc_style.font_name,
        font_size=desc_style.font_size,
        font_style=desc_style.get_font_style(),
        text_color=desc_style.color,
        color=White,
        parent=details,
        padding=Padding.all(2),
        align_x=AlignX.LEFT,
        align_y=AlignY.FLOW,
        multi_line=True,
        line_height=desc_style.font_size * 0.6,
        layer=layer + 1,
    )
    details.add_child(description)
    
    return content

# ============================================================================
# 7.1 追加个人总结模板 (generate_summary_template) - 修复版
# ============================================================================

def generate_summary_template(
    root: LayoutObject,
    index: int,
    desc_style: Style = None,
    layer: int = 0,
) -> LayoutObject:
    """
    生成节详情子模板 (关键词 + 时间 + 标签 + 描述)
    
    模板结构：
        root
        └── {root.name}_section_details_content_{index}:LayoutObject
            └── {root.name}_section_details_details_{index}:LayoutObject
                └── {root.name}_section_details_description_{index}:TextObject (支持多行)
    
    Args:
        root: 挂载子模板的父节点 (LayoutObject)
        index: 子模板索引
        desc_style: 描述样式，默认 STYLES["detail_description"]
        layer: 图层索引
    
    Returns:
        LayoutObject: content 对象
    """
    if desc_style is None:
        desc_style = STYLES["detail_description"]
    
    prefix = f"{root.name}_section_details_{index}"
    
    # ---- content ----
    content = LayoutObject(
        name=f"{prefix}_content",
        x=0,
        y=0,
        width=0,
        height=0,
        color=White,
        parent=root,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    root.add_child(content)
    
    # ---- details ----
    details = LayoutObject(
        name=f"{prefix}_details",
        x=0,
        y=0,
        width=0,
        height=0,
        color=Color(250, 250, 252, 0),
        parent=content,
        padding=Padding.all(0),
        align_x=AlignX.CENTER,
        align_y=AlignY.FLOW,
        layer=layer,
    )
    content.add_child(details)
    
    # ---- description (TextObject, 支持多行) ----
    description = TextObject(
        name=f"{prefix}_description",
        x=0,
        y=0,
        width=0,
        height=50,
        text="",  # 由用户填充
        font_name=desc_style.font_name,
        font_size=desc_style.font_size,
        font_style=desc_style.get_font_style(),
        text_color=desc_style.color,
        color=White,
        parent=details,
        padding=Padding.all(2),
        align_x=AlignX.LEFT,
        align_y=AlignY.FLOW,
        multi_line=True,
        line_height=desc_style.font_size * 0.6,
        layer=layer + 1,
    )
    details.add_child(description)
    
    return content




# ============================================================================
# 8. 辅助函数：快速填充数据
# ============================================================================

def fill_profile_data(root: LayoutObject, index: int, name: str, image_path: str = ""):
    """
    快速填充个人信息数据
    
    Args:
        root: 根布局对象
        index: 个人信息模板索引
        name: 姓名
        image_path: 头像路径
    """
    prefix = f"{root.name}_profile_{index}"
    
    icon = root.find_by_name(f"{prefix}_icon")
    if icon and image_path:
        icon.set_image(image_path)
    
    text = root.find_by_name(f"{prefix}_text")
    if text:
        text.set_text(name)


def fill_section_title_data(root: LayoutObject, index: int, title: str, image_path: str = ""):
    """
    快速填充节标题数据
    
    Args:
        root: 根布局对象
        index: 节标题模板索引
        title: 标题文字
        image_path: 图标路径
    """
    prefix = f"{root.name}_section_title_{index}"

    
    
    icon = root.find_by_name(f"{prefix}_icon")
    if icon and image_path:

        #icon_height = FPDF().image_info(image_path)['h']
        #icon_width = FPDF().image_info(image_path)['w']
        

        icon.set_image(image_path)

    text = root.find_by_name(f"{prefix}_text")
    if text:
        text.set_text(title)


def fill_section_details_data(
    root: LayoutObject,
    index: int,
    key: str,
    during_time: str,
    tags: str,
    description: str,
    brief_height = 10,
    description_height: float = 50,
    #description_resize_to_fit_rext : bool = False,
):
    """
    快速填充节详情数据
    
    Args:
        root: 根布局对象
        index: 节详情模板索引
        key: 关键词/标题
        during_time: 起讫时间
        tags: 标签 (用逗号或空格分隔)
        description: 详细描述 (支持多行)
        description_height：重设文本块高度，以支持流式排版压缩空间。
    """
    prefix = f"{root.name}_section_details_{index}"
    
    content_obj = root.find_by_name(f"{prefix}_content")
    if content_obj:
        content_obj._height = description_height + brief_height
        
    key_obj = root.find_by_name(f"{prefix}_key")
    if key_obj:
        key_obj.set_text(key)
    
    time_obj = root.find_by_name(f"{prefix}_during_time")
    if time_obj:
        time_obj.set_text(during_time)
    
    tags_obj = root.find_by_name(f"{prefix}_tags")
    if tags_obj:
        tags_obj.set_text(tags)
        
    
    desc_obj = root.find_by_name(f"{prefix}_description")
    if desc_obj:
        desc_obj.set_text(description)
        desc_obj._height = description_height

def fill_summary_data(
    root: LayoutObject,
    index: int,
    description: str,
    description_height: float = 50,
    #description_resize_to_fit_rext : bool = False,
):
    """
    快速填充节详情数据
    
    Args:
        root: 根布局对象
        index: 节详情模板索引
        key: 关键词/标题
        during_time: 起讫时间
        tags: 标签 (用逗号或空格分隔)
        description: 详细描述 (支持多行)
        description_height：重设文本块高度，以支持流式排版压缩空间。
    """
    prefix = f"{root.name}_section_details_{index}"
    
    content_obj = root.find_by_name(f"{prefix}_content")
    if content_obj:
        content_obj._height = description_height 
    
    desc_obj = root.find_by_name(f"{prefix}_description")
    if desc_obj:
        desc_obj.set_text(description)
        desc_obj._height = description_height
        

# ============================================================================
# 9. 测试入口 (主函数)
# ============================================================================

if __name__ == "__main__":
    from fpdf import FPDF
    
    print("=" * 60)
    print("简历模板生成器 V2 - 综合测试")
    print("=" * 60)
    
    # ---- 1. 创建 PDF ----
    pdf = FPDF()
    pdf.add_page()
    
    # ---- 2. 注册中文字体 ----
    try:
        pdf.add_font("LXGW", "", ".\\Resources\\LXGWWenkai-Regular.ttf", subset = False)
        pdf.add_font("LXGW", "B", ".\\Resources\\LXGWWenkai-Bold.ttf", subset = False)
        print("✅ 已加载霞鹜文楷字体")
        font_available = True
    except Exception as e:
        print(f"⚠️ 加载字体失败: {e}")
        print("   将使用 Helvetica 字体")
        font_available = False
    
    # ---- 3. 创建根布局 ----
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
    
    # ---- 4. 生成基础模板 (左右分栏) ----
    print("\n【4. 生成基础模板】")
    content = generate_basic_subtemplate(
        root=root,
        ratio=[1.0, 2.5],
        left_padding=None,
        right_padding=Padding.left(8),
        layer=0,
    )
    print(f"  ✅ 基础模板生成完成: {content.name}")
    
    # 获取左右栏引用 (方便后续挂载)
    left_column = root.find_by_name("Root_left_column")
    right_column = root.find_by_name("Root_right_column")
    
    if left_column is None or right_column is None:
        raise RuntimeError("无法获取左右栏")
    
    print(f"  ✅ 左栏: {left_column.name}, 右栏: {right_column.name}")
    
    # ---- 5. 在左栏挂载个人信息 ----
    print("\n【5. 生成个人信息模板】")
    
    # 5.1 头像 + 姓名
    profile = generate_profile_template(
        root=left_column,
        index=0,
        icon_style=STYLES["name_image"],
        text_style=STYLES["name_text"],
        layer=1,
    )
    print(f"  ✅ 个人信息模板生成完成: {profile.name}")
    
    # 填充数据
    fill_profile_data(
        root=left_column,
        index=0,
        name="韩 梅 梅",
        image_path=".\\Resources\\icon.png",  # 无图片，使用占位
    )
    print(f"  ✅ 个人信息数据填充完成")
    
    # ---- 6. 在右栏挂载节标题和节详情 ----
    print("\n【6. 生成右栏内容】")
    
    # 6.1 教育背景标题
    edu_title = generate_section_title_template(
        root=right_column,
        index=0,
        icon_style=STYLES["section_title_image"],
        text_style=STYLES["section_title_text"],
        layer=1,
    )
    fill_section_title_data(
        root=right_column,
        index=0,
        title="教育背景",
        image_path=".\\Resources\\icon_Education_History.png",
    )
    print(f"  ✅ 教育背景标题生成完成")
    
    # 6.2 教育经历 1
    
    edu_detail_1 = generate_section_details_template(
        root=right_column,
        index=0,
        key_style=STYLES["detail_key_1"],
        time_style=STYLES["detail_time_1"],
        tags_style=STYLES["detail_tags_1"],
        desc_style=STYLES["detail_description"],
        brief_ratio=[2.0, 1.0, 2.0],
        layer=1,
    )
    
    fill_section_details_data(
        root=right_column,
        index=0,
        key="日本农业苞谷大学",
        during_time="2020.09 - 2024.06",
        tags="金坷垃制造与苞米发酵工程 | 本科",
        description="主修课程：数据结构与算法、操作系统、计算机网络、数据库原理、软件工程。\n毕业论文：基于深度学习的图像分类算法研究。",
        description_height = 12,
    )
    
    print(f"  ✅ 教育经历 1 生成完成")
    
    # 6.3 教育经历 2 (使用样式组2)
    edu_detail_2 = generate_section_details_template(
        root=right_column,
        index=1,
        key_style=STYLES["detail_key_1"],
        time_style=STYLES["detail_time_1"],
        tags_style=STYLES["detail_tags_1"],
        desc_style=STYLES["detail_description"],
        brief_ratio=[2.0, 1.0, 2.0],
        layer=1,
    )
    fill_section_details_data(
        root=right_column,
        index=1,
        key="XX高中",
        during_time="2017.09 - 2020.06",
        tags="理科实验班",
        description="高考成绩：全省前 5%，数学 148/150。",
        description_height = 6,
    )
    print(f"  ✅ 教育经历 2 (样式组2) 生成完成")
    
    # 6.4 项目经历标题
    proj_title = generate_section_title_template(
        root=right_column,
        index=1,
        icon_style=STYLES["section_title_image"],
        text_style=STYLES["section_title_text"],
        layer=1,
    )
    fill_section_title_data(
        root=right_column,
        index=1,
        title="项目经历",
        image_path=".\\Resources\\icon_Project_History.png",
    )
    print(f"  ✅ 项目经历标题生成完成")
    
    # 6.5 项目经历 1
    proj_detail_1 = generate_section_details_template(
        root=right_column,
        index=2,
        key_style=STYLES["detail_key_1"],
        time_style=STYLES["detail_time_1"],
        tags_style=STYLES["detail_tags_1"],
        desc_style=STYLES["detail_description"],
        brief_ratio=[2.0, 1.0, 2.0],
        layer=1,
    )
    fill_section_details_data(
        root=right_column,
        index=2,
        key="基于PDF的简历自动生成系统",
        during_time="2025.03 - 2025.06",
        tags="Python, FPDF, 排版引擎",
        description="设计并实现了一套基于 Python 的 PDF 简历自动生成系统。\n系统采用分层排版引擎，支持样式定制、多模板切换、自动分栏等高级功能。\n实现了简历元件的模块化管理，支持快速生成针对不同岗位的定制化简历。",
        description_height = 18,
    )
    print(f"  ✅ 项目经历 1 生成完成")
    
    # 6.6 项目经历 2
    proj_detail_2 = generate_section_details_template(
        root=right_column,
        index=3,
        key_style=STYLES["detail_key_1"],
        time_style=STYLES["detail_time_1"],
        tags_style=STYLES["detail_tags_1"],
        desc_style=STYLES["detail_description"],
        brief_ratio=[2.0, 1.0, 2.0],
        layer=1,
    )
    fill_section_details_data(
        root=right_column,
        index=3,
        key="数据可视化看板开发",
        during_time="2024.09 - 2024.12",
        tags="Vue.js, ECharts, Flask",
        description="为某电商公司开发了实时数据监控看板，展示销售、流量、转化等核心指标。\n使用 WebSocket 实现实时数据更新，日活用户 200+。",
        description_height = 12,
    )
    print(f"  ✅ 项目经历 2 (样式组2) 生成完成")
    
    # ---- 7. 调试渲染 ----
    print("\n【7. 渲染 PDF】")
    #root.render_debug(pdf, is_fill=True, has_border=True, show_name=True, show_bounds=True)
    root.render(pdf, is_fill=False)
    
    # ---- 8. 保存 ----
    output_path = "resume_template_v2_test.pdf"
    pdf.output(output_path)
    print(f"\n✅ PDF 已生成: {output_path}")
    
    # ---- 9. 打印图层信息 ----
    layer_manager.print_layer_info()
    
    # ---- 10. 打印布局信息 (仅显示关键对象) ----
    print("\n📐 关键布局信息:")
    print("-" * 60)
    key_names = [
        "Root_left_column",
        "Root_right_column",
        "Root_left_column_profile_0_content",
        "Root_right_column_section_title_0_content",
        "Root_section_title_1_content",
        "Root_section_details_0_content",
        "Root_section_details_1_content",
        "Root_section_details_2_content",
        "Root_section_details_3_content",
        "Root_right_column_section_details_0_key",
        "Root_right_column_section_details_1_key"
    ]
    for name in key_names:
        obj = root.find_by_name(name)
        if obj:
            info = obj.get_layout_info()
            eff = info["effective"]
            print(f"  {name}: ({eff['x']:.1f}, {eff['y']:.1f}) {eff['w']:.1f}x{eff['h']:.1f}")
        else:
            print(f"  {name}: 未找到")
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print(f"✅测试完成！测试PDF存储路径: {output_path}")
    print("=" * 60)

    
