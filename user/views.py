import django
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


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
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django.contrib.auth.login(request, user)
            request.session.set_expiry(0)
            print("登陆成功")
            return HttpResponseRedirect("/")
        else:
            error = '用户不存在或用户密码输入错误!!'
            return render(request, 'login.html', locals())


