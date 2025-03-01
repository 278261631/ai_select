import json

from django.shortcuts import render, get_object_or_404
from django.conf import settings
from datetime import datetime
import pytz
import os
import pandas as pd  # 添加pandas库用于读取Excel文件
from django.http import JsonResponse
import base64

from django.views.decorators.csrf import csrf_exempt


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
        # 替换所有NaN值为空字符串
        # df = df.fillna("{'false': '0.0%', 'line': '0.0%', 'review': '0.0%', 'true': '0.0%'}")
        # df = df.fillna("-")
        df = df.fillna("")
        excel_data = df.to_dict(orient='records')  # 将DataFrame转换为字典列表
        # 添加序列号
        for i, item in enumerate(excel_data, start=1):
            item['row_number'] = i
        if df.shape[1] >= 3:  # 确保Excel文件有至少三列
            third_column = df.iloc[:, 2].tolist()
        else:
            third_column = []
    else:
        third_column = []
        excel_data = []

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
        'excel_data': excel_data,  # 添加Excel数据到context
    }
    return render(request, 'directory_detail.html', context)


@csrf_exempt  # 确保可以接收POST请求
def get_image_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            a_img_value = data.get('a_img_value')
            a_img_value = a_img_value.replace('\\\\', '/').replace('\\', '/')

            # 查找a_img_value 中 字符"baseline"的位置并删除 之前的部分
            a_img_value = a_img_value[a_img_value.find("baseline") + len("baseline") + 1:]
            # 拼接新的路径
            a_img_value = os.path.join(settings.BASELINE_ROOT, a_img_value)
            print(a_img_value)

            if not os.path.exists(a_img_value):
                return JsonResponse({'error': 'Image not found'}, status=404)

            with open(a_img_value, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            return JsonResponse({'image_data': encoded_string})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt  # 确保可以接收POST请求
def save_change(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            filename = data.get('row_filename')
            row_index = data.get('row_index')
            type_value = data.get('type_value')
            comment_txt = data.get('comment_txt')
            directory_name = data.get('directory_name')

            directory_root = settings.DIRECTORY_ROOT
            directory_path = os.path.join(directory_root, directory_name)
            excel_file_path = os.path.join(directory_path, settings.EXCEL_FILE_NAME)
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return render(request, '404.html')  # 或者自定义错误页面

            # 读取Excel文件并提取第三列内容
            if os.path.exists(excel_file_path):
                df = pd.read_excel(excel_file_path)
                df = df.fillna("-")

                fn = df.at[row_index, 'Filename']
                if fn == filename:
                    df.at[row_index, 'Category'] = type_value
                    # 如果没有Category列，则添加该列
                    if 'comment' not in df.columns:
                        df['comment'] = ''
                    df.at[row_index, 'comment'] = comment_txt
                    df.to_excel(excel_file_path, index=False)
                else:
                    return JsonResponse({'error': 'filename not match'}, status=400)

            return JsonResponse({'success': 'Changes saved successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
