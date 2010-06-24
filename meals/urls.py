from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

import models

urlpatterns = patterns('',
                       
   url(r'^$', 'meals.views.home'),

   url(r'^recipes/$',
       'django.views.generic.list_detail.object_list',
       {'queryset': models.Recipe.objects.all(),
        'template_object_name': 'recipe'}),

   url(r'^(\d{4})/(\d{2})/(\d{2})/(\w+)/$', 
        'meals.views.planner',
        name="meals-planner"),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # need this while I don't have internet access :(
    (r'^jquery/', 
     'django.views.static.serve',
     {'document_root': '/home/mark/code/third_party/django/django/contrib/admin/media/js/',
      'path': 'jquery.min.js'})
)
