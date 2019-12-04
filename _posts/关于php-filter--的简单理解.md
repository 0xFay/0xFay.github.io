# 关于php:filter//的简单理解

标签（空格分隔）： 2019/12/1 Fay_D_Flourite
---

    今天稍微看了一点php:filter//协议的相关内容，之前虽然也用过，不过也只是照搬而已，今天就做了个大致的总结浏览。

首先，这个协议是php的**独有协议**，用来作为中间流处理其他流。

格式如下：
php://filter/read=<筛选列表>|<筛选列表>/resource=<要过滤的数据流>

有如下参数:

1. **必须**  resource=xxxxx 用于指定目标
2. **可选**  read=xxxxx  设定过滤器
3. **可选**  write=xxxxx  设定过滤器
如没有read或者write的话会自动判断是读或者是写

这里列出一点常用的过滤器：

 - string.rot13 对字符串执行ROT13转换
 - string.toupper转换为大写
 - string.tolower 转换为小写
 - string.strip_tags去除html和php标记
 - convert.base64-encode base64编码
 - convert.base64-decode base64解码
 - ......
 最常用的还是base64进行过滤

主要的用途还是在读文件时对文件进行过滤，其余的功能和打开一个文件应该没有太大差异。


