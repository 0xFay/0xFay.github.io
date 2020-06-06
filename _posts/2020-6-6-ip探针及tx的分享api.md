# ip探针及tx的分享api

去网上搬了个ip探针- -，没啥好说的，只改了下路径（写码一时爽，改码火葬场...里面好多全是绝对路径，改了一晚上）

原理就是记录来访者的ip信息和ua头，拿去api定位（虽然那个api好像用不了了）

我觉得最有意思的地方是腾讯分享的那个api，超级有意思

去b站随便开个视频找个分享到qq的链接，比如这个：

https://connect.qq.com/widget/shareqq/index.html?url=https%3A%2F%2Fwww.bilibili.com%2Fvideo%2FBV1Wt4y1y7mi%2F%3Fshare_medium%3Dweb%26share_source%3Dqq%26bbid%3D08859F22-D0FA-4282-A3B7-2BE9B814A78853936infoc%26ts%3D1591367881909&desc=【B限%2F剪辑熟肉】文乃的幸福理论%26夏令时记录【物述有栖】 UP主：物述有栖Official&title=【B限%2F剪辑熟肉】文乃的幸福理论%26夏令时记录【物述有栖】&summary=剪辑自5月4日 B限突击练习歌回%0A%0Atwitter：%0Atwitter.com%2FAliceMononobe%0A%0A字幕协力：物述有栖-爱丽丝搬运%0A剪辑：烧鸡%0A时轴：龙行%0A翻译：龙行%0A校对：文乃%0A后期：雪碧（特效轴）%0A封面：天狐公主&pics=http%3A%2F%2Fi0.hdslb.com%2Fbfs%2Farchive%2F1b3b74685fdf6c758e9041af1792866840aa44ef.jpg&flash=&site=&style=201&width=32&height=32

附一个urldecode后的内容：

```
https://connect.qq.com/widget/shareqq/index.html?url=https://www.bilibili.com/video/BV1Wt4y1y7mi/?share_medium=web&share_source=qq&bbid=08859F22-D0FA-4282-A3B7-2BE9B814A78853936infoc&ts=1591367881909&desc=【B限/剪辑熟肉】文乃的幸福理论&夏令时记录【物述有栖】 UP主：物述有栖Official&title=【B限/剪辑熟肉】文乃的幸福理论&夏令时记录【物述有栖】&summary=剪辑自5月4日 B限突击练习歌回

twitter：
twitter.com/AliceMononobe

字幕协力：物述有栖-爱丽丝搬运
剪辑：烧鸡
时轴：龙行
翻译：龙行
校对：文乃
后期：雪碧（特效轴）
封面：天狐公主&pics=http://i0.hdslb.com/bfs/archive/1b3b74685fdf6c758e9041af1792866840aa44ef.jpg&flash=&site=&style=201&width=32&height=32
```

这个链接分为几部分，url为分享的链接，desc是对链接的描述，title是标题，summary是介绍，pics是封面

我们来试试自己构造一个链接康康

https://connect.qq.com/widget/shareqq/index.html?url=http://www.baidu.com&desc=alicefoofoo&title=faydflourite&summary=alicetenshi&pics=http%3A%2F%2Fi2.hdslb.com%2Fbfs%2Farchive%2Ff41c7f9fd7088616fff5405cb10bf4ab8998dd07.jpg&flash=&site=&style=201&width=32&height=32

登录过后选择好友发送：

<img src='https://0xfay.github.io/public/image/225434.jpg'>

打开后不出意料是百度首页。

这个的好处在于它的伪装性更高，你要是直接发个链接过去对方的警惕性比这个估计要高不少。
