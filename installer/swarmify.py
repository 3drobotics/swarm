#!/usr/bin/env python

import curses


stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
#curses.curs_set(0)

if curses.has_colors():
    curses.start_color()

curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)

stdscr.addstr("Select Solos to swarmify", curses.A_REVERSE)
stdscr.chgat(-1, curses.A_REVERSE)

stdscr.addstr(curses.LINES-1, 0, "Press 'ESC' to go back, 'Q' to quit")

stdscr.chgat(curses.LINES-1,7, 1, curses.A_BOLD | curses.color_pair(2))

outer_window = curses.newwin(curses.LINES-2, curses.COLS, 1,0)
text_window = outer_window.subwin(curses.LINES-6, curses.COLS-4, 3,2)
text_window.addstr("Sololink_whatever")
outer_window.box()

stdscr.noutrefresh()
outer_window.noutrefresh()

curses.doupdate()

while True:
    c = outer_window.getch()

    if c == ord('r') or c == ord('R'):
        text_window.clear()
        text_window.addstr("Looking for Solos", curses.color_pair(3))
        text_window.refresh()
        text_window.clear()
    elif c == ord('q') or c == ord('Q'):
        break

    stdscr.noutrefresh()
    outer_window.noutrefresh()
    text_window.noutrefresh()
    curses.doupdate()


curses.nocbreak()
curses.echo()
curses.curs_set(1)

curses.endwin()
