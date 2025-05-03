from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from functools import wraps

def pdg_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'PDG':
            return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'MANAGER':
             return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def chef_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type.upper() != 'CHEF':
            return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
    
def waiter_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type.upper() != 'SERVER':
             return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def delivery_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'DELIVERY':
             return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def client_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'CLIENT':
             return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def all_roles_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type not in ['PDG', 'MANAGER', 'CHEF', 'WAITER', 'CLIENT']:
             return render(request, 'login.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

