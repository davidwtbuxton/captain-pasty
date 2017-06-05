import session_csrf
from django.conf.urls import include, url


session_csrf.monkeypatch()


urlpatterns = [
    url(r'^_ah/', include('djangae.urls')),
    url(r'^', include('pasty.urls')),
]
