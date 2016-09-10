from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^api/$', views.api_root, name='api_root'),
    url(r'^api/v1/', include([
        url(r'^$', views.api_index, name='api_index'),
        url(r'^pastes/$', views.api_paste_list, name='api_paste_list'),
        url(r'^pastes/([a-zA-Z0-9]+)/$', views.api_paste_detail, name='api_paste_detail'),
        url(r'^star/$', views.api_star, name='api_star'),
    ])),

    url(r'^highlight-styles.css$', views.highlight_styles, name='highlight_styles'),
    url(r'^$', views.home, name='home'),
    url(r'^new/$', views.paste_create, name='paste_create'),
    url(r'^recent/$', views.paste_list, name='paste_list'),
    url(r'^search/$', views.paste_search, name='paste_search'),
    url(r'^about/$', views.about, name='about'),
    url(r'^admin/$', views.admin, name='admin'),
    url(r'^([a-zA-Z0-9]+)/$', views.paste_detail, name='paste_detail'),
    url(r'^([a-zA-Z0-9]+).zip$', views.paste_download, name='paste_download'),
]
