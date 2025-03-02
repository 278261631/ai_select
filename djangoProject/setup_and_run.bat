@echo off
REM 创建虚拟环境
C:\Python\Python310\python.exe  -m venv venv_ai_select

REM 激活虚拟环境
call venv_ai_select\Scripts\activate

cd djangoProject

REM 安装依赖
pip install -r requirements.txt

REM 启动 Django 项目
python manage.py runserver 0.0.0.0:18000