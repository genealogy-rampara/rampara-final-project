from django.contrib import admin
from .models import Person, Family, SpouseInfo, UserRegistration, ContactMessage
# Register your models here.
admin.site.register(Person)
admin.site.register(Family)
admin.site.register(SpouseInfo)
admin.site.register(UserRegistration)
admin.site.register(ContactMessage)