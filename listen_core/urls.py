from django.contrib import admin 
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from practice.views import home_view   # ← 新增

urlpatterns = [
    path('', home_view, name='home'),  # ← 新增
    path('admin/', admin.site.urls),
    path('practice/', include('practice.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)