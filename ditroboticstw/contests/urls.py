from django_fsu import url

from ditroboticstw.contests import views


urlpatterns = [
    url('contests/', views.contests, name='contests'),
    url('', views.contests, name='index'),
]
