from schema_graph.views import Schema
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path("schema/", Schema.as_view()),
    path('users/', include('users.urls', namespace='users')),# Added users app URLs
    path('reconciliation/', include('reconciliation.urls', namespace='reconciliation')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    
    # You might want a root path later, e.g., redirecting to reconciliation dashboard
    # path('', include('reconciliation.urls')), # Or a specific landing page view
    #Auto Complete
    
]

# It's also common to add static and media file serving for development here
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)