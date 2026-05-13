from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import pathlib
import textwrap

MD_PATH = pathlib.Path("Documentação/Manual_Usuario.md")
OUT_PDF = pathlib.Path("Documentação/Manual_Usuario.pdf")

def md_to_plain_lines(md: str):
    lines = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            lines.append("")
            continue

        # headings
        if line.startswith("# "):
            lines.append(line[2:].upper())
        elif line.startswith("## "):
            lines.append(line[3:].upper())
        elif line.startswith("### "):
            lines.append(line[4:].title())
        else:
            # light markdown cleanup
            line = line.replace("**", "")
            line = line.replace("* ", "- ")
            lines.append(line)
    return lines

def draw_wrapped_text(c, text, x, y, max_width_chars=95, line_height=13):
    wrapped = textwrap.wrap(
        text,
        width=max_width_chars,
        break_long_words=False,
        replace_whitespace=False,
    )
    for w in wrapped:
        c.drawString(x, y, w)
        y -= line_height
    return y

def main():
    if not MD_PATH.exists():
        raise FileNotFoundError(str(MD_PATH))

    md = MD_PATH.read_text(encoding="utf-8")
    lines = md_to_plain_lines(md)

    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    width, height = A4

    x = 2 * cm
    y = height - 2.2 * cm
    line_height = 13

    c.setTitle("Manual do Usuário — GlassPrinter")

    for line in lines:
        if not line.strip():
            y -= line_height // 2
            continue

        if y < 2 * cm:
            c.showPage()
            y = height - 2.2 * cm

        if line.isupper() and len(line) >= 4:
            c.setFont("Helvetica-Bold", 14)
            y = draw_wrapped_text(c, line, x, y, max_width_chars=70, line_height=18)
            c.setFont("Helvetica", 10)
            y -= 2
        else:
            c.setFont("Helvetica", 10)
            y = draw_wrapped_text(c, line, x, y, max_width_chars=95, line_height=line_height)

    c.save()
    print(str(OUT_PDF))

if __name__ == "__main__":
    main()
