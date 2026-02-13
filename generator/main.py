import sys
from pathlib import Path
from generate_svg import generate_base_map, replace_commits_with_symbol, change_text_color, add_commit_animation, make_empty_days_transparent

if len(sys.argv) < 2:
    print("Usage: python generator/main.py <github_username>")
    sys.exit(1)

username = sys.argv[1]

generate_base_map(username)

replace_commits_with_symbol(
    base_svg_path=Path("assets/contributions.svg"),
    symbol_svg_path=Path("assets/footprint.svg"),
    scale_factor=1.0
)

change_text_color(
    svg_path=Path("assets/contributions.svg"),
    new_color="#854442"
)

make_empty_days_transparent(
    Path("assets/contributions.svg")
)

add_commit_animation(
    svg_path=Path("assets/contributions.svg"),
    step_seconds=0.45
)
