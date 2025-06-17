from django.db import models
from django.conf import settings

class AuditableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_created_by', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_updated_by', on_delete=models.SET_NULL, null=True, blank=True)
    attachment = models.FileField(upload_to='attachments/%(class)s/', blank=True, null=True)

    class Meta:
        abstract = True