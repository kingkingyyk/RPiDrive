from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout
from django.contrib.auth import views as auth_views
from .models import *
from .utils import LoginProtect


@LoginProtect.apply_login_protect
def login_view(request):
    context = {'form': auth_views.AuthenticationForm,
               'drive': Drive.objects.get()}

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_views.auth_login(request, user)
                return redirect('index'), True
        else:
            context['error_message'] = 'Incorrect username or password!'

    return render(request,  'drive/login.html', context), context.get('error_message', '') == 0


def logout_view(request):
    logout(request)
    return redirect('index')
