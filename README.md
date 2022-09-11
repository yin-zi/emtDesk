pyinstaller 打包命令
pyinstaller --name="emtDesk" --windowed --icon="emtDesk.ico" -F emtMainWindow.py
nuitka 打包命令
nuitka --onefile --windows-icon-from-ico=emtDesk.ico --enable-plugin=numpy --enable-plugin=pyside6 emtMainWindow.py