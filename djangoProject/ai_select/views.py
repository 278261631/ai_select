from django.shortcuts import render, get_object_or_404
from django.conf import settings
from datetime import datetime
import pytz
import os
import pandas as pd  # 添加pandas库用于读取Excel文件

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%Y%m%d')
        return True
    except ValueError:
        return False

def index_view(request):
    # 获取当前日期和时间
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')
    current_weekday = now.strftime('%A')
    current_timezone = now.tzinfo.tzname(now)

    # 获取目录列表
    directory_root = settings.DIRECTORY_ROOT
    directories = []
    if os.path.exists(directory_root) and os.path.isdir(directory_root):
        directories = [d for d in os.listdir(directory_root) if os.path.isdir(os.path.join(directory_root, d))]

    # 标记每个目录是否为日期格式，并添加格式化后的日期字符串
    directories_with_date_flag = []
    for d in directories:
        is_date = is_valid_date(d)
        formatted_date = d if not is_date else datetime.strptime(d, '%Y%m%d').strftime('%Y-%m-%d')
        directories_with_date_flag.append((d, is_date, formatted_date))
    print(directories_with_date_flag)

    context = {
        'user': request.user,
        'current_date': current_date,
        'current_time': current_time,
        'current_weekday': current_weekday,
        'current_timezone': current_timezone,
        'directories': directories_with_date_flag if request.user.is_authenticated else [],
    }
    return render(request, 'index.html', context)

def directory_detail_view(request, directory_name):
    directory_root = settings.DIRECTORY_ROOT
    directory_path = os.path.join(directory_root, directory_name)
    # 拼接excel文件路径
    excel_file_path = os.path.join(directory_path, settings.EXCEL_FILE_NAME)

    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return render(request, '404.html')  # 或者自定义错误页面
    
    items = os.listdir(directory_path)

    # 读取Excel文件并提取第三列内容
    if os.path.exists(excel_file_path):
        df = pd.read_excel(excel_file_path)
        if df.shape[1] >= 3:  # 确保Excel文件有至少三列
            third_column = df.iloc[:, 2].tolist()
        else:
            third_column = []
    else:
        third_column = []

    # 第三列的内容需要分组
    # 初始化 内容 REVIEW   FALSE   UNDETECT   TRUE   LINE
    grouped_third_column = {
        'REVIEW': 0,
        'FALSE': 0,
        'UNDETECT': 0,
        'TRUE': 0,
        'LINE': 0,
    }
    for item in third_column:
        if item in grouped_third_column:
            #
            grouped_third_column[item] += 1
        else:
            grouped_third_column[item] = 1
    print(grouped_third_column)
    context = {
        'directory_name': directory_name,
        'items': items,
        'third_column': grouped_third_column,  # 添加第三列内容到context
    }
    return render(request, 'directory_detail.html', context)