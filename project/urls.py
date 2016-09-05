from django.conf.urls import include, url


urlpatterns = [
    url(r'^_ah/', include('djangae.urls')),
    url(r'^', include('pasty.urls')),
]
