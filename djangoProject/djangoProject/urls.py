from django.contrib import admin
from django.urls import path, include  # 修改：添加 include 函数
from django.views.generic import RedirectView

from ai_select import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('ai_admin/', admin.site.urls),  # 修改：将 admin/ 路径改为 ai_select/admin/
    path('', RedirectView.as_view(url='ai_select/index/', permanent=True)),
    path('ai_select/index/', views.index_view, name='index'),
    path('ai_select/directory/<str:directory_name>/<str:save_list>/', views.directory_detail_view, name='directory_detail'),
    path('ai_select/directory_saved/<str:directory_name>/<str:save_list>/', views.directory_detail_view, name='directory_detail_saved'),
    path('ai_select/get_image_data/', views.get_image_data, name='get_image_data'),
    path('ai_select/save_change/', views.save_change, name='save_change'),
]