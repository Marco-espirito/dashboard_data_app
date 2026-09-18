from django import forms

from .models import Product, Sale


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Fichier CSV",
        help_text="CSV UTF-8 séparé par des points-virgules, 2 Mo maximum.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv", "class": "form-control"}),
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if not uploaded_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Le fichier doit avoir l’extension .csv.")
        if uploaded_file.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Le fichier dépasse la limite de 2 Mo.")
        return uploaded_file


class SaleForm(forms.ModelForm):
    product_name = forms.CharField(
        max_length=200,
        label="Produit",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex. Clavier"}),
    )

    class Meta:
        model = Sale
        fields = ["product_name", "price", "quantity", "date"]
        labels = {"price": "Prix unitaire", "quantity": "Quantité", "date": "Date et heure"}
        widgets = {
            "price": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_product_name(self):
        return self.cleaned_data["product_name"].strip()

    def save(self, commit=True):
        self.instance.product, _ = Product.objects.get_or_create(name=self.cleaned_data["product_name"])
        return super().save(commit=commit)


class PerformanceFilterForm(forms.Form):
    start_date = forms.DateField(required=False, label="Du", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    end_date = forms.DateField(required=False, label="Au", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and start > end:
            raise forms.ValidationError("La date de début doit précéder la date de fin.")
        return cleaned_data
