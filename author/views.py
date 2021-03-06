from django.conf import settings
from django.contrib.auth import (authenticate,
                                 login as auth_login, logout as auth_logout)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie

from author.models import Author, FriendRequest
from django.contrib import messages

from node.request_api import post_friend_request, get_is_friend


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
                # We need to make sure we aren't logging in with a remote
                # author...
                if author[0].host == settings.LOCAL_HOST:
                    # make sure the user is approved first
                    if not user.is_active:
                        # An error occurred
                        context['error'] = \
                            'Please wait for admin to approve your account'
                        return render_to_response('login.html', context)
                    auth_login(request, user)
                    return HttpResponseRedirect('/author/posts/', status=302)
                else:
                    context['error'] = ('The username and/or password is '
                                        'incorrect.')
            else:
                # An error occurred
                context['error'] = 'The username and/or password is incorrect.'

        return render_to_response('login.html', context)
    else:
        if request.user.is_superuser:
            auth_logout(request)
            return redirect('/')
        else:
            return HttpResponseRedirect('/author/posts/', status=302)


@login_required
def logout(request):
    if request.user.is_authenticated():
        """Logs the current logged in user out of the web application."""
        auth_logout(request)
    return redirect('/')

def profile_self(request):
    """Redirect to the logged in Author's profile"""
    context = RequestContext(request)

    if request.user.is_authenticated():

        if request.method == 'GET':
            try:
                author = Author.objects.get(user=request.user)
                return redirect('/author/%s' % author.uuid)

            except Author.DoesNotExist:
                return _render_error('login.html', 'Please log in.', context)
        else:
            return _render_error('login.html', 'Invalid request.', context)
    else:
        return _render_error('login.html', 'Please log in.', context)


def profile(request, author_id):
    """Display the author's profile and profile updates if authenticated."""
    context = RequestContext(request)

    if request.user.is_authenticated():

        if request.method == 'GET':
            # Display the profile page
            try:
                author = Author.objects.get(uuid=author_id)

                context['username'] = author.user
                context['github_username'] = author.github_user
                context['host'] = author.host

                if author_id != Author.objects.get(user=request.user).uuid:
                    context['readonly'] = True
                else:
                    context['readonly'] = False

                return render_to_response('profile.html', context)
            except Author.DoesNotExist:
                return _render_error('login.html', 'Please log in.', context)

        elif request.method == 'POST':
            # Update the profile information
            github_user = request.POST['github_username']
            password = request.POST['password']

            author = Author.objects.get(user=request.user)
            if author.uuid == author_id:
                # Make sure we have the permissions
                author.github_user = github_user

                if len(password) > 0:
                    # Password is changed, we need to force a re-login.
                    author.user.set_password(password)
                    author.user.save()
                    author.save()
                    return redirect('/')
                else:
                    author.user.save()
                    author.save()
                    context['success'] = 'Successfully updated!'
                    context['github_username'] = author.github_user
                    context['host'] = author.host
                    return render_to_response('profile.html', context)

            else:
                return _render_error('login.html', 'Invalid request.', context)
        else:
            return _render_error('login.html', 'Invalid request.', context)

    else:
        return _render_error('login.html', 'Please log in.', context)

@ensure_csrf_cookie
def register(request):
    """Register creates a new Author in the system.

    If the information is invalid, the error information will be displayed.
    """
    context = RequestContext(request)
    if request.method == 'POST':
        username = request.POST['userName']
        password = request.POST['pwd']
        github_user = request.POST['github_username']

        # check if its a unique username
        if len(User.objects.filter(username=username)) > 0:
            context = RequestContext(
                request,
                {
                    'userNameValidity':
                        'The username "%s" is taken' % username,
                    'github_username': "%s" % github_user
                })
        # check if there are spaces in username
        elif " " in username:
            context = RequestContext(
                request,
                {
                    'userNameValidity':
                        'The username "%s" cannot contain spaces' % username,
                    'github_username': "%s" % github_user
                })
        else:
            if username and password:
                user = User.objects.create_user(username=username,
                                                password=password)
                # user.is_active = true only when admin approves
                user.is_active = False
                user.save()

                Author.objects.create(user=user, github_user=github_user)
                return redirect('/')

    return render_to_response('register.html', context)


def search(request):
    """Returns a list of authors.

    The returned list of authors contains their username, first_name,
    and last_name.
    """
    context = RequestContext(request)

    if request.method == 'POST':
        search_value = request.POST['searchValue']

        author_info = []

        if search_value == '*' or search_value is None:
            users = User.objects.all()
        else:
            # query all values containing search results
            users = User.objects.filter(Q(username__contains=search_value) &
                                        ~Q(username=request.user))

        results = 0
        # setting each author search information
        for user in users:
            results += 1
            try:
                friend = False
                sent = False
                received = False
                sent = False
                follow = False
                sentList = []
                receivedList = []
                rUser = Author.objects.get(user = request.user)
                author = Author.objects.get(user=user)
                friend = FriendRequest.is_friend(rUser, author)
                follow = FriendRequest.is_following(rUser, author)
                sentList = FriendRequest.sent_requests(rUser)
                if sentList:
                    if author in sentList:
                        sent = True
                receivedList = FriendRequest.received_requests(rUser)
                if receivedList:
                    if author in receivedList:
                        received = True
                user_info = {"displayname": author.get_username(),
                             "userName": author.user.username,
                             "userID": author.get_uuid(),
                             "host": author.get_host(),
                             "friend": friend,
                             "sent": sent,
                             "received": received,
                             "follow": follow}

                author_info.append(user_info)
            except:
                pass
        print("context")
        context = RequestContext(request, {'searchValue': search_value,
                                           'authorInfo': author_info,
                                           'results': results})

    return render_to_response('searchResults.html', context)


def follow(request):
    context = RequestContext(request)
    if request.method == 'POST':
        if request.user.is_authenticated():
            followee = request.POST['followee']
            followee = User.objects.get(username=followee)
            followee2 = Author.objects.get(user=followee)
            author = Author.objects.get(user=request.user)
            status = FriendRequest.follow(author, followee2)
            if status:
                messages.info(request, 'New Follower')
            return redirect('/', context)
    else:
        _render_error('login.html', 'Please log in.', context)


def request_friendship(request):
    """Sends a friend request."""
    context = RequestContext(request)

    if request.method == 'POST':
        if request.user.is_authenticated():
            friend_requestee = request.POST['friend_requestee']
            friend_user = User.objects.get(username=friend_requestee)
            friend = Author.objects.get(user=friend_user)
            requester = Author.objects.get(user=request.user)

            if '__' not in friend.user.username:
                # local author
                status = FriendRequest.make_request(requester, friend)
            else:
                print 'HERE'
                # remote author
                status = post_friend_request(requester, friend)
                if status:
                    status = FriendRequest.make_request(requester, friend)

            if status:
                messages.info(request, 'Friend request sent successfully')
            else:
                messages.error(request, 'Error sending a friend request')

            return redirect('/author/friends')
        else:
            _render_error('login.html', 'Please log in.', context)


def accept_friendship(request):
    """Handles a post request to accept a friend request."""
    context = RequestContext(request)

    if request.method == 'POST':
        if request.user.is_authenticated():
            friend_requester = request.POST['friend_requester']
            requester = User.objects.get(username=friend_requester)
            requester2 = Author.objects.get(user=requester)
            author = Author.objects.get(user=request.user)
            status = FriendRequest.accept_request(requester2, author)
            print(status)
            if status:
                messages.info(request, 'Friend request has been accepted.')
            return redirect('/author/friends', context)
        else:
            _render_error('login.html', 'Please log in.', context)


def reject_friendship(request):
    """Handles a request to reject a friend request."""
    context = RequestContext(request)
    print("here")
    if request.method == 'POST':
        print("in post")
        if request.user.is_authenticated():
            friend_requester = request.POST['friend_requester']
            requester = User.objects.get(username=friend_requester)
            requester2 = Author.objects.get(user=requester)
            author = Author.objects.get(user=request.user)
            print(author)
            status = FriendRequest.reject_request(requester2, author)

            if status:
                messages.info(request, 'Friend request has been rejected.')
            return redirect('/author/friends', context)
        else:
            _render_error('login.html', 'Please log in.', context)

def unfriend(request):
    context = RequestContext(request)
    if request.method == 'POST':
        if request.user.is_authenticated():
            friendToUnfriend = request.POST['unfriender']
            print(friendToUnfriend)
            requester = User.objects.get(username=friendToUnfriend)
            requester2 = Author.objects.get(user=requester)
            author = Author.objects.get(user=request.user)
            print(author)
            status = FriendRequest.unfriend(author, requester2)
            if status:
                messages.info(request, 'Successfully unbefriended')
            return redirect('/author/friends', context)
        else:
            _render_error('login.html', 'Please log in.', context)


def friend_request_list(request):
    """Displays a list of users that the author sent a friend requst to."""
    context = RequestContext(request)

    if request.method == 'GET':
        if request.user.is_authenticated():
            request_list = []
            sent_list = []
            friend_list = []
            rlShow = True
            slShow = True
            flShow = True
            rUser = Author.objects.get(user = request.user)
            #friendJ = get_is_friend('2356e331-ef78-402f-b880-240269f7a93f', '52e7ace8-3723-4a7d-8abc-d4228ff5dced')
            for author in FriendRequest.received_requests(rUser):
                # check if it is a remote author
                info = {"displayname": author.get_username(),
                        "username": author.user.username,
                        "userID": author.get_uuid(),
                        "host": author.get_host()}
                request_list.append(info)
            for author in FriendRequest.sent_requests(rUser):
                if '__' in author.user.username:
                    isFriend = get_is_friend(rUser, author)
                info = {"displayname": author.get_username(),
                        "username": author.user.username,
                        "userID": author.get_uuid(),
                        "host": author.get_host()}
                sent_list.append(info)
            for author in FriendRequest.get_friends(rUser):
                info = {"displayname": author.user.username,
                        "username": author.user.username,
                        "userID": author.get_uuid(),
                        "host": author.get_host()}
                friend_list.append(info)
            if not request_list:
                rlShow = False
            if not sent_list:
                slShow = False
            if not friend_list:
                flShow = False
            context = RequestContext(request, {'requestList': request_list,
                                               'sentList': sent_list,
                                               'friendList':friend_list,
                                               'rlShow': rlShow,
                                               'slShow':slShow,
                                               'flShow':flShow})
        else:
            _render_error('login.html', 'Please log in.', context)

    return render_to_response('friendRequests.html', context)


def friend_list(request, author):
    """Gets the user's friends."""
    context = RequestContext(request)
    print("here")
    a = []
   # get_friends_in_list(author, a)
    print("here2")
    if request.method == 'GET':
        if request.user.is_authenticated():
            friend_usernames = []
            author = Author.objects.get(user=request.user)
            friend_list = FriendRequest.get_friends(author)

            for friend in friend_list:
                friend_usernames.append(friend.user)

            context = RequestContext(request, {'friendList': friend_usernames})
        else:
            _render_error('login.html', 'Please log in.', context)
    return render_to_response('friends.html', context)


def _render_error(url, error, context):
    context['error'] = error
    return render_to_response(url, context)
