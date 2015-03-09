from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'socialdistribution.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('author.urls')),
    url(r'^author/posts/', include('post.urls')),
    url(r'^api/', include('node.urls')),
)
