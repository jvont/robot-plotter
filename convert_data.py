import os

import numpy as np
from svgpathtools import Line, svg2paths2, bezier_point


# Input Parameters -----------------------------------------------------------

images_path = 'images/'
dataset_path = 'datasets/trees.npz'
width = 30
height = 24

# ----------------------------------------------------------------------------


def paths_to_stroke3(paths, scale=1.0):
    """Convert an svg path to stroke format."""
    strokes = []
    end = complex(0, 0)
    for path in paths:
        start = path[0].start
        dx = scale * (start.real - end.real)
        dy = scale * (start.imag - end.imag)
        strokes.append([dx, dy, 0])

        for segment in path:
            start = segment.start
            if end is None:
                strokes.append([scale * start.real, scale * start.imag, 0])

            end = segment.end
            if isinstance(segment, Line):
                dx = scale * (end.real - start.real)
                dy = scale * (end.imag - start.imag)
                strokes.append([dx, dy, 1])
            else:
                for i in range(1, 11):
                    end = bezier_point(segment, 0.1 * i)
                    dx = scale * (end.real - start.real)
                    dy = scale * (end.imag - start.imag)
                    strokes.append([dx, dy, 1])
                    start = end

    return strokes


def stroke3_to_gcode(strokes, scale=1.0, F=200):
    """Converts code in stroke-3 format to g code."""
    ZUP = 'M3S60'
    ZDOWN = 'M5'
    X, Y, Z = strokes[0]

    gcode = []
    gcode.append(ZDOWN if Z else ZUP)
    gcode.append(f'F{F}')
    gcode.append(f'G0X{scale * X:.5f}Y{scale * Y:.5f}')
    for dx, dy, z in strokes[1:]:
        X += dx
        Y += dy
        if Z != z:
            Z = z
            gcode.append(ZDOWN if Z else ZUP)

        gcode.append(f'G1X{scale * X:.5f}Y{scale * Y:.5f}')

    gcode.append(ZUP)
    return '\n'.join(gcode)


def plot_stroke3(strokes):
    """Plot stroke-3 line segments."""
    import matplotlib.pyplot as plt
    X, Y = (0, 0)
    for dx, dy, Z in strokes:
        if Z:
            plt.plot([X, X + dx], [Y, Y + dy], c='k', ls='-')

        X += dx
        Y += dy

    plt.show()


def convert_file(path):
    """Converts an svg to stroke-3 + gcode."""
    # determine scaling factor
    paths, _, attrs = svg2paths2(path)
    x1, y1, x2, y2 = [float(d) for d in attrs['viewBox'].split()]
    vwidth = x2 - x1
    vheight = y2 - y1
    scale = 0.9 * min(width / vwidth, height / vheight)

    # convert paths to stroke-3 + gcode
    strokes = paths_to_stroke3(paths)
    gcode = stroke3_to_gcode(strokes, scale=scale, F=250)

    return strokes, gcode


if __name__ == '__main__':
    dataset = []
    for p in os.listdir(images_path):
        fp = os.path.join(images_path, p)
        if os.path.isfile(fp) and fp.endswith('.svg'):
            # convert svg to stroke-3 + gcode
            strokes, gcode = convert_file(fp)
            dataset.append(strokes)

            # save to gcode
            name = os.path.splitext(p)[0]
            with open(f'gcode/{name}.gcode', 'w') as f:
                f.write(gcode)

            # plot_stroke3(strokes)

    # convert and save stroke-3
    npdataset = [np.asarray(d, dtype=np.float32) for d in dataset]
    with open(dataset_path, 'wb') as f:
        np.savez_compressed(f, *npdataset)
