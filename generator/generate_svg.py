import requests
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

EMPTY_COLORS = {
    "#ebedf0",
    "#161b22",
    "#eeeeee",
}

def generate_base_map(username: str):
    """
    Download GitHub contribution graph SVG.
    """
    url = f"https://ghchart.rshah.org/{username}"

    Path("assets").mkdir(exist_ok=True)
    output = Path("assets/contributions.svg")

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    svg = r.text.strip().lstrip("\ufeff")
    output.write_text(svg, encoding="utf-8")

    print("✔ Base SVG generated")


def extract_fill(element):
    fill = element.attrib.get("fill")

    if fill:
        return fill.lower()

    style = element.attrib.get("style")
    if style and "fill:" in style:
        for part in style.split(";"):
            if "fill:" in part:
                return part.split(":")[1].strip().lower()

    return None

def replace_commits_with_symbol(
    base_svg_path: Path,
    symbol_svg_path: Path,
    scale_factor: float = 0.9,
):
    tree = ET.parse(base_svg_path)
    root = tree.getroot()

    s_tree = ET.parse(symbol_svg_path)
    s_root = s_tree.getroot()

    viewbox = s_root.attrib.get("viewBox")
    if not viewbox:
        raise ValueError("Your symbol SVG must have a viewBox")

    _, _, vb_width, vb_height = map(float, viewbox.split())

    symbol_elements = list(s_root)

    rects = root.findall(".//{*}rect")

    commit_rects = []

    for rect in rects:
        fill = extract_fill(rect)
        if fill and fill not in EMPTY_COLORS:
            commit_rects.append(rect)

    print(f"Found {len(commit_rects)} commit squares")

    for rect in commit_rects:
        x = float(rect.attrib.get("x", 0))
        y = float(rect.attrib.get("y", 0))
        size = float(rect.attrib.get("width", 10))

        parent = None
        for p in root.iter():
            if rect in list(p):
                parent = p
                break

        if parent is None:
            continue

        parent.remove(rect)

        scale_x = (size / vb_width) * scale_factor
        scale_y = (size / vb_height) * scale_factor

        g = ET.Element("g")
        g.set("class", "commit-symbol")
        g.set(
            "transform",
            f"translate({x},{y}) scale({scale_x},{scale_y})"
        )

        for e in symbol_elements:
            g.append(ET.fromstring(ET.tostring(e)))

        parent.append(g)

    tree.write(base_svg_path, encoding="utf-8", xml_declaration=True)

    print("✔ Commits replaced successfully")


def change_text_color(svg_path: Path, new_color: str = "#740001"):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    texts = root.findall(".//{*}text")

    print(f"Found {len(texts)} text elements")

    for text in texts:
        style = text.attrib.get("style")
        if style and "fill:" in style:
            parts = []
            for part in style.split(";"):
                if not part.strip().startswith("fill:"):
                    parts.append(part)
            text.set("style", ";".join(parts))

        text.set("fill", new_color)

    tree.write(svg_path, encoding="utf-8", xml_declaration=True)

    print("✔ Text color updated")


def add_commit_animation(svg_path: Path, step_seconds=0.25):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    symbols = root.findall(".//{*}g[@class='commit-symbol']")
    total = len(symbols)

    if total == 0:
        print("No commit symbols found for animation")
        return

    print(f"Animating {total} commits")

    total_duration = step_seconds * total

    style = ET.Element("style", attrib={"type": "text/css"})

    style.text = f"""
    @keyframes reveal {{
      0%   {{ opacity: 0; }}
      5%   {{ opacity: 1; }}
      45%  {{ opacity: 1; }}
      50%  {{ opacity: 0; }}
      100% {{ opacity: 0; }}
    }}

    .commit-symbol {{
      opacity: 0;
      animation-name: reveal;
      animation-duration: {total_duration}s;
      animation-iteration-count: infinite;
      animation-timing-function: linear;
    }}
    """

    root.insert(0, style)

    for i, symbol in enumerate(symbols):
        symbol.set(
            "style",
            f"animation-delay:{i * step_seconds}s;"
        )

    tree.write(svg_path, encoding="utf-8", xml_declaration=True)

    print("✔ Animation added")

def make_empty_days_transparent(svg_path: Path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    rects = root.findall(".//{*}rect")

    changed = 0

    for rect in rects:
        fill = extract_fill(rect)

        if fill and fill in EMPTY_COLORS:
            if "style" in rect.attrib:
                del rect.attrib["style"]

            rect.set("fill", "none")
            changed += 1

    tree.write(svg_path, encoding="utf-8", xml_declaration=True)

    print(f"✔ {changed} empty days set to transparent")
