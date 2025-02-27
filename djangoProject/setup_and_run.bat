@echo off
REM 创建虚拟环境
python -m venv venv

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
pip install -r requirements.txt

REM 启动 Django 项目
python manage.py runserver