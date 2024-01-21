对于Wallpaper的bilibili响应壁纸无法通过小葫芦BGM控制台获取歌词显示的第三方api

```
python3 小葫芦bgm代替.py
```

打包好的exe暂时有bug无法运行

请自行安装python3.8以上并执行
```
pip install -r requirements.txt

```
安装依赖运行，如有bug请提交

若无法运行请尝试使用管理员身份或关闭windows防火墙

如果觉得有用请给个星，谢谢

阶段性问题：
1.首次运行时需重新播放一首歌，否则无法识别
2.暂停播放时会继续输出内容
3.无法隐藏到收纳栏中最小化
4.似乎无法识别出网易云音乐自动切换的音乐！！！

如果需要开机自启动可以通过cmd执行：shell:start
定位到开机自启动目录，然后编写一个startup.bat
内容如下：
python3 路径到小葫芦bgm代替.py

若执行python3 路径到小葫芦bgm代替.py  无输出请尝试：python 路径到小葫芦bgm代替.py

Bilibili video:https://www.bilibili.com/video/BV1Yb4y1N7X7/
