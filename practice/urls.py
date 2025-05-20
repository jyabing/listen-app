from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    practice_view,
    practice_setup_view,
    login_view,
    logout_view,
    wrong_list_view,
    retry_wrong_view,
    review_view,
    reading_view,
    review_recommendation_view,
    review_summary_view,
    review_priority_view,

)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', practice_setup_view, name='practice_setup'),
    path('start/', practice_view, name='practice'),
    path('wrong/', wrong_list_view, name='wrong_list'),
    path('wrong/<int:material_id>/retry/', retry_wrong_view, name='retry_wrong'),
    path('review/', review_view, name='review'),
    path('review/next/', review_recommendation_view, name='review_recommendation'),
    path('review/summary/', review_summary_view, name='review_summary'),
    path('review/priority/', review_priority_view, name='review_priority'),
    path('reading/<str:mode>/', reading_view, name='reading'),
]