"""
DOCX -> Markdown converter for LLM consumption.

Usage:
    python docx2md.py <input>                  # input can be a .docx file or a directory
    python docx2md.py <input> -o <output_dir>  # default output dir: <input_dir>/output
    python docx2md.py <input> -r               # recurse into subdirectories
"""

import argparse
import base64
import hashlib
import sys
from pathlib import Path

import mammoth
from markdownify import markdownify as md


def _image_writer(image_dir: Path):
    """Return a mammoth image handler that writes images to image_dir."""
    image_dir.mkdir(parents=True, exist_ok=True)
    seen: dict[str, str] = {}

    def handler(image):
        with image.open() as f:
            data = f.read()
        digest = hashlib.md5(data).hexdigest()[:10]
        if digest in seen:
            return {"src": seen[digest]}

        ext = (image.content_type or "image/png").split("/")[-1].split("+")[0]
        if ext == "jpeg":
            ext = "jpg"
        filename = f"{digest}.{ext}"
        (image_dir / filename).write_bytes(data)

        rel = f"images/{image_dir.name}/{filename}"
        seen[digest] = rel
        return {"src": rel}

    return handler


def convert_one(docx_path: Path, output_dir: Path) -> tuple[Path, list[str]]:
    """Convert a single .docx to Markdown. Returns (output_path, warnings)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = docx_path.stem
    image_dir = output_dir / "images" / stem

    with docx_path.open("rb") as f:
        result = mammoth.convert_to_html(
            f,
            convert_image=mammoth.images.img_element(_image_writer(image_dir)),
        )

    markdown = md(
        result.value,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )

    out_path = output_dir / f"{stem}.md"
    out_path.write_text(markdown, encoding="utf-8")

    warnings = [m.message for m in result.messages if m.type == "warning"]
    return out_path, warnings


def collect_inputs(target: Path, recurse: bool) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".docx" else []
    pattern = "**/*.docx" if recurse else "*.docx"
    return [p for p in target.glob(pattern) if not p.name.startswith("~$")]


def _interactive_prompt() -> list[str]:
    """Prompt user for input when launched without arguments (double-click case)."""
    print("=" * 50)
    print("  DOCX -> Markdown 转换工具")
    print("=" * 50)
    print("把 .docx 文件或文件夹拖进来，或直接粘贴路径，然后回车")
    print("（多个路径用空格分隔，路径含空格请用双引号包起来）")
    raw = input("> ").strip()
    if not raw:
        return []
    import shlex
    try:
        return shlex.split(raw, posix=False)
    except ValueError:
        return [raw.strip('"')]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    interactive = not argv
    if interactive:
        argv = _interactive_prompt()
        if not argv:
            print("[info] 没有输入，退出。")
            input("按回车关闭窗口...")
            return 0

    parser = argparse.ArgumentParser(description="Convert DOCX files to Markdown.")
    parser.add_argument("input", type=Path, help="A .docx file or a directory.")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory.")
    parser.add_argument("-r", "--recurse", action="store_true", help="Recurse into subdirectories.")
    args = parser.parse_args(argv)

    target: Path = args.input.resolve()
    if not target.exists():
        print(f"[error] not found: {target}", file=sys.stderr)
        return 2

    base_dir = target.parent if target.is_file() else target
    output_dir: Path = (args.output or base_dir / "output").resolve()

    files = collect_inputs(target, args.recurse)
    if not files:
        print(f"[info] no .docx files found under {target}")
        return 0

    print(f"[info] converting {len(files)} file(s) -> {output_dir}")
    failed = 0
    for src in files:
        try:
            out, warnings = convert_one(src, output_dir)
            print(f"  ok  {src.name} -> {out.relative_to(output_dir.parent) if output_dir.parent in out.parents else out}")
            for w in warnings[:3]:
                print(f"      ! {w}")
            if len(warnings) > 3:
                print(f"      ! ... and {len(warnings) - 3} more warnings")
        except Exception as e:
            failed += 1
            print(f"  fail {src.name}: {e}", file=sys.stderr)

    print(f"[done] {len(files) - failed}/{len(files)} converted")
    if interactive:
        input("按回车关闭窗口...")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
