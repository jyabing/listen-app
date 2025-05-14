from django.urls import path
from .views import (
    practice_view,
    practice_setup_view,
    login_view,
    wrong_list_view,      # ✅ 加入这里
    retry_wrong_view      # ✅ 加入这里
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', practice_setup_view, name='practice_setup'),
    path('start/', practice_view, name='practice'),
    path('wrong/', wrong_list_view, name='wrong_list'),
    path('wrong/<int:material_id>/retry/', retry_wrong_view, name='retry_wrong'),
]