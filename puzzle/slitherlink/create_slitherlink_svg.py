# Generate SVG:

import math
import xml.sax.saxutils
import random

from .slitherlink_config import GRID_TEXT_CONTENT

# --- CONFIGURATION ---
# The name of the output SVG file.
OUTPUT_FILENAME = "slitherlink.svg"

PRINTABLE = False

if PRINTABLE:
    BORDER_COLOR = 'lightgrey'
    BEEHIVE_COLORS = ['#FFFFFF']
else:
    BORDER_COLOR = 'black'
    # A list of beehive-like colors to be chosen from randomly for each hexagon.
    BEEHIVE_COLORS = ['#FFE180', '#FFEB80', '#FFD280', '#F8F2C5', '#ECD290']
# --- END CONFIGURATION ---


def get_hexagon_points_string(center_x, center_y, size):
    """
    Calculates the 6 vertex coordinates for a pointy-top hexagon.
    """
    points = []
    for i in range(6):
        angle_deg = 60 * i + 30
        angle_rad = math.pi / 180 * angle_deg
        x = center_x + size * math.cos(angle_rad)
        y = center_y + size * math.sin(angle_rad)
        points.append(f"{x:.3f},{y:.3f}")
    return " ".join(points)


def main():
    """
    Generates an SVG file with a hexagonal grid, with text content mapped
    from a multiline string constant.
    """

    lines = [line for line in GRID_TEXT_CONTENT.split('\n') if line]
    grid_radius = len(lines[0]) - 1

    # Validate the dimensions of the provided text content against the grid size.
    expected_rows = 2 * grid_radius + 1
    if len(lines) != expected_rows:
        print(
            f"Configuration Error: GRID_TEXT_CONTENT has {len(lines)} lines, "
            f"but the grid for edge size of {grid_radius + 1} requires {expected_rows} lines."
        )
        return

    svg_polygon_elements = []
    svg_center_text_elements = []
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    # Iterate through the grid using axial coordinates (q, r), but in a way
    # that corresponds to visual rows to map to the text content.
    for r_idx, r in enumerate(range(-grid_radius, grid_radius + 1)):
        q_min = max(-grid_radius, -r - grid_radius)
        q_max = min(grid_radius, -r + grid_radius)

        line = lines[r_idx]
        expected_cols = q_max - q_min + 1
        if len(line) != expected_cols:
            print(
                f"Configuration Error: Row {r_idx+1} in GRID_TEXT_CONTENT has {len(line)} chars, "
                f"but this grid row requires {expected_cols} characters."
            )
            return

        for q_idx, q in enumerate(range(q_min, q_max + 1)):
            char_to_draw = line[q_idx]

            # Convert axial grid coordinates to pixel coordinates.
            center_x = HEX_SIZE * math.sqrt(3) * (q + r / 2.0)
            center_y = HEX_SIZE * (3.0 / 2.0) * r

            # Add the hexagon polygon with a random beehive color.
            points_str = get_hexagon_points_string(center_x, center_y, HEX_SIZE)
            background_color = random.choice(BEEHIVE_COLORS)
            svg_polygon_elements.append(
                f'  <polygon points="{points_str}" style="fill:{background_color};stroke:{BORDER_COLOR};stroke-width:1" />'
            )

            # Add the center text, unless it's a space.
            if char_to_draw.strip():
                font_size = HEX_SIZE * 0.8
                escaped_char = xml.sax.saxutils.escape(char_to_draw)
                svg_center_text_elements.append(
                    f'  <text x="{center_x:.3f}" y="{center_y:.3f}" font-size="{font_size}" '
                    f'text-anchor="middle" dominant-baseline="central" fill="black">{escaped_char}</text>'
                )

            # Update the drawing boundaries.
            hex_half_width = HEX_SIZE * math.sqrt(3) / 2
            min_x = min(min_x, center_x - hex_half_width)
            max_x = max(max_x, center_x + hex_half_width)
            min_y = min(min_y, center_y - HEX_SIZE)
            max_y = max(max_y, center_y + HEX_SIZE)

    # Finalize SVG content.
    padding = HEX_SIZE * 0.5
    viewbox_x = min_x - padding
    viewbox_y = min_y - padding
    viewbox_width = (max_x - min_x) + 2 * padding
    viewbox_height = (max_y - min_y) + 2 * padding

    all_elements = svg_polygon_elements + svg_center_text_elements
    elements_inner_svg = "\n".join(all_elements)

    svg_content = f'''<svg width="{viewbox_width:.3f}" height="{viewbox_height:.3f}" viewBox="{viewbox_x:.3f} {viewbox_y:.3f} {viewbox_width:.3f} {viewbox_height:.3f}" xmlns="http://www.w3.org/2000/svg">
<g id="hexgrid">
{elements_inner_svg}
</g>
</svg>'''

    # Write to file.
    try:
        with open(OUTPUT_FILENAME, "w") as f:
            f.write(svg_content)
        print(f"Successfully created hexagonal grid in '{OUTPUT_FILENAME}'")
    except IOError as e:
        print(f"Error writing to file '{OUTPUT_FILENAME}': {e}")


if __name__ == "__main__":
    main()
