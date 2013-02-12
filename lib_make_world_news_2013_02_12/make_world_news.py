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

import sys, threading, hashlib, hmac, base64
from urllib import parse as url_parse

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

def make_world_news_thread(thr_lock, url_iter,
        site_url, news_secret_key,
        on_begin=None, on_result=None):
    while True:
        data = Data()
        
        with thr_lock:
            try:
                data.url_id, data.o_url = next(url_iter)
            except StopIteration:
                return
        
        if on_begin is not None:
            on_begin(data)
        
        try:
            o_scheme, o_netloc, o_path, o_query, o_fragment = \
                    url_parse.urlsplit(data.o_url)
            
            if o_path and not o_path.startswith('/'):
                o_path = '/{}'.format(o_path)
            
            query_kwargs = {
                    'key': base64.b64encode(get_news_key(data.o_url, news_secret_key)),
                    }
            
            if o_scheme and o_scheme != 'http':
                query_kwargs['scheme'] = o_scheme
            
            if o_netloc.startswith('www.'):
                query_kwargs['wnetloc'] = o_netloc[len('www.'):]
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
            
            data.result = news_url
        except Exception:
            data.error = sys.exc_info()
        else:
            data.error = None
        
        if on_result is not None:
            on_result(data)

def make_world_news(o_url_list,
        site_url=None, news_secret_key=None,
        conc=None, on_begin=None, on_result=None, on_done=None):
    if conc is None:
        conc = DEFAULT_CONCURRENCY
    
    thr_lock = threading.RLock()
    o_url_iter = enumerate(o_url_list)
    
    thread_list = tuple(
            threading.Thread(
                    target=lambda: make_world_news_thread(
                            thr_lock,
                            o_url_iter,
                            site_url,
                            news_secret_key,
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
