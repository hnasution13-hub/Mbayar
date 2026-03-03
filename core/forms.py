# ==================================================
# FILE: Mbayar/core/forms.py
# PATH: D:/Project Pyton/Mbayar/core/forms.py
# FUNGSI: Forms untuk input data (UPDATE - TAMBAH REGISTER & RESET FORM)
# ==================================================

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from core.models import StockItem, Menu, KodeBarang

class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['kode_barang', 'name', 'unit', 'stock', 'min_stock', 'supplier']
        widgets = {
            'kode_barang': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control','value': 0}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control','value': 0}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['code', 'name', 'category', 'is_available', 'image']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ===== FORM REGISTER =====
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Depan'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Belakang'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Konfirmasi Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email sudah terdaftar. Gunakan email lain.')
        return email


# ===== FORM RESET PASSWORD =====
class CustomPasswordResetForm(PasswordResetForm):
    """Form untuk meminta reset password via email"""
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Masukkan email Anda',
            'autofocus': True
        })
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Form untuk mengatur password baru"""
    new_password1 = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Masukkan password baru'
        }),
        strip=False,
        help_text='Password minimal 8 karakter dan tidak boleh terlalu umum'
    )
    
    new_password2 = forms.CharField(
        label='Konfirmasi Password Baru',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ulangi password baru'
        }),
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control'
        })