# THEOLDOWN
用于批量下载网络教学平台(优慕课)的教学资源

## 运行环境
python3 requests beautifulsoup4

## 使用方法
1 获取代码并安装依赖
```bash
git clone https://github.com/kamino-space/TheolDown.git
cd TheolDown
pip install -r requirements.txt
```
2 获取cookie  
打开浏览器进入网络教学平台，登录你的账号，获取cookie  
获取cookie方法参考 [怎样获取cookie](https://jingyan.baidu.com/article/5d368d1ea6c6e33f60c057ef.html)  
![example](https://static.isdut.cn/ii/images/2019/05/20/70fbe1474a027cfc4b4cd096f7f402bb.png)  
3 修改run.py，填入host和cookie
```bash
vi run.py
```
4 开始下载
```bash
python run.py
```
5 完成  

## 下载方法
- 自动下载 app.run()
- 从data.json文件下载 app.run_from_data_file('path/data.json')

## 注意事项
仅能下载设置为可下载的文件资源  
请按照学校的要求使用下载的文件  

## LICENSE
MIT