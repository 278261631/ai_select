import json
import shutil

from django.contrib.auth.decorators import login_required
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

@login_required
def index_view(request):
    # 获取当前日期和时间
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')

    current_weekday = now.strftime('%A')  # 获取英文星期几
    # 将英文星期几转换为中文
    weekday_map = {
        'Monday': '星期一',
        'Tuesday': '星期二',
        'Wednesday': '星期三',
        'Thursday': '星期四',
        'Friday': '星期五',
        'Saturday': '星期六',
        'Sunday': '星期日'
    }
    current_weekday = weekday_map.get(current_weekday, current_weekday)  # 转换为中文
    # 修改时区显示为GMT+的形式
    current_timezone = now.strftime('%z')  # 获取时区偏移量，例如 +0800
    current_timezone = f"GMT{current_timezone[:3]}:{current_timezone[3:]}"  # 格式化为 GMT+08:00

    # 获取目录列表
    directory_root = settings.DIRECTORY_ROOT
    directories = []
    if os.path.exists(directory_root) and os.path.isdir(directory_root):
        directories = [d for d in os.listdir(directory_root) if os.path.isdir(os.path.join(directory_root, d))]

    # directories 倒序排列
    directories.sort(reverse=True)
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

@login_required
def directory_detail_view(request, directory_name, save_list):
    save_list_bool = (save_list.lower() == 'true')
    directory_root = settings.DIRECTORY_ROOT
    directory_path = os.path.join(directory_root, directory_name)
    # 拼接excel文件路径
    excel_file_path = os.path.join(directory_path, f'saved_{settings.EXCEL_FILE_NAME}')

    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return render(request, '404.html')  # 或者自定义错误页面
    src_excel_file_path = os.path.join(directory_path, f'{settings.EXCEL_FILE_NAME}')
    items = os.listdir(directory_path)
    df = None
    # 读取Excel文件并提取第三列内容
    if os.path.exists(src_excel_file_path):
        if not os.path.exists(excel_file_path):
            print(f"备份文件 {excel_file_path} <- {src_excel_file_path}")
            shutil.copy(src_excel_file_path, excel_file_path)
        else:
            # 对比 src_excel_file_path 和 excel_file_path 的第一列, 如果excel_file_path没有, 则添加整行到excel_file_path
            sync_excel_rows(src_excel_file_path, excel_file_path)

        df_src = pd.read_excel(src_excel_file_path, dtype={'Category': str})
        df_src = df_src.fillna("")
        for row_index, row in df_src.iterrows():
            # 检查row['Category']的类型是不是布尔类型
            if isinstance(row['Category'], bool):
                if not row['Category']:
                    df_src.at[row_index, 'Category'] = "FALSE"
            if row['Category'].lower() == 'false' and row['Category'] != 'FALSE':
                df_src.at[row_index, 'Category'] = "FALSE"
            if row['Category'].lower() == 'true' and row['Category'] != 'TRUE':
                df_src.at[row_index, 'Category'] = "TRUE"
        src_excel_data = df_src.to_dict(orient='records')  # 将DataFrame转换为字典列表

        df = pd.read_excel(excel_file_path, dtype={'Category': str})
        # 替换所有NaN值为空字符串
        # df = df.fillna("{'false': '0.0%', 'line': '0.0%', 'review': '0.0%', 'true': '0.0%'}")
        # df = df.fillna("-")
        df = df.fillna("")
        need_fix_bool = False
        # 循环遍历DataFrame，将Category列的值替换为对应的字符串
        for row_index, row in df.iterrows():
            # 检查row['Category']的类型是不是布尔类型
            if isinstance(row['Category'], bool):
                if not row['Category']:
                    df.at[row_index, 'Category'] = "FALSE"
                    need_fix_bool = True
            if row['Category'].lower() == 'false' and row['Category'] != 'FALSE':
                df.at[row_index, 'Category'] = "FALSE"
                need_fix_bool = True
            if row['Category'].lower() == 'true' and row['Category'] != 'TRUE':
                df.at[row_index, 'Category'] = "TRUE"
                need_fix_bool = True

        if need_fix_bool:
            print(f"需要修复bool类型 {excel_file_path}")
            df['Category'] = df['Category'].astype(str)
            df.to_excel(excel_file_path, index=False)

        excel_data = df.to_dict(orient='records')  # 将DataFrame转换为字典列表

        # #  对比excel_data和src_excel_data, 如果src_excel_data 有 excel_data中没有的项，则添加到excel_data中
        # need_update = False
        # for item in src_excel_data:
        #     i_exists = False
        #     for j_item in excel_data:
        #         if j_item['Filename'] == item['Filename']:
        #             i_exists = True
        #             break
        #     if i_exists:
        #         continue
        #     need_update = True
        #     excel_data.append(item)
        # if need_update:
        #     print(f"更新 {excel_file_path}")
        #     df['Category'] = df['Category'].astype(str)
        #     df.to_excel(excel_file_path, index=False)

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
    for i, item in enumerate(third_column):
        row_edit = False
        if df.__contains__('username'):
            user_name = df.at[i, 'username']
            row_edit = user_name and len(user_name) > 0
        if item in grouped_third_column:
            if save_list_bool:
                if row_edit:
                    grouped_third_column[item] += 1
            else:
                if not row_edit:
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
    if save_list_bool:
        return render(request, 'directory_detail_saved.html', context)
    return render(request, 'directory_detail.html', context)


@csrf_exempt  # 确保可以接收POST请求
@login_required
def get_image_data(request):
    if request.method == 'POST':
        a_img_value = ''
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
                print(f'error : {a_img_value} not found')
                return JsonResponse({'error': f'Image not found {a_img_value}'}, status=404)

            with open(a_img_value, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            return JsonResponse({'image_data': encoded_string})
        except Exception as e:
            print(f'error: {a_img_value}')
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt  # 确保可以接收POST请求
@login_required
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
            excel_file_path = os.path.join(directory_path, f'saved_{settings.EXCEL_FILE_NAME}')
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return render(request, '404.html')  # 或者自定义错误页面

            # 读取Excel文件并提取第三列内容
            if os.path.exists(excel_file_path):
                df = pd.read_excel(excel_file_path, dtype={'Category': str})
                df = df.fillna("")
                print(df.at[row_index, 'Category'])

                fn = df.at[row_index, 'Filename']
                # 转为小写
                old_type_value = df.at[row_index, 'Category']
                old_type_value_path = old_type_value.lower()
                type_value_path = type_value.lower()
                if fn == filename:
                    df.at[row_index, 'Category'] = type_value
                    # 如果没有comment列，则添加该列
                    if 'comment' not in df.columns:
                        df['comment'] = ''
                    df.at[row_index, 'comment'] = comment_txt

                    if 'username' not in df.columns:
                        df['username'] = ''
                    df.at[row_index, 'username'] = request.user.username
                    df['Category'] = df['Category'].astype(str)
                    df.to_excel(excel_file_path, index=False)

                    jpg_file_path = os.path.join(directory_path, old_type_value_path, fn)
                    jpg_move_path = os.path.join(directory_path, type_value_path, fn)
                    # 移动文件
                    if  old_type_value != "UNDETECT":
                        if os.path.exists(jpg_file_path):
                            print(f'Move {jpg_file_path} to {jpg_move_path}')
                            shutil.move(jpg_file_path, jpg_move_path)
                        else:
                            return JsonResponse({'error': f'Image not found {jpg_file_path}'}, status=404)

                    else:
                        print(f'skip Move undetected {jpg_file_path} to {jpg_move_path}')
                else:
                    return JsonResponse({'error': 'filename not match'}, status=400)

            return JsonResponse({'success': 'Changes saved successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def sync_excel_rows(src_excel_file_path, excel_file_path):
    # 读取源文件和目标文件
    src_df = pd.read_excel(src_excel_file_path)
    target_df = pd.read_excel(excel_file_path)

    # 提取第一列数据（假设列名相同）
    src_ids = set(src_df.iloc[:, 0])  # 第一列的所有值
    target_ids = set(target_df.iloc[:, 0])

    # 找出源文件有但目标文件没有的ID
    missing_ids = src_ids - target_ids

    # 筛选需要新增的行
    new_rows = src_df[src_df.iloc[:, 0].isin(missing_ids)]

    if not new_rows.empty:
        # 追加新行并保存
        updated_df = pd.concat([target_df, new_rows], ignore_index=True)
        updated_df['Category'] = updated_df['Category'].astype(str)
        updated_df.to_excel(excel_file_path, index=False)
        print(f"{excel_file_path}  新增了 {len(new_rows)} 行数据")
        return f"新增了 {len(new_rows)} 行数据"
    return "没有需要新增的数据"