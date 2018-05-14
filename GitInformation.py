#!/usr/bin/env python
# coding:utf-8
#
#GitHub信息泄漏收集
# __author__="Jaqen"
#

import lib.requests as requests
from lib.termcolor import colored
from github import Github, GithubException
import threading
import Queue
import time
import sys
import re
import logging
import signal
import json
import xlwt
from lib.config import (
    GithubToken, PerPageLimit, THREAD_COUNT, InformationRegex, TIMEOUT
)

def KeyboardInterrupt(signum,frame):
    print '[ERROR] user quit'
    sys.exit(0)

signal.signal(signal.SIGINT,KeyboardInterrupt)
signal.signal(signal.SIGTERM,KeyboardInterrupt)
logging.basicConfig(level=logging.WARNING,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s <%(message)s>',
                filename='run.log',
                filemode='w')
GitUrlList = []
RESULTS = []
lock = threading.Lock()
#信息泄漏项目获取
def requestGitHubAPI(PageNumQueue):
    while not PageNumQueue.empty():
        i = PageNumQueue.get()
        GithubAPI = "https://api.github.com/search/code?sort=updated&order=desc&page=%d&per_page=%s&q="%(i, PerPageLimit)
        headers ={"Authorization":"token "+GithubToken}
        try:
            resp = requests.get(GithubAPI+keyword, headers=headers, timeout=TIMEOUT)
            print "正在爬取第%s页"%i
        except Exception,e:
            logging.error(e)
            continue
        if resp.status_code == 200:
            try:
                GitSource = json.loads(resp.content)
                for i in xrange(len(GitSource['items'])):
                    GitUrlList.append(GitSource['items'][i]["html_url"])
            except Exception,e:
                logging.error(e)
#敏感信息匹配
def Regex(GitUrlListQueue):
    while not GitUrlListQueue.empty():
        GitUrl = GitUrlListQueue.get()
        try:
            resp = requests.get(GitUrl, timeout=10)
        except Exception,e:
            logging.error(e)
            continue
        if resp.status_code == 200:
            try:
                lock.acquire()
                Remix("\n<repos>",GitUrl)
                for i in InformationRegex:
                    try:
                        text = resp.text.lower()
                        text = text.replace('&quot;','"')
                        text = text.replace('&amp;','&')
                        text = text.replace('&lt;','<')
                        text = text.replace('&gt;','>')
                        text = text.replace('&nbsp;',' ')
                        result = re.findall(InformationRegex[i],text)
                        if result:
                            if i == "title":
                                for j in result:
                                    if "github" in j or j is None:
                                        result.remove(j)
                                    else:
                                        Remix(i, j)
                            elif i == "domain":
                                for j in result:
                                    if keyword in j:
                                        Remix(i, j)
                                    else:
                                        result.remove(j)
                            elif i == "root":
                                for j in result:
                                    if "root_id" in j or "root_nwo" in j:
                                        result.remove(j)
                                    else:
                                        Remix(i, j)
                            elif i == "mail":
                                for j in result:
                                    if keyword not in j:
                                        result.remove(j)
                                    else:
                                        Remix(i, j)
                            elif i == "keyword":
                                for j in result:
                                    if "/src/main/" in j:
                                        result.remove(j)
                                    else:
                                        Remix(i, j)
                            else:
                                for j in result:
                                    Remix(i, j)
                    except Exception,e:
                        logging.error(e)
                        lock.release()
                        continue
                lock.release()
            except Exception,e:
                logging.error(e)

def Remix(i, result):
    if result not in RESULTS:
        RESULTS.append(result)
        if i == "\n<repos>":
            print colored(i+" >>>> "+result+"\n", color='green')
        else:
            print colored(i+" >>>> "+result, color='yellow')
def main(keyword):
    global GitUrlList
    GithubAPI = "https://api.github.com/search/code?sort=updated&order=desc&per_page=%s&q="%PerPageLimit
    headers ={"Authorization":"token "+GithubToken}
    try:
        resp = requests.get(GithubAPI+keyword, headers=headers, timeout=TIMEOUT)
    except Exception,e:
        logging.error(e)
        print '[ERROR] GithubAPI RISE ERROR'
        sys.exit(0)
    if resp.status_code == 200:
        try:
            InformationRegex["keyword"] = "([^<|>|\"|:]{0,100}%s[^<|>|\"|:]{0,100})"%keyword
            GitSource = json.loads(resp.content)
            total = GitSource["total_count"]
            PageNum = (total//PerPageLimit)+1
            PageNumQueue = Queue.Queue()
            for i in xrange(PageNum):
                PageNumQueue.put(i)
            threads = []
            for i in xrange(THREAD_COUNT):
                t = threading.Thread(target=requestGitHubAPI,args=(PageNumQueue,))
                t.setDaemon(True)
                threads.append(t)
            [t.start() for t in threads]
            while 1:
                alive = False
                for i in range(THREAD_COUNT):
                    alive = alive or threads[i].isAlive()#响应Ctrl+C
                if not alive:
                    break

            GitUrlList = list(set(GitUrlList))
            GitUrlListQueue = Queue.Queue()
            for i in GitUrlList:
                GitUrlListQueue.put(i)
            threads = []
            for i in xrange(THREAD_COUNT):
                t = threading.Thread(target=Regex,args=(GitUrlListQueue,))
                t.setDaemon(True)
                threads.append(t)
            [t.start() for t in threads]
            while 1:
                alive = False
                for i in range(THREAD_COUNT):
                    alive = alive or threads[i].isAlive()#响应Ctrl+C
                if not alive:
                    break

        except Exception,e:
            logging.error(e)
    else:
        print "[ERROR] 确认是否填入GithubAPI的token "
if len(sys.argv) == 2:
    keyword = sys.argv[1]
    if ',' in keyword:
        for i in keyword.split(','):
            main(i)
    else:
        main(keyword)

else:
    print "\nusage: python GitInfomation.py keyword,keyword\n*/lib/config.py 是配置文件，请先加入GithubAPI的token\n"
