from django.contrib import admin
from .models import Provider, Service, House, Apartment, Consumer, Meter

# Register your models here.
admin.site.register(Provider)
admin.site.register(Service)
admin.site.register(House)
admin.site.register(Apartment)
admin.site.register(Consumer)
admin.site.register(Meter)