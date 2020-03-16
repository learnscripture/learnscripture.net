#!/usr/bin/python

import os.path

import cairo
import gi

gi.require_version('Rsvg', '2.0')

from gi.repository import Rsvg  # noqa:E402  isort:skip


# Running this script requires some additional dependencies:
#
# sudo apt install gir1.2-rsvg-2.0 python3-cairo python3-gi

def combine(svg_files, out_file, size):
    img = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(img)
    ctx.scale(size / 500.0, size / 500.0)
    for f in svg_files:
        handle = Rsvg.Handle()
        svg = handle.new_from_file(f)
        svg.render_cairo(ctx)
    img.write_to_png(out_file)


thisdir = os.path.dirname(os.path.abspath(__file__))
updir = os.path.normpath(os.path.join(thisdir, '..'))

if __name__ == '__main__':
    award_types = [('STUDENT', 'shield_green.svg'),
                   ('MASTER', 'shield_red.svg'),
                   ('SHARER', 'shield_blue.svg'),
                   ('TREND_SETTER', 'shield_orange.svg'),
                   ('ACE', 'shield_silver.svg'),
                   ('RECRUITER', 'shield_recruit.svg'),
                   ('ADDICT', 'shield_addict.svg'),
                   ('ORGANIZER', 'shield_organizer.svg'),
                   ('CONSISTENT_LEARNER', 'shield_consistent.svg'),
                   ('QUESTION', 'shield_question.svg'),
                   ]

    single_level_awards = ['ADDICT']
    for name, award_file in award_types:
        if name in ['QUESTION']:
            levels = ['any']
        elif name in single_level_awards:
            levels = ['any', 1]
        elif name == 'CONSISTENT_LEARNER':
            levels = ['any'] + list(range(1, 11))
        else:
            levels = ['any'] + list(range(1, 10))
        for level in levels:
            for size in [50, 100]:
                svgs = [award_file]
                if level != 'any':
                    number_file = None
                    # Overlay number
                    if name in ['RECRUITER', 'ORGANIZER']:
                        # Smaller number icons
                        number_file = 'shield_level_%s_t2.svg'
                    elif name in single_level_awards:
                        number_file = None
                    else:
                        number_file = 'shield_level_%s.svg'

                    if number_file is not None:
                        svgs.append(number_file % level)

                    # Overlay number highlight for top level
                    if level == levels[-1] and name not in single_level_awards:
                        svgs.append((number_file % (str(level) + '_highlight')))

                fname = os.path.join(updir, 'learnscripture', 'static', 'img', 'awards',
                                     'award_%s_level_%s_%d.png' %
                                     (name, level, size))

                combine([os.path.join(updir, 'resources', f) for f in svgs], fname, size)
