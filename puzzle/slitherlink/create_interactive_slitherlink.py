# Generate HTML:

import math
import xml.sax.saxutils

from .slitherlink_config import GRID_TEXT_CONTENT, HEX_SIZE

# --- CONFIGURATION ---
# Output Filename
INTERACTIVE_HTML_FILENAME = "interactive_slitherlink.html"

# Style and Content Configuration
EDGE_COLORS = ['black', 'red', 'lightgrey']
VISIBLE_LINE_WIDTH = 1
CLICKABLE_LINE_WIDTH = 10
# --- END CONFIGURATION ---


def get_hexagon_vertices(center_x, center_y, size):
    """Calculates the 6 vertex coordinates (tuples) for a pointy-top hexagon."""
    vertices = []
    for i in range(6):
        angle_deg = 60 * i + 30
        angle_rad = math.pi / 180 * angle_deg
        x = center_x + size * math.cos(angle_rad)
        y = center_y + size * math.sin(angle_rad)
        vertices.append((x, y))
    return vertices


def get_grid_elements():
    """Helper to generate the grid components and boundaries."""
    lines = [line for line in GRID_TEXT_CONTENT.split('\n') if line]
    grid_radius = len(lines[0]) - 1

    hexagons = []
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    for r_idx, r in enumerate(range(-grid_radius, grid_radius + 1)):
        q_min = max(-grid_radius, -r - grid_radius)
        q_max = min(grid_radius, -r + grid_radius)
        line = lines[r_idx]

        for q_idx, q in enumerate(range(q_min, q_max + 1)):
            center_x = HEX_SIZE * math.sqrt(3) * (q + r / 2.0)
            center_y = HEX_SIZE * (3.0 / 2.0) * r
            vertices = get_hexagon_vertices(center_x, center_y, HEX_SIZE)
            char_to_draw = line[q_idx]

            hexagons.append({
                'center': (center_x, center_y),
                'vertices': vertices,
                'char': char_to_draw
            })

            for x, y in vertices:
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)

    padding = HEX_SIZE
    viewbox_str = f"{min_x - padding:.3f} {min_y - padding:.3f} {(max_x - min_x) + 2 * padding:.3f} {(max_y - min_y) + 2 * padding:.3f}"

    return hexagons, viewbox_str


def generate_interactive_html(hexagons, viewbox_str):
    """Generates a self-contained HTML file with an embedded, interactive SVG."""
    svg_elements = []
    drawn_edges = set()

    for hex_data in hexagons:
        # 1. Add interactive edges
        for i in range(len(hex_data['vertices'])):
            p1 = hex_data['vertices'][i]
            p2 = hex_data['vertices'][(i + 1) % 6]
            edge_tuple = tuple(sorted(((round(p1[0], 2), round(p1[1], 2)), (round(p2[0], 2), round(p2[1], 2)))))
            if edge_tuple in drawn_edges:
                continue
            drawn_edges.add(edge_tuple)

            # Create a unique, valid ID for the edge based on its coordinates
            coords_part = f"{edge_tuple[0][0]}_{edge_tuple[0][1]}_{edge_tuple[1][0]}_{edge_tuple[1][1]}"
            safe_coords = coords_part.replace('.', '_').replace('-', 'm')
            edge_id = f"edge-{safe_coords}"
            svg_elements.extend([
                f'<g id="{edge_id}" style="cursor: pointer;">',
                f'  <line x1="{p1[0]:.3f}" y1="{p1[1]:.3f}" x2="{p2[0]:.3f}" y2="{p2[1]:.3f}" stroke="transparent" stroke-width="{CLICKABLE_LINE_WIDTH}" />',
                f'  <line id="{edge_id}_visible" x1="{p1[0]:.3f}" y1="{p1[1]:.3f}" x2="{p2[0]:.3f}" y2="{p2[1]:.3f}" stroke="{EDGE_COLORS[0]}" stroke-width="{VISIBLE_LINE_WIDTH}" stroke-linecap="round" />',
                '</g>'
            ])

        # 3. Add text elements (drawn last, ignores clicks)
        if hex_data['char'].strip():
            center_x, center_y = hex_data['center']
            font_size = HEX_SIZE * 0.8
            escaped_char = xml.sax.saxutils.escape(hex_data['char'])
            svg_elements.append(
                f'<text x="{center_x:.3f}" y="{center_y:.3f}" font-size="{font_size}" text-anchor="middle" dominant-baseline="central" fill="#444" style="pointer-events: none;">{escaped_char}</text>'
            )

    svg_content = "\n".join(svg_elements)

    js_code = f"""
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const edgeColors = {EDGE_COLORS!r};
            const edgeStates = new Map();
            const edgeGroups = document.querySelectorAll('g[id^="edge-"]');

            edgeGroups.forEach(group => {{
                edgeStates.set(group.id, 0);
                group.addEventListener('click', () => handleEdgeClick(group.id));
            }});

            function handleEdgeClick(edgeId) {{
                let currentState = edgeStates.get(edgeId) || 0;
                const nextState = (currentState + 1) % edgeColors.length;
                edgeStates.set(edgeId, nextState);
                const newColor = edgeColors[nextState];
                const visibleLine = document.getElementById(edgeId + '_visible');
                if (visibleLine) {{ visibleLine.setAttribute('stroke', newColor); }}
            }}
        }});
    </script>"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Hexagonal Grid</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; margin: 1em; background-color: #f0f0f0; }}
        svg {{ border: 1px solid #ccc; background-color: white; max-width: 90vw; height: 80vh; }}
    </style>
</head>
<body>
    <h1>Interactive Hexagonal Grid</h1>
    <p>Click on the hexagon borders to change their color.</p>
    <svg viewBox="{viewbox_str}" xmlns="http://www.w3.org/2000/svg">
        {svg_content}
    </svg>
    {js_code}
</body>
</html>"""

    try:
        with open(INTERACTIVE_HTML_FILENAME, "w") as f:
            f.write(html_content)
        print(f"Successfully created interactive app: '{INTERACTIVE_HTML_FILENAME}'")
    except IOError as e:
        print(f"Error writing HTML file: {e}")


def main():
    """Generates a self-contained interactive HTML file."""
    hexagons, viewbox_str = get_grid_elements()
    generate_interactive_html(hexagons, viewbox_str)


if __name__ == "__main__":
    main()
