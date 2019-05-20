import os
import requests
import json
import time
import re
import queue
# import threading  # 暂时不使用多线程下载

from bs4 import BeautifulSoup


class TheolDown(object):
    data = {
        'user': '',
        'runat': 0,
        'save': '',
        'resource': {}
    }

    def __init__(self, host, cookie):
        """
        初始化，设置cookie
        :param cookie:
        """
        self._start_at = int(time.time())
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
        self.dlist = queue.Queue(10000)
        self._check_login()

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
            Log.info('%s 登录成功' % self.data['user'])
        except Exception as e:
            Log.error(str(e))
            exit(0)

    def get_lesson_list(self):
        """
        获取课程列表
        :return:
        """
        Log.info('获取课程列表')
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
        self.data['lessons'] = self.lessons.copy()
        Log.info('获取课程列表成功 %s' % self.lessons)

    def get_resource_list(self, lid):
        """
        获取资源列表
        :param lid:
        :return:
        """
        Log.info('获取资源列表 LID:%s' % lid)
        resource = {}
        response = self.session.get(self.urls['root'](lid))
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        soup = BeautifulSoup(response.content.decode('gbk'))
        lr = soup.findAll('tr')
        for i in range(1, len(lr)):
            try:
                name = lr[i].td.get_text().strip()
                href = lr[i].a.get('href')
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
                Log.warning(str(e))
            finally:
                time.sleep(1)
        Log.info('成功')
        return resource

    def _scan_dir(self, url):
        """
        遍历文件夹
        :param url:
        :return:
        """
        Log.info('扫描目录 %s' % url)
        response = self.session.get('http://%s/meol/common/script/%s' % (self.host, url))
        resource = {}
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        soup = BeautifulSoup(response.content.decode('gbk'))
        lr = soup.findAll('tr')
        for i in range(1, len(lr)):
            try:
                name = lr[i].td.get_text().strip()
                href = lr[i].a.get('href')
                if re.search('listview.jsp', href) is not None:
                    resource[name] = self._scan_dir(href)
                elif re.search('download_preview.jsp', href) is not None:
                    attr = dict([l.split("=", 1) for l in href.strip('preview/download_preview.jsp?').split("&")])
                    resource[name] = self.urls['url'](attr['fileid'], attr['resid'], attr['lid'])
                elif re.search('onlinepreview.jsp', href) is not None:
                    resource[name] = False
                else:
                    pass
            except Exception:
                pass
            finally:
                time.sleep(1)
        Log.info('完成')
        return resource

    def get_resource_all(self):
        """
        获取所有文件列表
        :return:
        """
        for lesson in self.lessons:
            Log.info('获取资源列表', lesson['name'])
            self.data['resource'][lesson['name']] = self.get_resource_list(lesson['lid'])

    def make_dirs(self):
        """
        创建所有的文件夹
        :return:
        """
        self.data['save'] = self.save
        if not os.path.exists(self.save):
            os.mkdir(self.save)
        self._make_dir(self.save, self.data['resource'])

    def _make_dir(self, parent, child):
        """
        循环创建子目录
        :param j:
        :return:
        """
        if child is {}:
            return

        for key, value in child.items():
            if value is False:
                continue
            path = parent + key + '/'
            if isinstance(value, str):
                self.dlist.put_nowait({
                    'filename': key,
                    'filepath': parent,
                    'url': value
                })
                continue
            try:
                Log.info('创建文件夹', path)
                if not os.path.exists(path):
                    os.mkdir(path)
                self._make_dir(path, value)
            except Exception as e:
                Log.error('创建文件夹错误', key, str(e))

    def download(self, url, path, name):
        """
        下载文件到指定文件夹
        :param url:
        :param path:
        :param name:
        :return:
        """
        Log.info('下载', name)
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception('服务器错误 %s' % response.status_code)
        if 'Content-Disposition' in response.headers.keys():
            extname = re.search(r'\.(.*)', response.headers['Content-Disposition']).group(0).strip('"')
        elif response.headers['Content-Type'] == 'application/x-shockwave-flash':
            extname = '.swf'
        else:
            if re.search('validCode', response.content.decode('gbk')):
                raise Exception('需要验证码')
            else:
                raise Exception('谜之错误')
        with open(path + name + extname, 'wb') as f:
            f.write(response.content)
        Log.info('成功', name + extname)

    def download_all(self):
        """
        下载全部文件
        :return:
        """
        Log.info('开始下载')
        while not self.dlist.empty():
            try:
                file = self.dlist.get_nowait()
                self.download(file['url'], file['filepath'], file['filename'])
            except Exception as e:
                Log.error('错误', str(e))
            finally:
                time.sleep(0.1)
        print('下载完成')

    def run(self):
        """
        开始下载
        :return:
        """
        try:
            self.get_lesson_list()
            self.get_resource_all()
            self.make_dirs()
            self.download_all()
        except Exception as e:
            Log.error('错误', str(e))
        finally:
            if not os.path.exists(self.save):
                os.mkdir(self.save)
            with open(self.save + 'data.json', 'w') as f:
                f.write(json.dumps(self.data))
            self._end_at = int(time.time())
            Log.info('用时%s秒', self._end_at - self._start_at)

    def run_from_data_file(self, path):
        """
        从data.json文件启动
        :param path:
        :return:
        """
        Log.info('开始运行')
        try:
            with open(path, 'r') as f:
                self.data = json.loads(f.read())
                self.save = self.data['save']
            self.make_dirs()
            self.download_all()
        except Exception as e:
            Log.error('错误', str(e))


class Log(object):
    @staticmethod
    def add(msg, level):
        """
        输出保存日志
        :param msg:
        :param level:
        :return:
        """
        text = '[{time}] [{level}]  {msg}'.format(
            time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            level=level,
            msg=msg
        )
        print(text)
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(text + '\r')

    @staticmethod
    def info(*args):
        """
        INFO
        :param args:
        :return:
        """
        Log.add(' '.join(args), 'INFO')

    @staticmethod
    def warning(*args):
        """
        INFO
        :param args:
        :return:
        """
        Log.add(' '.join(args), 'WARNING')

    @staticmethod
    def error(*args):
        """
        INFO
        :param args:
        :return:
        """
        Log.add(' '.join(args), 'ERROR')
