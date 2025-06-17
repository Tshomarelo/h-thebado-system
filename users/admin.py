from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Renamed to avoid conflict
from .models import User

# Register your models here.

class UserAdmin(BaseUserAdmin):
    model = User
    # Add 'role' to the list display and fieldsets
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_filter = BaseUserAdmin.list_filter + ('role',)

admin.site.register(User, UserAdmin)