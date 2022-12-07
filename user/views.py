import hashlib

import django
from django.contrib.auth import authenticate, logout, models
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password


def login(request):
    return render(request, 'login.html')


def login_view(request):
    # 处理GET请求
    if request.method == 'GET':
        # 1, 首先检查session，判断用户是否第一次登录，如果不是，则直接重定向到首页
        if 'username' in request.session:  # request.session 类字典对象
            return HttpResponseRedirect("/")
        # 2, 然后检查cookie，是否保存了用户登录信息
        if 'username' in request.COOKIES:
            # 若存在则赋值回session，并重定向到首页
            request.session['username'] = request.COOKIES['username']
            return HttpResponseRedirect("/")
        # 不存在则重定向登录页，让用户登录
        return render(request, 'login.html')
    elif request.method == 'POST':
        # username = request.POST['username']
        # password = request.POST['password']
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        try:
            user = models.User.objects.get(username=username)
            if password == user.password:
                response = HttpResponse()
                response.set_cookie('login', 'yes')
                return response
            else:
                password_error = '密码错误!!'
                return render(request, 'login.html', locals())
        except:
            username_error = '用户不存在!!'
            return render(request, 'login.html', locals())


def logout_view(request):
    logout(request)
    return render(request, 'login.html')


def register(requset):
    return render(requset, 'register.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        print(username)
        print(password)
        print(password2)
        same_name_user = models.User.objects.filter(username=username)
        if same_name_user:
            res = {
                'status': 1
            }
            return JsonResponse(res, safe= True)
        else:
            new_user = models.User.objects.create()
            new_user.username = username
            new_user.password = password  # 两次密码是否相同在前端验证
            new_user.save()
            return HttpResponseRedirect('/')
    return render(request, 'register.html')
