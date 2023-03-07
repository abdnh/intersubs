# holds the styling of the subtitles. Modify at your own risks.
style_subs = """
    QFrame {
        font-family: "Noto Serif CJK JP Light";
    }
"""

# point size of the font as in https://doc.qt.io/qt-5/qfont.html#pointSize
default_font_point_size = 25

# default zoom of the popup
default_zoom_popup = 1

# number of pixels to leave at the bottom of the screen, below subtitles
bottom_spacing_pixels = 100

# indicates the index of the screen the subtitles will be displayed on, to set manually.
# For example, if you have 3 screens, this number could be either 0, 1 or 2.
n_screen = 0

# Subtitle lines with more words than the specified number will be split
max_sub_line_words = 8

# If set to True, the pop-up dictionary will be triggered on click, while the on-click one will be triggered on a double click
# TODO: only tested on Windows - test on Linux
alternative_triggers = True

# Ideally, more parameters could be added here, as interSubs does:
# https://github.com/oltodosel/interSubs/blob/master/interSubs_config.py
