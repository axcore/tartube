#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2023 A S Lewis
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Classes imported and slightly modified for use by Tartube."""


# Import Gtk modules
#   ...


# Import other modules
import re
import textwrap


# Import our modules
#   ...


# Classes


class ModTextWrapper(textwrap.TextWrapper):

    """Python class to modify the behaviour of textwrap by Gregory P. Ward.

    If 'break_on_hyphens' is specified, wrap the text on both hyphens and
    forward slashes. In that way, we can break up long URLs in calls to
    utils.tidy_up_long_descrip() and utils.tidy_up_long_string().

    v2.3.606: Modified the '_whitespace' field to allow wrapping after an
    underline.
    """

    def _split(self, text):

#       _whitespace = '\t\n\x0b\x0c\r\_ '
        _whitespace = '\t\n\x0b\x0c\r '

        word_punct = r'[\w!"\'&.,?]'
        letter = r'[^\d\W]'
        whitespace = r'[%s]' % re.escape(_whitespace)
        nowhitespace = '[^' + whitespace[1:]
        mod_wordsep_re = re.compile(r'''
            ( # any whitespace
              %(ws)s+
            | # em-dash between words
              (?<=%(wp)s) -{2,} (?=\w)
            | # word, possibly hyphenated
              %(nws)s+? (?:
                # hyphenated word, or word with forward slash
                  [-\/](?: (?<=%(lt)s{2}[-\/]) | (?<=%(lt)s[-\/]%(lt)s[-\/]))
                  (?= %(lt)s [-\/]? %(lt)s)
                | # end of word
                  (?=%(ws)s|\Z)
                | # em-dash
                  (?<=%(wp)s) (?=-{2,}\w)
                )
            )''' % {'wp': word_punct, 'lt': letter,
                    'ws': whitespace, 'nws': nowhitespace},
            re.VERBOSE)

        if self.break_on_hyphens is True:
            chunks = mod_wordsep_re.split(text)
        else:
            chunks = self.wordsep_simple_re.split(text)
        chunks = [c for c in chunks if c]
        return chunks

