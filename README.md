# 远程桌面 —— Python实现


## pyinstaller 打包命令

```bash
pyinstaller -w -F -p ./ --clean -n "emtDesk" -i "./resources/logo.ico" emtMainWindow.py
```

nuitka 打包命令
```bash
nuitka --onefile --windows-icon-from-ico=emtDesk.ico --enable-plugin=numpy --enable-plugin=pyside6 emtMainWindow.py
```
