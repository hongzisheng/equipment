import copy
import html
import json
import re
import sqlite3
import warnings
from pathlib import Path

from bs4 import BeautifulSoup


def get_db_path():
    """获取数据库路径"""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    return base_dir / 'database' / 'db.sqlite3'

warnings.filterwarnings('ignore')

# ===================== 配置项 =====================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'assets' / 'extraction'
MD_FILE = OUTPUT_DIR / '第一册_完整合并版.md'
OUT_NODE = OUTPUT_DIR / 'graph_nodes.json'
OUT_REL = OUTPUT_DIR / 'graph_relations.json'
OUT_README = OUTPUT_DIR / '定额目录.md'
RESOURCE_CACHE_FILE = OUTPUT_DIR / 'resource_type_cache.json'
QUOTA_PAT = re.compile(r'^\s*J\d+[-—]\d+\s*$', re.IGNORECASE)

# 表头黑名单（绝对不会是资源名称的内容）
HEADER_BLACKLIST = {
    "定额编号", "项目", "基价", "基价(元)", "人工费", "人工费(元)",
    "材料费", "材料费(元)", "机械费", "机械费(元)", "其中",
    "名称", "单位", "单价", "单价(元)", "数量", "合计", "小计"
}

# ===================== 全局变量 =====================
unrecognized_resources = set()
resource_cache = {}
learned_resource_types = {}


# ===================== 移除标题编号前缀（册/章/节） =====================
def remove_title_prefix(title):
    """移除"第X册"、"第X章"、"第X节"等编号前缀，只保留纯名称"""
    title = re.sub(r'^第[一二三四五六七八九十廿卅\d]+册\s*', '', title)
    title = re.sub(r'^第[一二三四五六七八九十廿卅\d]+章\s*', '', title)
    title = re.sub(r'^第[一二三四五六七八九十廿卅\d]+节\s*', '', title)
    return title.strip()


# ===================== 移除工序序号前缀 =====================
def remove_process_number_prefix(title):
    """移除工序名称前面的各种序号前缀（一、二、1、2、(1)、①等）"""
    patterns = [
        r'^[一二三四五六七八九十百千]+[.、)]\s*',
        r'^\d+[.、)]\s*',
        r'^\([一二三四五六七八九十百千]+\)\s*',
        r'^\(\d+\)\s*',
        r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]+\s*',
        r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.、)]\s*'
    ]

    for pattern in patterns:
        title = re.sub(pattern, '', title)

    return title.strip()


# ===================== 自学习工具函数 =====================
def load_learned_types():
    global learned_resource_types
    try:
        with open(RESOURCE_CACHE_FILE, 'r', encoding='utf-8') as f:
            learned_resource_types = json.load(f)
    except FileNotFoundError:
        learned_resource_types = {}


def save_learned_types():
    with open(RESOURCE_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(learned_resource_types, f, ensure_ascii=False, indent=2)


# ===================== 提取标题编号（用于自动排序） =====================
def get_title_number(name):
    match = re.search(r'第([一二三四五六七八九十廿卅\d]+)[节小节]', name)
    if match:
        num_str = match.group(1)
    else:
        match = re.search(r'^([一二三四五六七八九十廿卅\d]+)[.、)]|^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])', name)
        if match:
            num_str = match.group(1) or match.group(2)
        else:
            return 999

    num_map = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '廿': 20, '卅': 30,
        '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5, '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
        '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15, '⑯': 16, '⑰': 17, '⑱': 18, '⑲': 19, '⑳': 20
    }
    return num_map.get(num_str, int(num_str) if num_str.isdigit() else 999)


# ===================== 生成阅读用目录文件 =====================
def generate_readme_file(hierarchy):
    try:
        with open(OUT_README, 'w', encoding='utf-8') as f:
            f.write(f"# {hierarchy['册名']}\n\n")
            f.write("## 完整目录结构（仅显示有直接工序的内容）\n\n")

            total_chapters = 0
            total_sections = 0
            total_processes = 0

            for chapter_idx, chapter in enumerate(hierarchy['章节'], 1):
                chapter_name = chapter['名称']
                chapter_has_content = False
                chapter_sections = []

                if "节" in chapter:
                    for section in chapter['节']:
                        section_name = section['名称']
                        section_procs = section.get("直接工序", [])

                        if len(section_procs) > 0:
                            chapter_has_content = True
                            total_sections += 1
                            total_processes += len(section_procs)
                            chapter_sections.append((section_name, section_procs))

                chapter_direct_procs = chapter.get("直接工序", [])
                if len(chapter_direct_procs) > 0:
                    chapter_has_content = True
                    total_processes += len(chapter_direct_procs)

                if chapter_has_content:
                    total_chapters += 1
                    f.write(f"## {chapter_idx}. {chapter_name}\n\n")

                    for sec_idx, (sec_name, sec_procs) in enumerate(chapter_sections, 1):
                        f.write(f"### {chapter_idx}.{sec_idx} {sec_name}\n")
                        f.write(f"直接工序：{len(sec_procs)} 个\n\n")
                        for proc_idx, proc in enumerate(sec_procs, 1):
                            proc_name = proc['名称']
                            proc_unit = proc['计量单位']
                            f.write(f"  {proc_idx}. **{proc_name}**")
                            if proc_unit:
                                f.write(f" （计量单位：{proc_unit}）")
                            f.write("\n")
                        f.write("\n")

                    if len(chapter_direct_procs) > 0:
                        f.write("### 直接工序\n")
                        f.write(f"共 {len(chapter_direct_procs)} 个\n\n")
                        for proc_idx, proc in enumerate(chapter_direct_procs, 1):
                            proc_name = proc['名称']
                            proc_unit = proc['计量单位']
                            f.write(f"  {proc_idx}. **{proc_name}**")
                            if proc_unit:
                                f.write(f" （计量单位：{proc_unit}）")
                            f.write("\n")
                        f.write("\n")

            f.write("---\n\n")
            f.write("## 统计信息\n\n")
            f.write(f"- 有效章节数：{total_chapters} 个\n")
            f.write(f"- 有效节数：{total_sections} 个（含共享节）\n")
            f.write(f"- 总工序引用数：{total_processes} 次\n")
            f.write(f"- 生成时间：{str(__import__('datetime').datetime.now()).split('.')[0]}\n")

        print(f"阅读目录已生成：{OUT_README}")
    except Exception as e:
        print(f"生成阅读目录失败：{str(e)}")


# ===================== 基础工具函数 =====================
def expand_table(soup):
    rows = soup.find_all('tr')
    if not rows:
        return []

    cell_matrix = []
    for row in rows:
        cell_row = []
        for cell in row.find_all(['td', 'th']):
            cell_row.append({
                'text': clean_text(cell.get_text()),
                'colspan': int(cell.get('colspan', 1)),
                'rowspan': int(cell.get('rowspan', 1))
            })
        cell_matrix.append(cell_row)

    max_cols = 0
    for r in cell_matrix:
        try:
            s = sum(c['colspan'] for c in r)
            if s > max_cols:
                max_cols = s
        except Exception:
            continue
    if max_cols == 0:
        max_cols = 20

    total_rows = len(cell_matrix)
    fill = [[None] * max_cols for _ in range(total_rows)]
    occupy = [[False] * max_cols for _ in range(total_rows)]

    for r in range(total_rows):
        col = 0
        for cell in cell_matrix[r]:
            while col < max_cols and occupy[r][col]:
                col += 1
            if col >= max_cols:
                break
            try:
                text = cell['text']
                cs = cell['colspan']
                rs = cell['rowspan']
            except Exception:
                col += 1
                continue

            er = min(r + rs, total_rows)
            ec = min(col + cs, max_cols)
            for i in range(r, er):
                for j in range(col, ec):
                    fill[i][j] = text
                    occupy[i][j] = True
            col += cs
    return [row for row in fill if any(cell is not None for cell in row)]


def clean_text(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r'<eq>|</eq>', '', s)
    s = re.sub(r'[\u3000\xa0\x0b\x0c\r\n\t]', ' ', s)
    s = re.sub(r'\*\*', '', s)
    s = re.sub(r'\|', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'[.…]+\(\d+\)$', '', s)
    s = re.sub(r'\(\d+\)$', '', s)
    s = re.sub(r'中国石化|SINOPEC|Slooee|中石化|国石化', '', s).strip()
    s = s.strip('.,;:，。；：')
    return s


def sanitize_id(s):
    s = clean_text(s)
    s = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')


# ===================== 生成唯一工序ID =====================
def get_unique_process_id(title):
    return f"工序_{sanitize_id(title)}"


# ===================== 纯结构工序验证 =====================
def is_valid_process_title(title, sec_content):
    if len(title) < 2 or len(title) > 60:
        return False

    forbidden_keywords = [
        "工作内容", "计量单位", "定额编号", "基价", "人工费", "材料费", "机械费",
        "名称", "单位", "单价", "数量", "说明", "适用范围", "注意事项", "编制依据",
        "计算规则", "工程量", "备注", "附注", "附录", "附表", "附图"
    ]
    for kw in forbidden_keywords:
        if kw in title:
            return False

    has_work_content = re.search(r'工作内容[:：]', sec_content, re.I)
    has_unit = re.search(r'计量单位[:：]', sec_content, re.I)
    has_table = re.search(r'<table>|J\d+[-—]\d+', sec_content, re.I)

    return has_work_content and has_unit and has_table


# ===================== 章节过滤与重命名逻辑 =====================
def merge_duplicate_chapters(hierarchy):
    # 第一步：拆分包含"、"的复合检修章节
    new_chapters = []
    for chapter in hierarchy["章节"]:
        chapter_name = chapter["名称"]

        if "、" in chapter_name and "检修" in chapter_name:
            core_name = chapter_name
            parts = [p.strip() for p in core_name.split('、')]

            # 识别通用节（填料/催化剂）
            common_sections = []
            exclusive_sections = []
            for section in chapter["节"]:
                section_name = section["名称"]
                if "填料" in section_name or "催化剂" in section_name:
                    common_sections.append(copy.deepcopy(section))
                else:
                    exclusive_sections.append(section)

            # 为每个部分创建独立章节
            for part in parts:
                if part.endswith("检修"):
                    new_chapter_name = part
                else:
                    new_chapter_name = f"{part}检修"

                new_chapter = {
                    "名称": new_chapter_name,
                    "直接工序": chapter.get("直接工序", []),
                    "节": []
                }

                # 添加专属节
                part_key = part.replace("检修", "").strip()
                for section in exclusive_sections:
                    section_name = section["名称"]
                    if part_key and part_key in section_name:
                        new_section = copy.deepcopy(section)
                        new_chapter["节"].append(new_section)

                # 添加共享通用节
                new_chapter["节"].extend(common_sections)

                new_chapters.append(new_chapter)
        else:
            new_chapters.append(chapter)

    hierarchy["章节"] = new_chapters

    # 第二步：合并重复章节
    unique_chapters = {}
    merged_hierarchy = {"册名": hierarchy["册名"], "章节": []}

    for chapter in hierarchy["章节"]:
        chapter_name = chapter["名称"]
        if chapter_name in unique_chapters:
            existing = unique_chapters[chapter_name]

            if "节" in chapter:
                if "节" not in existing:
                    existing["节"] = []
                existing_section_map = {s["名称"]: s for s in existing["节"]}
                for section in chapter["节"]:
                    if section["名称"] in existing_section_map:
                        existing_section = existing_section_map[section["名称"]]
                        existing_section["直接工序"] = existing_section.get("直接工序", []) + section.get("直接工序", [])
                    else:
                        existing["节"].append(section)

            existing["直接工序"] = existing.get("直接工序", []) + chapter.get("直接工序", [])
        else:
            unique_chapters[chapter_name] = chapter

    # 第三步：排序
    sorted_chapters = sorted(unique_chapters.values(), key=lambda x: get_title_number(x["名称"]))

    for ch in sorted_chapters:
        if "节" in ch:
            ch["节"].sort(key=lambda x: get_title_number(x["名称"]))

    # 第四步：过滤空内容
    filtered_chapters = []
    for ch in sorted_chapters:
        if "节" in ch:
            filtered_sections = []
            for s in ch["节"]:
                if len(s.get("直接工序", [])) > 0:
                    filtered_sections.append(s)
            ch["节"] = filtered_sections

        has_content = (
            len(ch.get("节", [])) > 0 or
            len(ch.get("直接工序", [])) > 0
        )
        if has_content:
            filtered_chapters.append(ch)

    final_chapters = []
    for ch in filtered_chapters:
        chapter_name = ch["名称"]
        final_chapters.append(ch)

    merged_hierarchy["章节"] = final_chapters
    return merged_hierarchy


# ===================== Markdown 管道表格 → HTML 表格转换 =====================
def convert_md_tables_to_html(content):
    """将 markdown 管道表格（| ... |）转换为 HTML <table>，以便后续统一解析"""
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 检测管道表格起始行（包含 | 分隔符）
        if line.strip().startswith('|') and line.count('|') >= 2:
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            # 跳过纯分隔行（只有 --- 的行）
            data_start = 0
            if len(table_lines) > 1 and all(c in '| -:' for c in table_lines[1].strip()):
                data_start = 1
            data_rows = table_lines[data_start:]
            if data_rows:
                html = '<table>\n'
                for row in data_rows:
                    cells = [c.strip() for c in row.strip().strip('|').split('|')]
                    html += '  <tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>\n'
                html += '</table>'
                result.append(html)
            else:
                for tl in table_lines:
                    result.append(tl)
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)


# ===================== 修复：完整提取跨多行的工作内容和计量单位 =====================
def extract_hierarchy(content):
    # 预处理：将 markdown 管道表格统一转为 HTML 表格
    content = convert_md_tables_to_html(content)

    hierarchy = {"册名": "", "章节": []}

    title_pat = re.compile(
        r'^\s*((?:#+\s+)|'
        r'(?:\d+[.、]\s*)|'
        r'(?:[一二三四五六七八九十百千]+[.、]\s*)|'
        r'(?:\(\d+\)\s*)|'
        r'(?:\([一二三四五六七八九十百千]+\)\s*)|'
        r'(?:[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]+)\s*|'
        r'(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+[.、]\s*)|'
        r'(?:第[一二三四五六七八九十廿卅\d]+[册章节]\s+))'
        r'([^#\n]+?)(?=\n|$)',
        re.M
    )

    matches = list(title_pat.finditer(content))
    current_chapter = None
    current_section = None

    for i in range(len(matches)):
        raw_title = matches[i].group(2).strip()
        full_text = matches[i].group(0).strip()
        title = clean_text(raw_title)
        full_clean = clean_text(full_text)
        # 对册/章/节结构判断优先使用完整匹配文本（含"第X章"前缀），
        # 因为部分标题被 title_pat 剥离了"第X章"前缀
        struct_text = full_clean if re.match(r'^第', full_clean) else title
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sec_content = content[start:end].strip()

        if re.match(r'^第[一二三四五六七八九十廿卅\d]+册', struct_text):
            if not hierarchy["册名"]:  # 只取第一个出现的册名
                hierarchy["册名"] = remove_title_prefix(struct_text)
            current_chapter = None
            current_section = None
            continue

        if re.match(r'^第[一二三四五六七八九十廿卅\d]+章', struct_text):
            current_chapter = {"名称": remove_title_prefix(struct_text), "直接工序": []}
            hierarchy["章节"].append(current_chapter)
            current_section = None
            continue

        if re.match(r'^第[一二三四五六七八九十廿卅\d]+节', struct_text):
            current_section = {"名称": remove_title_prefix(struct_text), "直接工序": []}
            if current_chapter:
                if "节" not in current_chapter:
                    current_chapter["节"] = []
                current_chapter["节"].append(current_section)
            continue

        if is_valid_process_title(title, sec_content):
            if current_section:
                parent = current_section
            elif current_chapter:
                parent = current_chapter
            else:
                current_chapter = {"名称": "静置设备检修工程", "直接工序": []}
                hierarchy["章节"].append(current_chapter)
                parent = current_chapter

            sec_content = re.sub(r'(工作内容[:：].*?)(\n+工作内容[:：])+', r'\1', sec_content, flags=re.S)

            work = ""
            work_match = re.search(r'工作内容[:：]\s*(.*?)(?=计量单位|定额编号|^#|<|$)', sec_content, re.S | re.I)
            if work_match:
                work = clean_text(work_match.group(1))

            unit = ""
            unit_match = re.search(r'计量单位[:：]\s*(.*?)(?=工作内容|定额编号|^#|<|$)', sec_content, re.S | re.I)
            if unit_match:
                unit_raw = unit_match.group(1)
                unit = clean_text(re.sub(r'<.*', '', unit_raw))

            table_pat = re.compile(r'<table[^>]*>.*?</table>', re.S | re.I)
            tables = table_pat.findall(sec_content)

            clean_process_title = remove_process_number_prefix(title)

            proc = {
                "名称": clean_process_title,
                "工作内容": work,
                "计量单位": unit,
                "tables": tables
            }
            parent["直接工序"].append(proc)

    merged_hierarchy = merge_duplicate_chapters(hierarchy)
    return merged_hierarchy


# ===================== 资源类型识别 =====================
def get_resource_type(table_group):
    if table_group in ["人工", "材料", "机械"]:
        return table_group
    return None


def create_resource_node(res_name, res_unit, res_price, res_type):
    res_key = f"资源_{res_type}_{sanitize_id(res_name)}"
    if res_key not in resource_cache:
        price_clean = ""
        if res_price and res_price != "-" and res_price != "SINOPEC":
            price_clean = re.sub(r'[^\d\.]', '', res_price)
            try:
                price_clean = float(price_clean)
            except Exception:
                price_clean = res_price.strip()
        resource_cache[res_key] = {
            "实体类型": "资源", "实体ID": res_key,
            "属性": {"资源名称": res_name, "资源类型": res_type, "单位": res_unit, "单价(元)": price_clean}
        }
    return res_key


# ===================== 表格解析（已修复所有重复问题） =====================
def parse_table(html_text, proc_name="", proc_resources=None):
    if proc_resources is None:
        proc_resources = {"人工": [], "材料": [], "机械": []}

    soup = BeautifulSoup(html_text, 'html.parser')
    data = expand_table(soup)
    if len(data) < 2:
        return [], proc_resources

    quotas = []
    quota_pos = []
    for r, row in enumerate(data):
        for c, cell in enumerate(row):
            if cell and isinstance(cell, str):
                cell_clean = cell.strip()
                if QUOTA_PAT.match(cell_clean):
                    quota_pos.append((r, c, cell_clean))

    if not quota_pos:
        return [], proc_resources

    quota_groups = {}
    for r, c, code in quota_pos:
        if r not in quota_groups:
            quota_groups[r] = []
        quota_groups[r].append((c, code))

    for q_row, q_cols_codes in quota_groups.items():
        seen_codes = set()
        unique_q_cols_codes = []
        for c, code in q_cols_codes:
            if code not in seen_codes:
                seen_codes.add(code)
                unique_q_cols_codes.append((c, code))
        q_cols_codes = unique_q_cols_codes

        q_cols = [x[0] for x in q_cols_codes]
        q_codes = [x[1] for x in q_cols_codes]
        q_count = len(q_cols_codes)

        dim = ""
        dim_vals = []

        main_dim_row = q_row + 1
        sub_dim_row = q_row + 2

        if q_count == 1:
            dim = "项目"
            if main_dim_row < len(data) and q_cols[0] < len(data[main_dim_row]):
                dim_val = str(data[main_dim_row][q_cols[0]]).strip()
                dim_vals = [dim_val]
            else:
                dim_vals = [""]
        else:
            if main_dim_row < len(data) and sub_dim_row < len(data):
                main_dims = []
                for c in q_cols:
                    if c < len(data[main_dim_row]) and data[main_dim_row][c]:
                        main_dims.append(str(data[main_dim_row][c]).strip())
                    else:
                        main_dims.append("")

                sub_dims = []
                for c in q_cols:
                    if c < len(data[sub_dim_row]) and data[sub_dim_row][c]:
                        sub_dims.append(str(data[sub_dim_row][c]).strip())
                    else:
                        sub_dims.append("")

                unique_main_dims = set([d for d in main_dims if d])
                if len(unique_main_dims) > 1:
                    for i in range(q_count):
                        main = main_dims[i]
                        sub = sub_dims[i]
                        if main and sub:
                            dim_vals.append(f"{main} {sub}")
                        elif main:
                            dim_vals.append(main)
                        elif sub:
                            dim_vals.append(sub)
                        else:
                            dim_vals.append("")
                    dim = "项目"
                else:
                    if main_dims[0]:
                        dim = main_dims[0]
                    dim_vals = sub_dims
            elif main_dim_row < len(data):
                if q_cols[0] < len(data[main_dim_row]) and data[main_dim_row][q_cols[0]]:
                    dim = str(data[main_dim_row][q_cols[0]]).strip()
                dim_vals = [""] * q_count

        while len(dim_vals) < q_count:
            dim_vals.append("")

        cost_items = [
            ("基价(元)", [r'基价', r'合计']),
            ("人工费(元)", [r'人工费']),
            ("材料费(元)", [r'材料费']),
            ("机械费(元)", [r'机械费'])
        ]
        cost_data = {k: [None] * q_count for k, _ in cost_items}

        for r in range(q_row + 1, len(data)):
            row = data[r]
            row_text = ' '.join([str(c) for c in row if c])
            if "名称" in row_text and "单位" in row_text and "单价" in row_text:
                break
            if not row_text or row_text.strip() == "其中":
                continue

            matched = None
            for k, pats in cost_items:
                if any(re.search(p, row_text, re.I) for p in pats):
                    matched = k
                    break
            if not matched:
                continue

            for i, c in enumerate(q_cols):
                if c >= len(row) or row[c] is None:
                    continue
                v = str(row[c]).strip()
                if not v or v in ["-", "", "其中", "SINOPEC", "国石化"]:
                    continue
                v_clean = re.sub(r'[^\d\.]', '', v)
                try:
                    cost_data[matched][i] = float(v_clean)
                except Exception:
                    cost_data[matched][i] = v.strip()

        quota_resource_data = {}

        header_row = -1
        for r in range(q_row + 1, len(data)):
            row_text = ' '.join([str(c) for c in data[r] if c])
            if "名称" in row_text and "单位" in row_text and "单价" in row_text:
                header_row = r
                break

        if header_row != -1:
            header = data[header_row]
            col_map = {}
            for idx, cell in enumerate(header):
                if not cell:
                    continue
                cell_lower = cell.strip().lower()
                if "名称" in cell_lower or "项目" in cell_lower:
                    col_map["name"] = idx
                elif "单位" in cell_lower:
                    col_map["unit"] = idx
                elif "单价" in cell_lower or "基价" in cell_lower:
                    col_map["price"] = idx
                elif "数量" in cell_lower or "用量" in cell_lower:
                    if "qty_start" not in col_map:
                        col_map["qty_start"] = idx

            if "name" not in col_map or "unit" not in col_map:
                continue

            if "qty_start" not in col_map:
                col_map["qty_start"] = col_map.get("price", 3) + 1

            current_group = None

            for r in range(header_row + 1, len(data)):
                row = data[r]
                row_text = ' '.join([str(c) for c in data[r] if c])

                first_cell = str(row[0]).strip() if 0 < len(row) and row[0] else ""
                if first_cell in ["人工", "材料", "机械"]:
                    current_group = first_cell

                if not row_text or row_text.strip() in ["小计", "合计"]:
                    continue

                name = str(row[col_map["name"]]).strip() if col_map["name"] < len(row) and row[col_map["name"]] else ""
                unit = str(row[col_map["unit"]]).strip() if col_map["unit"] < len(row) and row[col_map["unit"]] else ""
                price = str(row[col_map["price"]]).strip() if "price" in col_map and col_map["price"] < len(row) and row[col_map["price"]] else ""

                if not name or not current_group or name in HEADER_BLACKLIST:
                    continue

                rt = get_resource_type(current_group)
                if not rt:
                    continue

                if name not in proc_resources[rt]:
                    proc_resources[rt].append(name)

                res_id = create_resource_node(name, unit, price, rt)

                qtys = []
                for i in range(q_count):
                    c = col_map["qty_start"] + i
                    v = str(row[c]).strip() if c < len(row) and row[c] else ""
                    if v == "-":
                        qtys.append("")
                    else:
                        vc = re.sub(r'[^\d\.]', '', v)
                        try:
                            qtys.append(float(vc) if vc else "")
                        except Exception:
                            qtys.append(v)

                while len(qtys) < q_count:
                    qtys.append("")

                for i, code in enumerate(q_codes):
                    qty = qtys[i]
                    if qty in ["", "-", None]:
                        continue
                    if code not in quota_resource_data:
                        quota_resource_data[code] = []
                        quota_resource_data[code + "_seen"] = set()

                    if res_id not in quota_resource_data[code + "_seen"]:
                        quota_resource_data[code].append({
                            "资源ID": res_id, "资源类型": rt, "使用数量": qty
                        })
                        quota_resource_data[code + "_seen"].add(res_id)

        for code in list(quota_resource_data.keys()):
            if code.endswith("_seen"):
                del quota_resource_data[code]

        for i in range(q_count):
            quotas.append({
                "定额编号": q_codes[i],
                "计量维度": dim,
                "计量值": dim_vals[i],
                "基价(元)": cost_data["基价(元)"][i],
                "人工费(元)": cost_data["人工费(元)"][i],
                "材料费(元)": cost_data["材料费(元)"][i],
                "机械费(元)": cost_data["机械费(元)"][i],
                "资源数据": quota_resource_data.get(q_codes[i], [])
            })

    return quotas, proc_resources


# ===================== 实体与关系提取 =====================
def extract_all(hierarchy):
    entities = {
        "册名": {}, "章节": {}, "节": {}, "工序": {},
        "定额编号": {}, "资源": {}, "定额人工明细": {},
        "定额材料明细": {}, "定额机械明细": {}
    }
    relations = []

    processed_sections = set()

    volume_id = f"册名_{sanitize_id(hierarchy['册名'])}"
    entities["册名"][volume_id] = {"名称": hierarchy["册名"]}

    for chapter in hierarchy["章节"]:
        chapter_id = f"章节_{sanitize_id(chapter['名称'])}"
        entities["章节"][chapter_id] = {"名称": chapter["名称"]}
        relations.append({
            "源实体类型": "册名", "源实体ID": volume_id,
            "关系类型": "包含章节",
            "目标实体类型": "章节", "目标实体ID": chapter_id
        })

        if "节" in chapter:
            for section in chapter["节"]:
                section_id = f"节_{sanitize_id(section['名称'])}"

                relations.append({
                    "源实体类型": "章节", "源实体ID": chapter_id,
                    "关系类型": "包含节",
                    "目标实体类型": "节", "目标实体ID": section_id
                })

                if section_id in processed_sections:
                    continue
                processed_sections.add(section_id)

                entities["节"][section_id] = {"名称": section["名称"]}

                for proc in section.get("直接工序", []):
                    proc_id = get_unique_process_id(proc["名称"])

                    all_quotas = []
                    for table in proc["tables"]:
                        try:
                            q, _ = parse_table(table, proc["名称"])
                            all_quotas.extend(q)
                        except Exception as e:
                            print(f"解析表格失败：{proc['名称']} - {str(e)}")
                            continue

                    entities["工序"][proc_id] = {
                        "名称": proc["名称"],
                        "工作内容": proc["工作内容"],
                        "计量单位": proc["计量单位"]
                    }
                    relations.append({
                        "源实体类型": "节", "源实体ID": section_id,
                        "关系类型": "包含工序",
                        "目标实体类型": "工序", "目标实体ID": proc_id
                    })

                    unique_quotas = {}
                    for q in all_quotas:
                        code = q["定额编号"]
                        if code not in unique_quotas:
                            unique_quotas[code] = q
                        else:
                            existing = unique_quotas[code]
                            existing_resources = {d["资源ID"]: d for d in existing["资源数据"]}
                            for d in q["资源数据"]:
                                if d["资源ID"] not in existing_resources:
                                    existing["资源数据"].append(d)

                    for code, q in unique_quotas.items():
                        entities["定额编号"][code] = {k: v for k, v in q.items() if k not in ["定额编号", "资源数据"]}
                        relations.append({
                            "源实体类型": "工序", "源实体ID": proc_id,
                            "关系类型": "包含定额",
                            "目标实体类型": "定额编号", "目标实体ID": code
                        })

                        labor_list = [d for d in q["资源数据"] if d["资源类型"] == "人工"]
                        mat_list = [d for d in q["资源数据"] if d["资源类型"] == "材料"]
                        mach_list = [d for d in q["资源数据"] if d["资源类型"] == "机械"]

                        for d in labor_list:
                            del d["资源类型"]
                        for d in mat_list:
                            del d["资源类型"]
                        for d in mach_list:
                            del d["资源类型"]

                        if labor_list:
                            labor_detail_id = f"明细_{code}_人工"
                            entities["定额人工明细"][labor_detail_id] = {"所属定额": code, "人工明细": labor_list}
                            relations.append({
                                "源实体类型": "定额编号", "源实体ID": code,
                                "关系类型": "包含人工明细",
                                "目标实体类型": "定额人工明细", "目标实体ID": labor_detail_id
                            })
                            for d in labor_list:
                                relations.append({
                                    "源实体类型": "定额人工明细", "源实体ID": labor_detail_id,
                                    "关系类型": "关联资源",
                                    "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                                })

                        if mat_list:
                            mat_detail_id = f"明细_{code}_材料"
                            entities["定额材料明细"][mat_detail_id] = {"所属定额": code, "材料明细": mat_list}
                            relations.append({
                                "源实体类型": "定额编号", "源实体ID": code,
                                "关系类型": "包含材料明细",
                                "目标实体类型": "定额材料明细", "目标实体ID": mat_detail_id
                            })
                            for d in mat_list:
                                relations.append({
                                    "源实体类型": "定额材料明细", "源实体ID": mat_detail_id,
                                    "关系类型": "关联资源",
                                    "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                                })

                        if mach_list:
                            mach_detail_id = f"明细_{code}_机械"
                            entities["定额机械明细"][mach_detail_id] = {"所属定额": code, "机械明细": mach_list}
                            relations.append({
                                "源实体类型": "定额编号", "源实体ID": code,
                                "关系类型": "包含机械明细",
                                "目标实体类型": "定额机械明细", "目标实体ID": mach_detail_id
                            })
                            for d in mach_list:
                                relations.append({
                                    "源实体类型": "定额机械明细", "源实体ID": mach_detail_id,
                                    "关系类型": "关联资源",
                                    "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                                })

        for proc in chapter.get("直接工序", []):
            proc_id = get_unique_process_id(proc["名称"])

            all_quotas = []
            for table in proc["tables"]:
                try:
                    q, _ = parse_table(table, proc["名称"])
                    all_quotas.extend(q)
                except Exception as e:
                    print(f"解析表格失败：{proc['名称']} - {str(e)}")
                    continue

            entities["工序"][proc_id] = {
                "名称": proc["名称"],
                "工作内容": proc["工作内容"],
                "计量单位": proc["计量单位"]
            }
            relations.append({
                "源实体类型": "章节", "源实体ID": chapter_id,
                "关系类型": "包含工序",
                "目标实体类型": "工序", "目标实体ID": proc_id
            })

            unique_quotas = {}
            for q in all_quotas:
                code = q["定额编号"]
                if code not in unique_quotas:
                    unique_quotas[code] = q
                else:
                    existing = unique_quotas[code]
                    existing_resources = {d["资源ID"]: d for d in existing["资源数据"]}
                    for d in q["资源数据"]:
                        if d["资源ID"] not in existing_resources:
                            existing["资源数据"].append(d)

            for code, q in unique_quotas.items():
                entities["定额编号"][code] = {k: v for k, v in q.items() if k not in ["定额编号", "资源数据"]}
                relations.append({
                    "源实体类型": "工序", "源实体ID": proc_id,
                    "关系类型": "包含定额",
                    "目标实体类型": "定额编号", "目标实体ID": code
                })

                labor_list = [d for d in q["资源数据"] if d["资源类型"] == "人工"]
                mat_list = [d for d in q["资源数据"] if d["资源类型"] == "材料"]
                mach_list = [d for d in q["资源数据"] if d["资源类型"] == "机械"]

                for d in labor_list:
                    del d["资源类型"]
                for d in mat_list:
                    del d["资源类型"]
                for d in mach_list:
                    del d["资源类型"]

                if labor_list:
                    labor_detail_id = f"明细_{code}_人工"
                    entities["定额人工明细"][labor_detail_id] = {"所属定额": code, "人工明细": labor_list}
                    relations.append({
                        "源实体类型": "定额编号", "源实体ID": code,
                        "关系类型": "包含人工明细",
                        "目标实体类型": "定额人工明细", "目标实体ID": labor_detail_id
                    })
                    for d in labor_list:
                        relations.append({
                            "源实体类型": "定额人工明细", "源实体ID": labor_detail_id,
                            "关系类型": "关联资源",
                            "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                        })

                if mat_list:
                    mat_detail_id = f"明细_{code}_材料"
                    entities["定额材料明细"][mat_detail_id] = {"所属定额": code, "材料明细": mat_list}
                    relations.append({
                        "源实体类型": "定额编号", "源实体ID": code,
                        "关系类型": "包含材料明细",
                        "目标实体类型": "定额材料明细", "目标实体ID": mat_detail_id
                    })
                    for d in mat_list:
                        relations.append({
                            "源实体类型": "定额材料明细", "源实体ID": mat_detail_id,
                            "关系类型": "关联资源",
                            "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                        })

                if mach_list:
                    mach_detail_id = f"明细_{code}_机械"
                    entities["定额机械明细"][mach_detail_id] = {"所属定额": code, "机械明细": mach_list}
                    relations.append({
                        "源实体类型": "定额编号", "源实体ID": code,
                        "关系类型": "包含机械明细",
                        "目标实体类型": "定额机械明细", "目标实体ID": mach_detail_id
                    })
                    for d in mach_list:
                        relations.append({
                            "源实体类型": "定额机械明细", "源实体ID": mach_detail_id,
                            "关系类型": "关联资源",
                            "目标实体类型": "资源", "目标实体ID": d["资源ID"]
                        })

    for rid, node in resource_cache.items():
        entities["资源"][rid] = node["属性"]

    unique_relations = []
    seen_relations = set()
    for rel in relations:
        rel_key = (rel["源实体ID"], rel["关系类型"], rel["目标实体ID"])
        if rel_key not in seen_relations:
            seen_relations.add(rel_key)
            unique_relations.append(rel)
    relations = unique_relations

    nodes = []
    for etype, edict in entities.items():
        for eid, attrs in edict.items():
            nodes.append({"实体类型": etype, "实体ID": eid, "属性": attrs})
    return nodes, relations


# ===================== 数据库导入函数 =====================
def reset_graph_tables(cursor):
    # 重置本次展示用的表（每次覆盖）
    cursor.execute('DROP TABLE IF EXISTS graph_nodes')
    cursor.execute('''
    CREATE TABLE graph_nodes (
        entity_type TEXT NOT NULL,
        entity_id TEXT PRIMARY KEY,
        attributes JSON NOT NULL
    )
    ''')

    cursor.execute('DROP TABLE IF EXISTS graph_relations')
    cursor.execute('''
    CREATE TABLE graph_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_relation_unique
    ON graph_relations (source_id, relation_type, target_id)
    ''')

    # 新增：累积表（用于保存所有历史数据，仅首次创建，之后不再删除）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS graph_nodes_archive (
        entity_type TEXT NOT NULL,
        entity_id TEXT PRIMARY KEY,
        attributes JSON NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS graph_relations_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_relation_archive_unique
    ON graph_relations_archive (source_id, relation_type, target_id)
    ''')


def import_graph_data(nodes, relations, db_path=None, reset_tables=True):
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        if reset_tables:
            reset_graph_tables(cursor)  # 只重置原表，累积表不受影响

        # 写入本次结果到原表（覆盖）
        node_data = []
        for node in nodes:
            node_data.append((
                node['实体类型'],
                node['实体ID'],
                json.dumps(node['属性'], ensure_ascii=False)
            ))

        cursor.executemany('''
        INSERT INTO graph_nodes (entity_type, entity_id, attributes)
        VALUES (?, ?, ?)
        ''', node_data)

        rel_data = []
        for rel in relations:
            rel_data.append((
                rel['源实体类型'],
                rel['源实体ID'],
                rel['关系类型'],
                rel['目标实体类型'],
                rel['目标实体ID']
            ))

        cursor.executemany('''
        INSERT INTO graph_relations (source_type, source_id, relation_type, target_type, target_id)
        VALUES (?, ?, ?, ?, ?)
        ''', rel_data)

        # 追加写入累积表（使用 INSERT OR IGNORE 自动去重）
        cursor.executemany('''
        INSERT OR IGNORE INTO graph_nodes_archive (entity_type, entity_id, attributes)
        VALUES (?, ?, ?)
        ''', node_data)

        cursor.executemany('''
        INSERT OR IGNORE INTO graph_relations_archive (source_type, source_id, relation_type, target_type, target_id)
        VALUES (?, ?, ?, ?, ?)
        ''', rel_data)

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ===================== 统一入口：Markdown -> 提取 -> 入库 =====================
def extract_and_import_from_markdown(markdown_text, db_path=None, write_files=True, reset_tables=True):
    global resource_cache, learned_resource_types
    resource_cache = {}
    learned_resource_types = {}

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hierarchy = extract_hierarchy(markdown_text)
    if not hierarchy["章节"]:
        raise RuntimeError("未找到有效章节")

    generate_readme_file(hierarchy)

    nodes, relations = extract_all(hierarchy)

    if write_files:
        with open(OUT_NODE, 'w', encoding='utf-8') as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2)
        with open(OUT_REL, 'w', encoding='utf-8') as f:
            json.dump(relations, f, ensure_ascii=False, indent=2)

    save_learned_types()

    import_graph_data(nodes, relations, db_path=db_path, reset_tables=reset_tables)

    return {
        "chapters": len([n for n in nodes if n['实体类型'] == '章节']),
        "sections": len([n for n in nodes if n['实体类型'] == '节']),
        "processes": len([n for n in nodes if n['实体类型'] == '工序']),
        "quotas": len([n for n in nodes if n['实体类型'] == '定额编号']),
        "resources": len([n for n in nodes if n['实体类型'] == '资源']),
        "relations": len(relations)
    }


def query_quotas(db_path=None):
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        print("正在查询定额信息...\n")

        sql = '''
        SELECT
            vol.attributes->>'$.名称' AS 册名,
            chap.attributes->>'$.名称' AS 章节名,
            proc.entity_id AS 工序ID,
            proc.attributes->>'$.名称' AS 所属工序,
            q.entity_id AS 定额编号,
            json_extract(q.attributes, '$.计量维度') AS 计量维度,
            json_extract(q.attributes, '$.计量值') AS 计量值,
            json_extract(q.attributes, '$.基价(元)') AS 基价,
            json_extract(q.attributes, '$.人工费(元)') AS 人工费,
            json_extract(q.attributes, '$.材料费(元)') AS 材料费,
            json_extract(q.attributes, '$.机械费(元)') AS 机械费,
            json_extract(ld.attributes, '$.人工明细[0].使用数量') AS 合计工日
        FROM graph_nodes proc
        LEFT JOIN graph_relations rproc
            ON rproc.target_id = proc.entity_id
            AND rproc.relation_type = '包含工序'
        LEFT JOIN graph_nodes sec
            ON sec.entity_id = rproc.source_id
            AND sec.entity_type = '节'
        LEFT JOIN graph_relations rsec
            ON rsec.target_id = sec.entity_id
            AND rsec.relation_type = '包含节'
        LEFT JOIN graph_nodes chap
            ON chap.entity_id = rsec.source_id
            AND chap.entity_type = '章节'
        LEFT JOIN graph_relations rchap
            ON rchap.target_id = chap.entity_id
            AND rchap.relation_type = '包含章节'
        LEFT JOIN graph_nodes vol
            ON vol.entity_id = rchap.source_id
            AND vol.entity_type = '册名'
        LEFT JOIN graph_relations r1
            ON r1.source_id = proc.entity_id
            AND r1.relation_type = '包含定额'
        LEFT JOIN graph_nodes q
            ON q.entity_id = r1.target_id
            AND q.entity_type = '定额编号'
        LEFT JOIN graph_relations r2
            ON r2.source_id = q.entity_id
            AND r2.relation_type = '包含人工明细'
        LEFT JOIN graph_nodes ld
            ON ld.entity_id = r2.target_id
        WHERE proc.entity_type = '工序'
          AND q.entity_type = '定额编号'
        GROUP BY q.entity_id
        ORDER BY CAST(SUBSTR(q.entity_id, 4) AS INTEGER), proc.entity_id
        '''

        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            print("未查询到任何定额数据")
            return []

        result = []

        def _to_number(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            text = str(value).strip()
            if not text:
                return None
            try:
                cleaned = re.sub(r'[^\d\.]', '', text)
                return float(cleaned) if cleaned else None
            except Exception:
                return text


        for idx, row in enumerate(rows, 1):
            process_id = row[2]
            process_name = row[3] if row[3] is not None else '未关联'
            quota_id = row[4]
            volume_name = row[0] if row[0] is not None else '未关联'
            chapter_name = row[1] if row[1] is not None else '未关联'
            measurement_dimension = row[5] if row[5] is not None else '-'
            measurement_value = row[6] if row[6] is not None else '-'
            base_price = _to_number(row[7])
            labor_price = _to_number(row[8])
            material_price = _to_number(row[9])
            machine_price = _to_number(row[10])
            total_days = _to_number(row[11])

            tool_cost = 0.0
            for cost_value in (material_price, machine_price):
                if isinstance(cost_value, (int, float)):
                    tool_cost += float(cost_value)

            display_base_price = f"{base_price:.2f}" if isinstance(base_price, (int, float)) else '-'
            display_labor_price = f"{labor_price:.2f}" if isinstance(labor_price, (int, float)) else '-'
            display_material_price = f"{material_price:.2f}" if isinstance(material_price, (int, float)) else '-'
            display_machine_price = f"{machine_price:.2f}" if isinstance(machine_price, (int, float)) else '-'
            display_total_days = f"{total_days:.3f}" if isinstance(total_days, (int, float)) else '-'

            display_process_name = process_name[:22] + "..." if len(process_name) > 22 else process_name
            display_volume_name = volume_name[:16] + "..." if len(volume_name) > 16 else volume_name
            display_chapter_name = chapter_name[:16] + "..." if len(chapter_name) > 16 else chapter_name


            result.append({
                "equipmentCategory": volume_name,
                "equipment": chapter_name,
                "processId": process_id,
                "processName": process_name,
                "quotaId": quota_id,
                "measurementDimension": measurement_dimension,
                "measurementValue": measurement_value,
                "basePrice": base_price,
                "laborCost": labor_price,
                "materialCost": material_price,
                "machineCost": machine_price,
                "toolCost": tool_cost if tool_cost else None,
                "manHours": total_days,
            })

        print(f"\n查询完成，共显示 {len(rows)} 条定额信息")
        return result

    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("错误：数据库中不存在所需的表，请先运行导入脚本")
        else:
            print(f"数据库错误：{e}")
        return []
    finally:
        conn.close()


if __name__ == '__main__':
    if MD_FILE.exists():
        with open(MD_FILE, 'r', encoding='utf-8') as f:
            markdown = f.read()
        summary = extract_and_import_from_markdown(markdown)
        print(f"提取完成：{summary}")
    else:
        print(f"未找到输入文件：{MD_FILE}")