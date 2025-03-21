Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\EngrKurt\PycharmProjects\yolov5" ' Change this to your project path

' Activate the virtual environment
WshShell.Run "cmd.exe /k ""C:\Users\EngrKurt\PycharmProjects\yolov5\.venv\Scripts\activate.bat"" && python app.py", 0, False
