from django import forms
from .models import User

class FingerprintRegistrationForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())