from django import forms

class AuditableForm(forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request.user.is_authenticated:
            if not instance.pk:
                instance.created_by = self.request.user
            instance.updated_by = self.request.user
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
class ExpenseCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
