#!/usr/bin/python

import os.path
import sys

import cairo
import rsvg


def combine(svg_files, out_file, size):
    img =  cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(img)
    ctx.scale(size/500.0, size/500.0)
    for f in svg_files:
        handler = rsvg.Handle(f)
        handler.render_cairo(ctx)
    img.write_to_png(out_file)


thisdir = os.path.dirname(os.path.abspath(__file__))
updir = os.path.normpath(os.path.join(thisdir, '..'))

if __name__ == '__main__':
    award_types = [('STUDENT', 'shield_green.svg'),
                   ('MASTER', 'shield_red.svg'),
                   ('SHARER', 'shield_blue.svg'),
                   ('TREND_SETTER', 'shield_orange.svg'),
                   ('ACE', 'shield_silver.svg'),
                   ]

    for name, award_file in award_types:
        for level in ['any', 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            for size in [50, 100]:
                svgs = [os.path.join(updir, 'resources', award_file)]
                if level != 'any':
                    svgs.append(os.path.join(updir, 'resources', 'shield_level_%s.svg' % level))
                fname = os.path.join(updir, 'learnscripture', 'static', 'img', 'awards',
                                     'award_%s_level_%s_%d.png' %
                                     (name, level, size))

                combine(svgs, fname, size)
