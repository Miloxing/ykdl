#!/usr/bin/env python

from ..util.html import get_content
from ..embedextractor import EmbedExtractor
from ..util.match import match1

class Tudou(EmbedExtractor):
    name = "土豆 (tudou)"

    def prepare(self, **kwargs):
        assert self.url

        html = get_content(self.url)
        self.title = match1(html, '<title>([^<]+)')
        vcode = match1(html, 'vcode\s*[:=]\s*\'([^\']+)\'')
        if vcode:
            self.video_info.append(('youku', vcode))
        else:
            vid = match1(html, 'iid\s*[:=]\s*(\d+)')
            if vid:
                self.video_info.append(('tdorig', vid))

    def parse_plist(self):
        html = get_content(self.url)
        lcode = match1(html, "lcode:\s*'([^']+)'")
        plist_info = json.loads(get_content('http://www.tudou.com/crp/plist.action?lcode=' + lcode))
        return ([(item['kw'], item['iid']) for item in plist_info['items']])

    def download_playlist_by_url(self, url, param, **kwargs):
        exit(0)
        self.url = url
        videos = self.parse_plist()
        for i, (title, id) in enumerate(videos):
            print('Processing %s of %s videos...' % (i + 1, len(videos)))
            self.download_by_vid(id, param, title=title, **kwargs)

site = Tudou()
download = site.download
download_playlist = site.download_playlist_by_url
