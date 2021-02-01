import win32com.client
h = win32com.client.Dispatch('WinHTTP.WinHTTPRequest.5.1')
url = 'http://127.0.0.1:5000'
h.SetAutoLogonPolicy(0)
h.Open('GET', url, False)
h.Send()