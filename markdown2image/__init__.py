from . import parser
import time
from . import style
# from rich import print

def md2img(markdown: str, output_path: str, debug: bool = False) -> None:
    ast = style.init_style(
        style.init_lists(
            style.init_pre(
                style.init_links(
                    parser.parse(
                        markdown
                    )
                )
            )
        )
    )
    size = style.get_size(ast)
    try:
        bg_color = style.default_style["html"]["background_color"]
    except KeyError:
        bg_color = (255, 255, 255, 255)
    i = style.draw(ast, size, bg_color)
    if debug:
        i.show()
    i.save(output_path)
