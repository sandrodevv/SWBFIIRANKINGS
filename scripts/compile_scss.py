"""Compile frontend/static/scss/main.scss -> frontend/static/css/main.css."""

from pathlib import Path

import sass


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "frontend" / "static"
    scss = root / "scss" / "main.scss"
    css_out = root / "css" / "main.css"
    css_out.parent.mkdir(parents=True, exist_ok=True)
    css = sass.compile(
        filename=str(scss),
        output_style="compressed",
        include_paths=[str(root / "scss")],
    )
    css_out.write_text(css, encoding="utf-8")
    print(f"Wrote {css_out} ({css_out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
