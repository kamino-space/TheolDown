import os
import requests
import json
import time
import re

from bs4 import BeautifulSoup


class TheolDown(object):
    data = {
        'user': None,
        'runat': None,
        'data': {
            'resource': {}
        }
    }

    def __init__(self, host, cookie):
        """
        初始化，设置cookie
        :param cookie:
        """
        self.cookie = cookie
        self.host = host
        self.data['runat'] = int(time.time())
        self.urls = {
            'welcome': 'http://%s/meol/welcomepage/student/index.jsp' % self.host,
            'lessons': 'http://%s/meol/lesson/blen.student.lesson.list.jsp' % self.host,
            'root': lambda lid: 'http://%s/meol/common/script/listview.jsp?lid=%s&folderid=0' % (self.host, lid),
            'url': lambda fileid, resid,
                          lid: 'http://%s/meol/common/script/download.jsp?fileid=%s&resid=%s&lid=%s' % (
                self.host, fileid, resid, lid),
        }
        self.path = os.path.dirname(__file__) + '/'
        self.save = self.path + 'download/%s/' % self.data['runat']
        self.session = requests.session()
        self.session.headers.update({
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "max-age=0",
            'Connection': "keep-alive",
            'Cookie': self.cookie,
            'Host': self.host,
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
            'cache-control': "no-cache",
        })
        self._check_login()
        if not os.path.exists(self.save):
            os.mkdir(self.save)

    def _check_login(self):
        """
        判断登录状态
        :return:
        """
        try:
            response = self.session.get(self.urls['welcome'])
            if response.status_code != 200:
                raise Exception('服务器错误 %s' % response.status_code)
            content = response.content.decode('gbk')
            if re.search('用户身份错误，请重新登录！', content) is not None:
                raise Exception('用户身份错误，请重新登录！')
            soup = BeautifulSoup(content)
            self.data['user'] = soup.findAll('li')[0].get_text().strip('姓名：')
            print('%s 登录成功' % self.data['user'])
        except Exception as e:
            print(e)
            exit(0)

    def get_lesson_list(self):
        """
        获取课程列表
        :return:
        """
        print('获取课程列表')
        response = self.session.get(self.urls['lessons'])
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        self.lessons = []
        soup = BeautifulSoup(response.content.decode('gbk'))
        l = soup.findAll('td')
        for i in range(len(l) // 5):
            le = {
                'name': l[i * 5 + 0].get_text().strip(),
                'school': l[i * 5 + 1].get_text().strip(),
                'teacher': l[i * 5 + 2].get_text().strip(),
                'lid': l[i * 5 + 0].a.get('href').replace('init_course.jsp?lid=', '')
            }
            self.lessons.append(le)
        print('获取课程列表成功 %s' % self.lessons)

    def get_resource_list(self, lid):
        """
        获取资源列表
        :param lid:
        :return:
        """
        print('获取资源列表 LID:%s' % lid)
        resource = {}
        response = self.session.get(self.urls['root'](lid))
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        soup = BeautifulSoup(response.content.decode('gbk'))
        l = soup.findAll('td')
        for i in range(len(l) // 2):
            try:
                name = l[i * 2 + 0].get_text().strip()
                href = l[i * 2 + 0].a.get('href')
                if re.search('listview.jsp', href) is not None:
                    resource[name] = self._scan_dir(href)
                elif re.search('download_preview.jsp', href) is not None:
                    attr = dict([l.split("=", 1) for l in href.strip('preview/download_preview.jsp?').split("&")])
                    resource[name] = self.urls['url'](attr['fileid'], attr['resid'], attr['lid'])
                elif re.search('onlinepreview.jsp', href) is not None:
                    resource[name] = False
                else:
                    pass
            except Exception as e:
                pass
            finally:
                time.sleep(1)
        print('成功')
        return resource

    def _scan_dir(self, url):
        """
        遍历文件夹
        :param url:
        :return:
        """
        print('扫描目录 %s' % url)
        response = self.session.get('http://%s/meol/common/script/%s' % (self.host, url))
        resource = {}
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        soup = BeautifulSoup(response.content.decode('gbk'))
        l = soup.findAll('td')
        for i in range(len(l) // 2):
            try:
                name = l[i * 2 + 0].get_text().strip()
                href = l[i * 2 + 0].a.get('href')
                if re.search('listview.jsp', href) is not None:
                    resource[name] = self._scan_dir(href)
                elif re.search('download_preview.jsp', href) is not None:
                    attr = dict([l.split("=", 1) for l in href.strip('preview/download_preview.jsp?').split("&")])
                    resource[name] = self.urls['url'](attr['fileid'], attr['resid'], attr['lid'])
                elif re.search('onlinepreview.jsp', href) is not None:
                    resource[name] = False
                else:
                    pass
            except Exception as e:
                pass
            finally:
                time.sleep(1)
        return resource

    def get_all_resource(self):
        """
        获取所有文件列表
        :return:
        """
        print(self.lessons)
        for lesson in self.lessons:
            print(lesson)
            print(lesson['name'])
            self.data['resource'][lesson['name']] = self.get_resource_list(lesson['lid'])

    def run(self):
        """
        开始下载
        :return:
        """
        try:
            self.get_lesson_list()
            self.get_all_resource()
            print(self.data)
        except Exception as e:
            print(e)
        finally:
            with open(self.save + 'data.json', 'w') as f:
                f.write(json.dumps(self.data))
