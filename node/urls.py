from django.conf.urls import patterns, url

from node import views

urlpatterns = patterns(
    '',
    url(r'^posts$', views.public_posts),
    url(r'^posts/(?P<post_id>[-\w]+)$', views.public_posts),
    url(r'^posts/$', views.public_posts),
    url(r'^posts/(?P<post_id>[-\w]+)/$', views.public_posts),
    url(r'^author/posts$', views.posts),
    url(r'^author/(?P<author_id>[-\w]+)/posts$', views.posts),
    url(r'^author$', views.authors),
    url(r'^author/(?P<author_id>[-\w]+)$', views.author),
    url(r'^friends/(?P<user_id>[-\w]+)$', views.friends),
    url(r'^friends/(?P<user_id1>[-\w]+)/(?P<user_id2>[-\w]+)$',
        views.is_friend),
    url(r'^friendrequest$', views.friend_request),
    url(r'^getpost/(?P<post_id>[-\w]+)$', views.get_post),
)
