#!/usr/bin/env python3
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

import re

def create_hashtag_set(word_list):
    hashtag_set = set()
    
    for item in word_list:
        hashtag_set.add(item)
        
        if not isinstance(item, str):
            continue
        
        hashtag_set.add(item.lower())
        hashtag_set.add(item.title())
        hashtag_set.add(item.capitalize())
    
    return frozenset(hashtag_set)

class HashtagReplacer:
    def __init__(self, hashtag_set):
        self._hashtag_set = hashtag_set
        self._used = set()
    
    # XXX! this function is NOT threadsafe. (and NOT NEED be threadsafe).
    def __call__(self, word):
        def replace_func(matchobj):
            word_lower = matchobj.group('word').lower()
            
            if matchobj.group('pre_word').endswith('#'):
                self._used.add(word_lower)
                
                return matchobj.group()
            
            if word_lower in self._hashtag_set and \
                    word_lower not in self._used:
                self._used.add(word_lower)
                
                return '{}#{}{}'.format(
                        matchobj.group('pre_word'),
                        matchobj.group('word'),
                        matchobj.group('post_word'),
                        )
            
            return matchobj.group()
        
        return re.sub(
                r'^(?P<pre_word>\W*?)(?P<word>\w+?)(?P<post_word>\W*?)$',
                replace_func,
                word,
                flags=re.M | re.S,
                )

def create_word_func_factory(word_list):
    hashtag_set = create_hashtag_set(word_list)
    
    def word_func_factory():
        hr = HashtagReplacer(hashtag_set)
        
        return hr
    
    return word_func_factory
