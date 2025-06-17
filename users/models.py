from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('CASHIER', 'Cashier'),
        ('MANAGER', 'Manager'),
        ('SENIOR_MANAGER', 'Senior Manager'),
        ('CEO', 'CEO'),
        # Add other roles as needed based on SRS actors
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True, help_text="User role in the system")
    fingerprint_id_thumb = models.BinaryField(max_length=2048, null=True, blank=True)
    fingerprint_id_index = models.BinaryField(max_length=2048, null=True, blank=True)
    fingerprint_id_middle = models.BinaryField(max_length=2048, null=True, blank=True)
    fingerprint_id_ring = models.BinaryField(max_length=2048, null=True, blank=True)
    fingerprint_id_little = models.BinaryField(max_length=2048, null=True, blank=True)
    # fname You can add additional fields here if needed in the future
    # For example:
    # bio = models.TextField(blank=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    pass

    def __str__(self):
        return f"{self.username} ({self.get_role_display() or 'No Role'})"