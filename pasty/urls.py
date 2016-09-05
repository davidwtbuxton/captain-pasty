from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^api/v2/', include([
        url(r'^pastes/$', views.api_paste_list, name='api_paste_list'),
        url(r'^pastes/([a-zA-Z0-9]+)/$', views.api_paste_detail, name='api_paste_detail'),
        url(r'^tags/$', views.api_tag_list, name='api_tag_list'),
    ])),

    url(r'^highlight-styles.css$', views.highlight_styles, name='highlight_styles'),
    url(r'^$', views.paste_create, name='paste_create'),
    url(r'^recent/$', views.paste_list, name='paste_list'),
    url(r'^search/$', views.paste_search, name='paste_search'),
    url(r'^tags/$', views.tag_list, name='tag_list'),
    url(r'^about/$', views.about, name='about'),
    url(r'^admin/$', views.admin, name='admin'),
    url(r'^([a-zA-Z0-9]+)/$', views.paste_detail, name='paste_detail'),
]
