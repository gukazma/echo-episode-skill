Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "D:\lanview"
sh.Run """D:\OpenMontage\.venv\Scripts\pythonw.exe"" ""D:\lanview\server.py""", 0, False
