import sys
import os

# Add the cloned repo to path
sys.path.append(os.path.abspath("themes_cloned/catppuccin_python"))

from catppuccin import PALETTE

# Updated template for Container-based Chat Layout
TEMPLATE = """/* === Catppuccin {flavor_name} === */
.theme-{flavor_id} {{
    background: {base};
    color: {text};
    /* 优化滚动条: 更细、交互更明显 */
    scrollbar-color: {surface2};
    scrollbar-color-hover: {blue};
    scrollbar-color-active: {lavender};
    scrollbar-background: {base};
    scrollbar-background-hover: {crust};
    scrollbar-background-active: {crust};
    scrollbar-corner-color: {crust};
    scrollbar-size-vertical: 1;
    scrollbar-size-horizontal: 1;
}}

/* Header Styling */
.theme-{flavor_id} Header {{
    background: {mantle};
    color: {mauve};
}}

.theme-{flavor_id} HeaderTitle {{
    color: {mauve};
}}

/* Status Bar */
.theme-{flavor_id} #status-bar {{
    background: {mantle};
    color: {text};
    border-top: heavy {overlay0}; 
}}

/* Common Bubble Container */
.theme-{flavor_id} .user-bubble-container, 
.theme-{flavor_id} .ai-bubble-container, 
.theme-{flavor_id} .system-bubble-container,
.theme-{flavor_id} .input-container {{
    margin: 1 2;
    padding: 0 0; 
    border: heavy {overlay0}; 
    background: transparent;
    height: auto;
    width: 100%; /* 恢复满宽，避免坍缩 */
}}

.theme-{flavor_id} .bubble-content {{
    height: auto;
    width: 100%;
    text-wrap: wrap; 
    overflow: hidden;
    padding: 0 1;
}}

/* Bubble Headers */
.theme-{flavor_id} .bubble-header {{
    dock: top;
    width: 100%;
    background: {surface0};
    color: {text};
    padding: 0 1;
    margin-bottom: 1; /* 标题栏与内容间距 */
    text-style: bold;
}}

/* Specific Styles per Role */

/* User */
.theme-{flavor_id} .user-bubble-container {{
    border: heavy {pink};
}}
.theme-{flavor_id} .user-header {{
    background: {pink};
    color: {base}; /* Contrast text */
}}
.theme-{flavor_id} .user-bubble-container .bubble-content {{
    color: {pink};
    padding: 0 1;
}}

/* AI */
.theme-{flavor_id} .ai-bubble-container {{
    border: heavy {cyan};
}}
.theme-{flavor_id} .ai-header {{
    background: {cyan};
    color: {base};
}}
.theme-{flavor_id} .ai-bubble-container .bubble-content {{
    color: {cyan};
    padding: 0 1;
}}

/* System */
.theme-{flavor_id} .system-bubble-container {{
    border: dashed {overlay0};
}}
.theme-{flavor_id} .system-header {{
    background: {overlay0};
    color: {base};
}}
.theme-{flavor_id} .system-bubble-container .bubble-content {{
    color: {overlay0};
    padding: 0 1;
}}

/* ERROR */
.theme-{flavor_id} .error-bubble {{
    color: {red};
}}


/* Input Container */
.theme-{flavor_id} .input-container {{
    border: heavy {green};
}}
.theme-{flavor_id} .input-header {{
    background: {green};
    color: {base};
}}

/* Inline Input Widget inside container */
.theme-{flavor_id} .inline-input {{
    background: transparent;
    border: none;
    color: {green};
    height: auto;
    min-height: 1; /* 默认一行，输入多了自动扩展 */
    padding: 0 0; /* TextArea 自带 padding */
}}
.theme-{flavor_id} .inline-input:focus {{
    background: transparent; 
}}

/* TextArea 内部去黑底 */
.theme-{flavor_id} .inline-input > .text-area--cursor-line {{
    background: transparent;
}}
.theme-{flavor_id} .inline-input > .text-area--content {{
    background: transparent;
}}

/* TextArea specific styling */
.theme-{flavor_id} .inline-input .text-area--cursor {{
    background: {green};
    color: {base};
}}

/* Reconnecting Animation specific */
.theme-{flavor_id} .reconnecting {{
    color: {yellow};
}}
"""

def generate():
    flavors = [PALETTE.latte, PALETTE.frappe, PALETTE.macchiato, PALETTE.mocha]
    
    full_content = "/* Generated Catppuccin Themes - Cyberpunk Container Style */\n\n"
    
    for flavor in flavors:
        c = flavor.colors
        content = TEMPLATE.format(
            flavor_name=flavor.name,
            flavor_id=flavor.identifier,
            base=c.base.hex,
            mantle=c.mantle.hex,
            text=c.text.hex,
            overlay0=c.overlay0.hex,
            mauve=c.mauve.hex,
            pink=c.pink.hex,
            sky=c.sky.hex,
            green=c.green.hex,
            peach=c.peach.hex,
            red=c.red.hex,
            yellow=c.yellow.hex,
            teal=c.teal.hex,
            surface0=c.surface0.hex,
            cyan=c.sky.hex,
            blue=c.blue.hex,
            lavender=c.lavender.hex,
            surface2=c.surface2.hex,
            crust=c.crust.hex,
        )
        full_content += content + "\n"
        
    filename = "styles/all_themes.tcss"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate()
