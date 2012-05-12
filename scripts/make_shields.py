#!/usr/bin/python

import os.path
import sys

import cairo
import rsvg

def scale_img(img, size):
    factor = float(img.get_width()) / float(size)
    scaler = cairo.Matrix()
    scaler.scale(factor, factor)
    imgpat = cairo.SurfacePattern(img)
    imgpat.set_matrix(scaler)
    imgpat.set_filter(cairo.FILTER_BEST)
    canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(canvas)
    ctx.set_source(imgpat)
    ctx.paint()

    return canvas

def combine(svg_files, out_file, size):
    # First create on a larger than necessary surface, later scale back. This
    # gives better results
    SCALE = 5
    img1_size = int(size * SCALE)
    img = cairo.ImageSurface(cairo.FORMAT_ARGB32, img1_size, img1_size)
    ctx = cairo.Context(img)
    ctx.scale(img1_size/500.0, img1_size/500.0) # 500 is the nominal width of SVG images
    for f in svg_files:
        handler = rsvg.Handle(f)
        handler.render_cairo(ctx)
    img2 = scale_img(img, size)
    img2.write_to_png(out_file)


thisdir = os.path.dirname(os.path.abspath(__file__))
updir = os.path.normpath(os.path.join(thisdir, '..'))

if __name__ == '__main__':
    award_types = [('STUDENT', 'shield_green.svg'),
                   ('MASTER', 'shield_red.svg'),
                   ('SHARER', 'shield_blue.svg'),
                   ('TREND_SETTER', 'shield_orange.svg'),
                   ('ACE', 'shield_silver.svg'),
                   ('RECRUITER', 'shield_recruit.svg'),
                   ('HACKER', 'shield_hacker.svg'),
                   ('WEEKLY_CHAMPION', 'shield_gold.svg'),
                   ('REIGNING_WEEKLY_CHAMPION', 'shield_gold_crown.svg'),
                   ]

    for name, award_file in award_types:
        for level in ['any', 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            for size in [50, 100]:
                svgs = [os.path.join(updir, 'resources', award_file)]
                if level != 'any':
                    if name in ['RECRUITER']:
                        number_file = 'shield_level_%s_t2.svg'
                    else:
                        # Single level awards
                        if name in ['HACKER', 'REIGNING_WEEKLY_CHAMPION']:
                            if level > 1:
                                continue
                            else:
                                number_file = None
                        else:
                            number_file = 'shield_level_%s.svg'

                    if number_file is not None:
                        svgs.append(os.path.join(updir, 'resources', number_file % level))
                fname = os.path.join(updir, 'learnscripture', 'static', 'img', 'awards',
                                     'award_%s_level_%s_%d.png' %
                                     (name, level, size))

                combine(svgs, fname, size)
