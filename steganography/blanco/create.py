import base64

import piexif
from PIL import Image

# Generate image:
image_dscription = b'Sorry'

# N  32°  3.123'
# E 034° 48.RGB'
RGB = ('00110001', '00111010', '00110011')  # 123
top_r = [
    '@  @     @@@ @@@  @       @@@    @@ @@  @@  @',
    '@@ @       @   @ @ @        @     @   @   @ @',
    '@ @@     @@@ @@@  @       @@@     @  @   @   ',
    '@  @       @ @              @     @          ',
    '@  @     @@@ @@@          @@@ @   @  @   @   ',
]
top_g = [
    '@  @     @@@ @@@  @       @@@   @@  @@@ @@  @',
    '@@ @       @   @ @ @        @     @   @   @ @',
    '@ @@     @@@ @@@  @       @@@    @  @@@  @   ',
    '@  @       @ @              @       @        ',
    '@  @     @@@ @@@          @@@ @  @  @@@  @   ',
]
top_b = [
    '@  @     @@@ @@@  @       @@@   @@  @@  @@@ @',
    '@@ @       @   @ @ @        @     @   @   @ @',
    '@ @@     @@@ @@@  @       @@@    @   @  @@@  ',
    '@  @       @ @              @             @  ',
    '@  @     @@@ @@@          @@@ @  @   @  @@@  ',
]

bottom = [
    '@@@  @@@ @@@ @ @  @   @ @ @@@   @@@  @@ @@@ @',
    '@    @ @   @ @ @ @ @  @ @ @ @   @ @ @   @ @ @',
    '@@   @ @ @@@ @@@  @   @@@ @@@   @@  @ @ @@   ',
    '@    @ @   @   @        @ @ @   @ @ @ @ @ @  ',
    '@@@  @@@ @@@   @        @ @@@ @ @ @  @@ @@@  ',
]


def put_block(board, x, y, value, block_size=8, offset=(0, 0)):
    for w in range(offset[0] + x * block_size, offset[0] + (x + 1) * block_size):
        for h in range(offset[1] + y * block_size, offset[1] + (y + 1) * block_size):
            board[h][w] = value


def image_from_boards(boards):
    width, height = len(boards[0][0]), len(boards[0])
    im = Image.new('RGB', (width, height))
    for y in range(height):
        for x in range(width):
            im.putpixel((x, y), tuple(board[y][x] for board in boards))
    return im


def generate_image(block_size=8, white=255, black=200, line_spacing=1, margin=8, offsets=((0, 0), (4, 4), (8, 0)), path=None):
    tops = (top_r, top_g, top_b)
    board_width = margin * 2 + max(len(bottom[0]) * block_size, max(len(top[0]) * block_size + offset[0] for offset, top in zip(offsets, tops)))
    bottom_base = margin + (max(len(top) for top in tops) + line_spacing) * block_size
    board_height = bottom_base + margin + (line_spacing + len(bottom)) * block_size
    boards = [[[white] * board_width for y in range(board_height)] for c in range(3)]
    for offset, top, board in zip(offsets, tops, boards):
        for y, line in enumerate(top):
            for x, c in enumerate(line):
                value = white if c == ' ' else black
                put_block(board, x, y, value, block_size=block_size, offset=offset)
    for board in boards:
        for y, line in enumerate(bottom):
            for x, c in enumerate(line):
                value = white if c == ' ' else black
                put_block(board, x, y, value, block_size=block_size, offset=(0, bottom_base))

    for bits, board in zip(RGB, boards):
        spaces = [i * len(board[0]) // len(bits) for i in range(len(bits) + 1)]
        for bit, start, stop in zip(bits, spaces[:-1], spaces[1:]):
            value = black if bit == '1' else white
            for y in range(board_height - block_size, board_height):
                for x in range(start, stop):
                    board[y][x] = value
    im = image_from_boards(boards)
    if path is not None:
#         exif_0th = {piexif.ImageIFD.ImageDescription: image_dscription}
#         exif = {"0th": exif_0th, "Exif": {}, "1st": {}, "thumbnail": None, "GPS": {}}
        im.save(path, quality=80, optimize=True, progressive=True) #, exif=piexif.dump(exif))
    return im


im = generate_image()
im  # show the image with high contrast

generate_image(black=254, path='blanco2.png')
with open('blanco2.png', 'rb') as f:
    data = f.read()
print(base64.b64encode(data))


# Parse image:
im = Image.open('blanco2.png')
for y in range(im.height):
    for x in range(im.width):
        value = im.getpixel((x, y))
        value = tuple(255 - (255 - c) * 255 // 5 for c in value)
#         value = (0, value[1], 0)
        im.putpixel((x, y), value)
im  # show the image with high contrast