from django.contrib.auth import (authenticate,
                                 login as auth_login, logout as auth_logout)
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext

from author.models import Author


def login(request):
    """Validate the user, password combination on login.

    If successful, redirect the user to the home page, otherwise, return an
    error in the response.
    """
    if not request.user.is_authenticated():
        context = RequestContext(request)

        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']

            # Use Django's built in authentication to verify if the username
            # and password combination is valid
            user = authenticate(username=username, password=password)
            author = Author.objects.filter(user=user)
            if len(author) > 0:
                auth_login(request, user)
                return redirect('/authors/' + str(user.id))
            else:
                # An error occurred
                context['error'] = 'The username and/or password is incorrect.'

        return render_to_response('login.html', context)
    else:
        return redirect('/authors/' + str(request.user.id))


@login_required
def logout(request, author):
    context = RequestContext(request)
    auth_logout(request)
    return redirect('/')


def home(request, author):
    """Display the author's home page."""
    context = RequestContext(request)

    if request.method == 'GET':
        if request.user.is_authenticated():
            try:
                author = Author.objects.get(user=request.user)
                return render_to_response('home.html', context)
            except Author.DoesNotExist:
                return _render_error('login.html', 'Please log in.', context)
        else:
            return _render_error('login.html', 'Please log in.', context)
    else:
        _render_error('login.html', 'Invalid request.', context)


def profile(request, author):
    """Display the author's profile and handle profile updates."""
    context = RequestContext(request)

    if request.method == 'GET':
        if request.user.is_authenticated():
            # Display the profile page
            try:
                author = Author.objects.get(user=request.user)

                context['github_username'] = author.github_user
                return render_to_response('profile.html', context)
            except Author.DoesNotExist:
                return _render_error('login.html', 'Please log in.', context)
        else:
            return _render_error('login.html', 'Please log in.', context)
    elif request.method == 'POST':
        if request.user.is_authenticated():
            # Update the profile information
            github_user = request.POST['github_username']
            password = request.POST['password']

            author = Author.objects.get(user=request.user)
            author.github_user = github_user
            author.user.set_password(password)
            author.save()

            context['success'] = 'Successfully updated!'
            context['github_username'] = author.github_user
            return render_to_response('profile.html', context)
    else:
        _render_error('login.html', 'Invalid request.', context)


def _render_error(url, error, context):
    context['error'] = error
    return render_to_response(url, context)
