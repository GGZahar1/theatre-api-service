from django.contrib import admin

from theatre.models import (
    Genre,
    Actor,
    Performance,
    Ticket,
    Reservation,
    TheatreHall,
    Play,
)

admin.site.register(TheatreHall)
admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Performance)
admin.site.register(Play)
admin.site.register(Reservation)
admin.site.register(Ticket)
