from django.urls import path
from .views import PetsView, PetsIdView

urlpatterns = [
    path("pets/", PetsView.as_view()),
    path("pets/<int:pet_id>/", PetsIdView.as_view()),
]
