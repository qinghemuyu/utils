@echo off
chcp 65001 >nul
echo 正在打包程序...
pyinstaller --onefile  --name ColorHit color_detector.py
echo 打包完成！程序位于dist文件夹中
pause