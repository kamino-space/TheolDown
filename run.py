import theoldown

if __name__ == '__main__':
    host = 'xxx.xxxx.edu.cn'
    cookie = 'DWRSESSIONID=xxxxxxxxxxx;JSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxx;'
    app = theoldown.TheolDown(host, cookie)
    app.run()
    # app.run_from_data_file('path/data.json')
