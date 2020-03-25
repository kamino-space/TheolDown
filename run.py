import theoldown

if __name__ == '__main__':
    host = 'etcnew.sdut.edu.cn'
    cookie = 'JSESSIONID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    app = theoldown.TheolDown(host, cookie)
    app.run()
    # app.run_from_data_file('path/data.json')
