
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class AlphanumericPasswordValidator:
    def validate(self, password, user=None):
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            raise ValidationError(
                _('Password must be at least 8 characters long and contain both letters and numbers.'),
                code='password_not_alphanumeric',
            )

    def get_help_text(self):
        return _('Your password must be at least 8 characters long and contain both letters and numbers.')