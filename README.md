make-world-news
===============

``make-world-news`` is utility for creating new pages (getting links)
for web-sites of class ``world-news``.

Status
------

Beta branch.

Compiling for Microsoft Windows
-------------------------------

Using cx_Freeze like:

    $ cxfreeze \
            --base-name=Win32GUI \
            --target-name=make-world-news-gui.exe \
            start_make_world_news_gui_2013_02_12.py
    $ echo "VERSION: $(git rev-list HEAD^..)" > dist/VERSION.txt
