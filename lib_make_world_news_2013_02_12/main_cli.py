# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2013 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

assert str is not bytes

import threading, argparse, configparser, base64, heapq
from . import fix_url, read_list, make_world_news

class UserError(Exception):
    pass

def on_begin(ui_lock, data):
    with ui_lock:
        print('[{!r}] begin: {!r}'.format(data.msg_id, data.in_msg))

def on_result(ui_lock, out_heap, data):
    with ui_lock:
        if data.error is not None:
            print('[{!r}] error: {!r}: {!r}: {!r}'.format(
                    data.msg_id, data.in_msg,
                    data.error[0], data.error[1]))
            return
        
        heapq.heappush(out_heap, (data.msg_id, data))
        
        print('[{!r}] pass: {!r}'.format(data.msg_id, data.in_msg))

def on_done(ui_lock, out_heap, out_fd, done_event):
    with ui_lock:
        print('writing...')
        
        while True:
            try:
                msg_id, data = heapq.heappop(out_heap)
            except IndexError:
                break
            
            out_fd.write('{}\n'.format(data.result))
            out_fd.flush()
        
        print('done!')
        done_event.set()

def main():
    parser = argparse.ArgumentParser(
            description='utility for creating new pages (getting links) '
                    'for web-sites of class ``world-news``.',
            )
    parser.add_argument(
            '--use-short',
            action='store_true',
            help='use short links',
            )
    parser.add_argument(
            'cfg',
            metavar='CONFIG-PATH',
            help='path to configuration file',
            )
    parser.add_argument(
            'in_msgs',
            metavar='INPUT-MESSAGES-PATH',
            help='path to input news messages (with original urls) list file',
            )
    parser.add_argument(
            'out',
            metavar='OUTPUT-MESSAGES-PATH',
            help='path to output result messages (with urls) list file',
            )
    args = parser.parse_args()
    
    if args.cfg is None:
        raise UserError('args.cfg is None')
    if args.in_msgs is None:
        raise UserError('args.in_msgs is None')
    if args.out is None:
        raise UserError('args.out is None')
    
    cfg = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation())
    with open(args.cfg, encoding='utf-8', errors='replace') as cfg_fd:
        cfg.read_file(cfg_fd)
    
    site_url = cfg.get('core', 'site_url')
    news_secret_key_b64 = cfg.get('core', 'news_secret_key')
    news_secret_key = base64.b64decode(news_secret_key_b64.encode())
    
    site_url = fix_url.fix_url(site_url)
    
    ui_lock = threading.RLock()
    
    in_msg_list = read_list.read_list(args.in_msgs)
    out_heap = []
    
    with open(args.out, 'w', encoding='utf-8', newline='\n') as out_fd:
        done_event = threading.Event()
        make_world_news.make_world_news(
                in_msg_list,
                site_url,
                news_secret_key,
                use_short=args.use_short,
                on_begin=lambda data: on_begin(ui_lock, data),
                on_result=lambda data: on_result(ui_lock, out_heap, data),
                on_done=lambda: on_done(ui_lock, out_heap, out_fd, done_event),
                )
        done_event.wait()
