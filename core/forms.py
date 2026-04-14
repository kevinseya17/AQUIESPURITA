from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Perfil
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    cedula = forms.CharField(
        max_length=20,
        required=True,
        label="Cédula",
        widget=forms.TextInput(attrs={'placeholder': 'Ingresa tu cédula'})
    )

    numero_contacto = forms.CharField(
        max_length=15,
        required=True,
        label="Número de contacto",
        widget=forms.TextInput(attrs={'placeholder': 'Ej: +56912345678'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'cedula', 'numero_contacto', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado')
        return email

from django import forms
from django.contrib.auth.models import User
from .models import Perfil

from django import forms
from django.contrib.auth.models import User
from .models import Perfil

class EditarPerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='Nombre', required=True)
    last_name = forms.CharField(max_length=30, label='Apellidos', required=True)
    email = forms.EmailField(label='Correo electrónico', required=True)

    # Campos del modelo Perfil
    cedula = forms.CharField(max_length=20, label='Cédula', required=False)
    numero_contacto = forms.CharField(max_length=15, label='Número de contacto', required=False)
    foto_perfil = forms.ImageField(label='Foto de perfil', required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'perfil'):
            perfil = user.perfil
            self.fields['cedula'].initial = perfil.cedula
            self.fields['numero_contacto'].initial = perfil.numero_contacto
            self.fields['foto_perfil'].initial = perfil.foto_perfil

    def save(self, commit=True):
        user = super().save(commit=False)
        perfil, _ = Perfil.objects.get_or_create(user=user)

        perfil.cedula = self.cleaned_data.get('cedula', perfil.cedula)
        perfil.numero_contacto = self.cleaned_data.get('numero_contacto', perfil.numero_contacto)

        nueva_foto = self.cleaned_data.get('foto_perfil')
        if nueva_foto:
            perfil.foto_perfil = nueva_foto

        if commit:
            user.save()
            perfil.save()
        return user


    def clean_email(self):
        email = self.cleaned_data['email']
        user_id = self.instance.id
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
