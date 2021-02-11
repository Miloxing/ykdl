#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
from logging import getLogger
from ykdl.compact import Request, urlopen
from ykdl.util import log
from ykdl.util.wrap import encode_for_wrap
from .html import fake_headers
import traceback
import requests
import time
import shutil
import streamlink

logger = getLogger("downloader")

def get_proxy():
    while True:
        try:
            return requests.get("http://127.0.0.1:5010/get/").json().get("proxy")
        except:
            time.sleep(0.5)

try:
    from concurrent.futures import ThreadPoolExecutor
    MultiThread = True
except:
    MultiThread = False
    logger.warning("failed to import ThreadPoolExecutor!")
    logger.warning("multithread download disabled!")
    logger.warning("please install concurrent.futures from https://github.com/agronholm/pythonfutures !")

def simple_hook(arg1, arg2, arg3,name):
    if arg3 > 0:
        percent = int(arg1 * arg2 * 100 / arg3)
        if percent > 100:
            percent = 100
        sys.stdout.write('\r %3d' % percent + '%')
        sys.stdout.flush()
    else:
        sys.stdout.write('\r'+"\033[K" +name+' -- '+ str(round(arg1 * arg2 / 1048576, 1)) + 'MB')
        sys.stdout.flush()

def streamlink_url(url,name,ext,status,reporthook = simple_hook):
    try:
        print("Download: " + name)
        name = name + '.' + ext
        streams = streamlink.streams(url)
        try:
            stream = ''
            stream = streams['best']
        except:
            print(streams)
        assert stream
        fd = stream.open()
        open_mode = 'ab+'
        readbuffer = 1024*8
        desize = 1024*1024/8
        size = -1
        fs=0
        f = open(name, open_mode)
        while 1:
            try:
                data = fd.read(readbuffer)
                if data:
                    f.write(data)
                else:
                    break
                fs+=1
                if fs % 100 == 0:
                    reporthook(fs, readbuffer, size,name)
                if fs>=desize:
                    f.close()
                    fs = 0
                    sys.stdout.write('\033[K')
                    print(name,'大小达到限制，分割文件')
                    shutil.move(name,'/root/b/')
                    namepart = name.split('-',1)
                    name = time.strftime('%y%m%d_%H%M%S')+"-"+namepart[-1]
                    fs=0
                    f = open(name, open_mode)
            except:
                break
        if os.path.exists(name):
            filesize = os.path.getsize(name)
            if filesize >0 :
                status[0] = 1
    except AssertionError:
        print(name,'no stream')
    except:
        traceback.print_exc()
    finally:
        if 'fd' in locals():
            fd.close()
        if 'f' in locals():
            f.close()
        if os.path.exists(name):
            shutil.move(name,'/root/b/')
    
def save_url(url, name, ext, status, part = None, reporthook = simple_hook):
    if part is None:
        print("Download: " + name)
        name = name + '.' + ext
    else:
        print("Download: " + name + " part %d" % part)
        name = name + '_%d_.' % part + ext
    bs = 1024*8
    size = -1
    read = 0
    blocknum = 0
    open_mode = 'ab+'
    req = Request(url, headers = fake_headers)
    try:
        url = 'http://'+url.split("://")[-1]
        hasproxy=0
        retry = 0
        while True:
            while 1:
                if hasproxy:
                    proxy = {'http':get_proxy()}
                else:
                    proxy = 0
                try:
                    r = requests.get(url,proxies=proxy,stream=True,timeout=(5,8))
                    if r.status_code == 200 or r.status_code == 404:
                        break
                    else:
                        r.close()
                        raise Exception(r.status_code)
                except:
                    hasproxy = 1
                    if retry < 10:
                        retry +=1
                        continue
                    else:
                        break
            reporthook(blocknum, bs, size,name)
            tfp = open(name, open_mode)
            for chunk in r.iter_content(chunk_size=bs):
                if(chunk):
                    tfp.write(chunk)
                    blocknum += 1
                    if blocknum % 100 == 0:
                        reporthook(blocknum, bs, size,name)
                    if(blocknum >= 131072):
                        tfp.close()
                        r.close()
                        print('文件大小达到限制，结束')
                        #os.system('mv "{}" /root/b/'.format(name))
                        shutil.move(name,'/root/b/')
                        namepart = name.split('-',1)
                        name = time.strftime('%y%m%d_%H%M%S')+"-"+namepart[-1]
                        blocknum = 0
                        break
                        #tfp = open(name, open_mode)
                else:
                    print(name,"无 chunk")
                    break
            break
        if os.path.exists(name):
            filesize = os.path.getsize(name)
            if filesize == size:
                if part is None:
                    status[0] = 1
                else:
                    status[part] =1
    except:
        traceback.print_exc()
    finally:
        if "r" in locals():
            r.close()
        if "tfp" in locals():
            tfp.close()
        if os.path.exists(name):
            filesize = os.path.getsize(name)
            if filesize < 1024*600:
                print(name,"大小不足1mb，删除")
                os.remove(name)
            else:
                #os.system('mv "{}" /root/b/'.format(name))
                shutil.move(name,'/root/b/')
    #upload(name)
    
'''    
def upload(name):
    nick = name.split("-")[1]
    os.system("rclone move '{}' milo:milo/b/huya/'{}'".format(name,nick))
    if (not os.path.exists(name)):
        print("%s 上传成功" % name)
'''

def save_urls(urls, name, ext, jobs=1):
    ext = encode_for_wrap(ext)
    status = [0] * len(urls)
    if len(urls) == 1:
        if ext == "mp4":
            streamlink_url(urls[0],name,ext,status)
        save_url(urls[0], name, ext, status)
        if 0 in status:
            logger.error("donwload failed")
        return not 0 in status
    if not MultiThread:
        for no, u in enumerate(urls):
            save_url(u, name, ext, status, part = no)
    else:
        with ThreadPoolExecutor(max_workers=jobs) as worker:
            for no, u in enumerate(urls):
                worker.submit(save_url, u, name, ext, status, part = no)
            worker.shutdown()
    i = 0
    for a in status:
        if a == 0:
            logger.error("downloader failed at part {}".format(i))
        i += 1
    return not 0 in status
