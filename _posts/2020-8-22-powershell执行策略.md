# powershell 执行策略

来自出题的时候碰到的一点问题。。记录一下

# 执行策略一览

参考自:https://blog.csdn.net/Jeffxu_lib/article/details/84710386

1. Restricted

win8 ，win10的默认执行策略为“Restricted”。在此策略下：

- 允许单独的命令，但不会运行脚本。
- 阻止所有脚本文件的运行。包括格式设置文件和配置文件 (.ps1xml)、模块脚本文件 (.psm1) 和 Windows PowerShell 配置文件 (.ps1)。

2. AllSigned

- 脚本可以运行。
- 要求所有脚本和配置文件都由受信任的发布者签名，包括在本地计算机上编写的脚本。
- 会在运行来自某类发布者（即你尚未归类为受信任或不受信任的发布者）的脚本之前提示你。
- 存在运行已签名但却是恶意的脚本的风险。

3. REMOTESIGNED

- 脚本可以运行。
- 要求从 Internet 下载的脚本和配置文件（包括电子邮件和即时消息程序）具有受信任的发布者的数字签名。
- 不要求你在本地计算机上编写的脚本（不是从 Internet 下载的）具有数字签名。
- 如果脚本已被取消阻止（比如通过使用 Unblock-File cmdlet），则运行从 Internet 下载但未签名的脚本。
- 存在运行来自 Internet 之外的未签名脚本和已签名但却是恶意的脚本的风险。

4. UNRESTRICTED

- 未签名的脚本可以运行。（这存在运行恶意脚本的风险。）
- 在运行从 Internet 下载的脚本和配置文件之前提醒用户。

5. BYPASS

- 不阻止任何内容，并且没有任何警告或提示。
- 该执行策略旨在用于后述配置：在其中 Windows PowerShell 被内置于一个更大的应用程序中，或者在其中 Windows PowerShell 是具有其自己安全模式的程序的基础

6. UNDEFINED

- 当前作用域中未设置执行策略。
- 如果所有作用域中的执行策略都是 Undefined，则有效的执行策略是 Restricted，它是默认执行策略。
- 注意：在不区分通用命名约定 (UNC) 路径和 Internet 路径的系统上，可能不允许使用 RemoteSigned 执行策略运行由 UNC 路径标识的脚本

# 问题所在

在默认的restricted下无法执行所有脚本

所以题目里的ps1脚本在拿到后直接执行会报错...需要管理员权限改变执行策略，如下

`set-executionpolicy -executionpolicy 想改变的策略组`

可通过`get-executionpolicy`查看当前的执行组策略

这里还有一点是，虽然无法执行脚本只能执行单行指令，但是通过下载的方式执行脚本其实是可以的，他实际上相当于在命令行执行下载的脚本内容，而不是直接执行脚本。

另外，用键盘开启管理员权限cmd，只需要win键输入cmd，按ctrl + shift + enter后就会提示是否管理员权限开启，按左方向键后enter就行，这适用于badusb。




