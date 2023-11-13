from django.urls import path

from rpidrive.views.ui_api.users import (
    UserCreateView,
    UserDetailView,
    UserListView,
    UserLoggedInView,
    UserLoginView,
    UserLogoutView,
    UserSelfView,
)

urlpatterns = [
    path("", UserListView.as_view()),
    path("create", UserCreateView.as_view()),
    path("login", UserLoginView.as_view()),
    path("logout", UserLogoutView.as_view()),
    path("check", UserLoggedInView.as_view()),
    path("<int:user_id>", UserDetailView.as_view()),
    path("self", UserSelfView.as_view()),
]
