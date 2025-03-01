from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from ai_select import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='ai_select/', permanent=True)),
    path('ai_select/', views.index_view, name='index'),
    path('ai_select/directory/<str:directory_name>/', views.directory_detail_view, name='directory_detail'),
    path('ai_select/get_image_data/', views.get_image_data, name='get_image_data'),
    path('ai_select/save_change/', views.save_change, name='save_change'),
]