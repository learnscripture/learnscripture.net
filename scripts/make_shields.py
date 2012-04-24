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
    shield_types = [('LEARNER', 'shield_green.svg'),
                    ('RECRUITER', 'shield_blue.svg'),
                    ('TREND_SETTER', 'shield_red.svg'),
                    ('MASTER', 'shield_gold.svg')]

    for name, shield_file in shield_types:
        for level in [1, 2, 3]:
            for size in [50, 100]:
                s1 = os.path.join(updir, 'resources', shield_file)
                s2 = os.path.join(updir, 'resources', 'shield_level_%d.svg' % level)
                fname = os.path.join(updir, 'learnscripture', 'static', 'img',
                                     'shield_%s_level_%d_%d.png' %
                                     (name, level, size))
                combine([s1, s2], fname, size)
