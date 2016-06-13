from django.contrib.auth import views as auth_views
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class EmailValidationPasswordResetForm(auth_views.PasswordResetForm):
    """
    Override django auth_view reset and inform user if email isn't associated with user
    """
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__exact=email, is_active=True).exists():
            raise ValidationError("There is no user registered with that email address")
        return email