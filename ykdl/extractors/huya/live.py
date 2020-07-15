#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ykdl.extractor import VideoExtractor
from ykdl.videoinfo import VideoInfo
from ykdl.util.html import get_content, add_header
from ykdl.util.match import match1, matchall
from ykdl.compact import unescape#新添加


import json
import random
import time,re


class HuyaLive(VideoExtractor):
    name = u"Huya Live (虎牙直播)"

    def prepare(self):
        info = VideoInfo(self.name)

        html  = get_content(self.url)

        json_stream = match1(html, '"stream": "([a-zA-Z0-9+=/]+)"')
        assert json_stream, "live video is offline"
        data = json.loads(base64.b64decode(json_stream).decode())
        assert data['status'] == 200, data['msg']

        room_info = data['data'][0]['gameLiveInfo']
        intro=room_info['introduction']
        rstr = r"[\/\\\:\*\?\"\<\>\|\- ]"
        info.title = re.sub(rstr,"_",intro)
        nick = room_info['nick']
        info.artist = re.sub(rstr,"_",nick)

        stream_info = random.choice(data['data'][0]['gameStreamInfoList'])
        sStreamName = stream_info['sStreamName']
        
        def link_urls():
            for sType in ('flv', 'hls'):
                sType = sType.title()
                sUrl = stream_info['s{}Url'.format(sType)]
                sUrlSuffix = stream_info['s{}UrlSuffix'.format(sType)]
                sAntiCode = stream_info['s{}AntiCode'.format(sType)]
                yield u'{}/{}.{}?{}'.format(sUrl, sStreamName, sUrlSuffix, sAntiCode)

        info.stream_types.append("current")
        info.streams["current"] = {
            'container': 'flv',
            'video_profile': 'current',
            'src': [unescape(url) for url in link_urls()],
            'size' : float('inf')
        }
        return info
    
site = HuyaLive()
