from django.urls import path

from . import monitoring, views, web_views

app_name = "music"
urlpatterns = [
    path("", web_views.IndexView.as_view(), name="home"),
    path("about", web_views.AboutView.as_view(), name="about"),
    path("register", web_views.RegisterView.as_view(), name="register"),
    path("login", web_views.LoginView.as_view(), name="login"),
    path("logout", web_views.LogoutView.as_view(), name="logout"),
    path("calculate", web_views.CalculationView.as_view(), name="calculate"),
    path("logs", web_views.LogsView.as_view(), name="logs"),
    path("roles", web_views.RolesView.as_view(), name="roles"),
    path("actuator/health", monitoring.HealthView.as_view(), name="health"),
    path("actuator/info", monitoring.InfoView.as_view(), name="info"),
    path("actuator/metrics", monitoring.MetricsView.as_view(), name="metrics"),
    path(
        "actuator/metrics/<str:metric>", monitoring.MetricsView.as_view(), name="metric"
    ),
    path("songs", web_views.SongListView.as_view(), name="songs"),
    path("songs/add", web_views.SongFormView.as_view(), name="songs-add"),
    path("songs/<int:pk>/edit", web_views.SongFormView.as_view(), name="songs-edit"),
    path(
        "songs/<int:pk>/delete", web_views.SongDeleteView.as_view(), name="songs-delete"
    ),
    path("artists", web_views.ArtistListView.as_view(), name="artists"),
    path("artists/add", web_views.ArtistFormView.as_view(), name="artists-add"),
    path(
        "artists/<int:pk>/edit", web_views.ArtistFormView.as_view(), name="artists-edit"
    ),
    path(
        "artists/<int:pk>/delete",
        web_views.ArtistDeleteView.as_view(),
        name="artists-delete",
    ),
    path("api/songs", views.SongListAPIView.as_view(), name="songs-api"),
    path(
        "api/songs/<int:pk>", views.SongDetailAPIView.as_view(), name="songs-api-detail"
    ),
    path("api/artists", views.ArtistListAPIView.as_view(), name="artists-api"),
    path(
        "api/artists/<int:pk>",
        views.ArtistDetailAPIView.as_view(),
        name="artists-api-detail",
    ),
]
