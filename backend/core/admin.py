from django.contrib import admin

from core.models import HRUser

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(HRUser, UserAdmin)
