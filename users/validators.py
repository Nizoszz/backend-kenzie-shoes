from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        requirements = (
            (any(character.isupper() for character in password), "uma letra maiúscula"),
            (any(character.islower() for character in password), "uma letra minúscula"),
            (any(character.isdigit() for character in password), "um número"),
            (
                any(not character.isalnum() for character in password),
                "um caractere especial",
            ),
        )
        missing = [description for valid, description in requirements if not valid]
        if missing:
            raise ValidationError(
                _("A senha deve conter %(requirements)s."),
                code="password_missing_character_classes",
                params={"requirements": ", ".join(missing)},
            )

    def get_help_text(self):
        return _(
            "Sua senha deve conter letra maiúscula, letra minúscula, número e "
            "caractere especial."
        )
