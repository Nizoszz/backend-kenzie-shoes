from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from addresses.models import Address
from products.models import Product
from users.models import PartnerApplication, User


class StyledFormMixin:
    def style_fields(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class RegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=50, label="Nome")
    last_name = forms.CharField(max_length=50, label="Sobrenome")
    street = forms.CharField(max_length=255, label="Rua")
    number = forms.IntegerField(label="Número", min_value=1)
    add_on = forms.CharField(max_length=5, label="Complemento", required=False)
    zipcode = forms.CharField(max_length=10, label="CEP")
    city = forms.CharField(max_length=50, label="Cidade")
    state = forms.CharField(max_length=2, label="UF")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        address = Address.objects.create(
            street=self.cleaned_data["street"],
            number=self.cleaned_data["number"],
            add_on=self.cleaned_data["add_on"],
            zipcode=self.cleaned_data["zipcode"],
            city=self.cleaned_data["city"],
            state=self.cleaned_data["state"].upper(),
        )
        user.address = address
        if commit:
            user.save()
        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "image_user")
        labels = {"image_user": "URL da imagem"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class AddressForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Address
        fields = ("street", "number", "add_on", "zipcode", "city", "state")
        labels = {"street": "Rua", "number": "Número", "add_on": "Complemento", "zipcode": "CEP", "city": "Cidade", "state": "UF"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class PartnerApplicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PartnerApplication
        fields = ("message",)
        labels = {"message": "Conte sobre sua loja e os produtos que deseja vender"}
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "value", "category", "stock", "description", "image_product")
        labels = {"name": "Nome", "value": "Preço", "category": "Categoria", "stock": "Estoque", "description": "Descrição", "image_product": "URL da imagem"}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class CartQuantityForm(forms.Form):
    quantities = forms.IntegerField(min_value=1, max_value=999)
