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

import sys, threading, hashlib, hmac, base64, json
from urllib import parse as url_parse, request

DEFAULT_CONCURRENCY = 20

class Data:
    pass

def get_news_key(original_news_url, news_secret_key):
    news_key = hmac.new(
            news_secret_key,
            original_news_url.encode(),
            hashlib.sha256,
            ).digest()
    
    return news_key[:6]

def make_world_news_thread(thr_lock, in_msg_iter,
        site_url, news_secret_key, use_short=None,
        on_begin=None, on_result=None):
    if use_short is None:
        use_short = False
    
    while True:
        data = Data()
        
        with thr_lock:
            try:
                data.msg_id, data.in_msg = next(in_msg_iter)
            except StopIteration:
                return
        
        if on_begin is not None:
            on_begin(data)
        
        try:
            result_msg = []
            
            for in_msg_cell in data.in_msg.split('|'):
                result_cell = []
                
                for in_msg_word in data.in_msg.split(' '):
                    if not in_msg_word.startswith('https://') and \
                            not in_msg_word.startswith('http://') or \
                            in_msg_word.startswith(url_parse.urljoin(site_url, 'sh/')) or \
                            in_msg_word.startswith(url_parse.urljoin(site_url, 'news/')):
                        result_cell.append(in_msg_word)
                        
                        continue
                    
                    in_msg_url = in_msg_word
                    
                    news_key = get_news_key(in_msg_url, news_secret_key)
                    news_key_b64 = base64.b64encode(news_key).decode('utf-8', 'replace')
                    
                    if use_short:
                        opener = request.build_opener()
                        resp = opener.open(
                                request.Request(
                                        url_parse.urljoin(site_url, 'api/sh/new'),
                                        json.dumps({
                                                'original_news_url': in_msg_url,
                                                'news_key': news_key_b64,
                                               }).encode(),
                                        {'Content-Type': 'application/json;charset=utf-8'},
                                        ),
                                timeout=20.0,
                                )
                        if resp.getcode() != 200:
                            raise IOError('resp.getcode() != 200')
                        
                        sh_data = json.loads(resp.read(10000000).decode('utf-8', 'replace'))
                        news_url = sh_data.get('micro_news_url')
                    else:
                        o_scheme, o_netloc, o_path, o_query, o_fragment = \
                                url_parse.urlsplit(in_msg_url)
                        
                        o_netloc = o_netloc.replace('.', '_')
                        
                        if o_path and not o_path.startswith('/'):
                            o_path = '/{}'.format(o_path)
                        
                        query_kwargs = {
                                'key': news_key_b64,
                                }
                        
                        if o_scheme and o_scheme != 'http':
                            query_kwargs['scheme'] = o_scheme
                        
                        if o_netloc.startswith('www_'):
                            query_kwargs['wnetloc'] = o_netloc[len('www_'):]
                        elif o_netloc:
                            query_kwargs['netloc'] = o_netloc
                        
                        if o_query:
                            query_kwargs['query'] = o_query
                        
                        if o_fragment:
                            query_kwargs['fragment'] = o_fragment
                        
                        query = url_parse.urlencode(query_kwargs)
                        news_url_path = 'news{}{}'.format(
                                o_path,
                                '?{}'.format(query) if query else '',
                                )
                        news_url = url_parse.urljoin(site_url, news_url_path)
                    
                    result_cell.append(news_url)
                
                result_msg.append(' '.join(result_cell))
            
            data.result = '|'.join(result_msg)
        except Exception:
            data.error = sys.exc_info()
        else:
            data.error = None
        
        if on_result is not None:
            on_result(data)

def make_world_news(in_msg_list,
        site_url, news_secret_key, use_short=None,
        conc=None, on_begin=None, on_result=None, on_done=None):
    if conc is None:
        conc = DEFAULT_CONCURRENCY
    
    thr_lock = threading.RLock()
    in_msg_iter = enumerate(in_msg_list)
    
    thread_list = tuple(
            threading.Thread(
                    target=lambda: make_world_news_thread(
                            thr_lock,
                            in_msg_iter,
                            site_url,
                            news_secret_key,
                            use_short=use_short,
                            on_begin=on_begin,
                            on_result=on_result,
                            ),
                    )
            for thread_i in range(conc)
            )
    
    for thread in thread_list:
        thread.start()
    
    def in_thread():
        for thread in thread_list:
            thread.join()
        
        if on_done is not None:
            on_done()
    
    threading.Thread(target=in_thread).start()
