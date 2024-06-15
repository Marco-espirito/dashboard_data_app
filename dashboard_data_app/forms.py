from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Sale

class UploadFileForm(forms.Form):
    file = forms.FileField()

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'price', 'quantity']
