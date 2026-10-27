Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = folder
If Not fso.FolderExists(folder & "\logs") Then fso.CreateFolder(folder & "\logs")

sh.Run "cmd /c python -m streamlit run dashboard_streamlit.py --server.headless true > logs\dashboard.log 2>&1", 0, False
WScript.Sleep 8000
sh.Run "http://localhost:8501"
WScript.Sleep 6000
sh.Run "cmd /c python -u replay_real_data.py > logs\replay.log 2>&1", 0, False