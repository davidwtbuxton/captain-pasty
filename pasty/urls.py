from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^api/v1/', include([
        url(r'^pastes/$', views.api_paste_list, name='api_paste_list'),
        url(r'^pastes/([a-zA-Z0-9]+)/$', views.api_paste_detail, name='api_paste_detail'),
        url(r'^star/$', views.api_star_create, name='api_star_create'),
        url(r'^star/list/$', views.api_star_list, name='api_star_list'),
        url(r'^star/delete/$', views.api_star_delete, name='api_star_delete'),
    ])),

    url(r'^$', views.home, name='home'),
    url(r'^new/$', views.paste_create, name='paste_create'),
    url(r'^recent/$', views.paste_list, name='paste_list'),
    url(r'^search/$', views.paste_list, name='paste_search'),

    url(r'^admin/$', views.admin, name='admin'),
    url(r'^admin/lexers/$', views.admin_lexers, name='admin_lexers'),

    url(r'^p/([a-zA-Z0-9]+)/$', views.paste_redirect, name='paste_redirect'),
    url(r'^([a-zA-Z0-9]+)/$', views.paste_detail, name='paste_detail'),
    url(r'^([a-zA-Z0-9]+).zip$', views.paste_download, name='paste_download'),
    url(r'^([a-zA-Z0-9]+)/(.+)$', views.paste_raw, name='paste_raw'),
]
