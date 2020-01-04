import theoldown

if __name__ == '__main__':
    host = '211.64.28.63'
    cookie = 'JSESSIONID=EA4348ED730D5E3514466F4172F69B65.TM1; DWRSESSIONID=3U7tDH9A$LCGZ6VoOeygpIjQCZm'
    app = theoldown.TheolDown(host, cookie)
    app.run()
    # app.run_from_data_file('path/data.json')
