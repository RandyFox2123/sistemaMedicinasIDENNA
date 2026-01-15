
from django import forms  
from .models import Medicina, Presentacion_Medicamento, Ubicacion
from datetime import date

class MedicinaForm(forms.ModelForm):
    class Meta:
        model = Medicina

        fields = ['medicina', 'presentacion', 'cantidad', 'laboratorio', 
                 'ubicacion', 'anaquel', 'descripcion', 'observaciones', 
                 'imagen_medicina', 'fecha_caducidad']
        
        widgets = {
            'medicina': forms.TextInput(attrs={
                'class': 'campo',
                'minlength': '2',  
                'maxlength': '400',
                'required': True
            }),

            'presentacion': forms.Select(attrs={
                'class': 'campo',
                'required': True
            }),

            'cantidad': forms.NumberInput(attrs={
                'class': 'campo',
                'min': '0',  
                'max': '100000',
                'required': True
            }),

            'laboratorio': forms.TextInput(attrs={
                'class': 'campo',
                'minlength': '2',  
                'maxlength': '350',
                'required': True
            }),
            
            'ubicacion' : forms.Select(attrs={
                'class': 'campo',
                'required': True
            }),

            'anaquel': forms.TextInput(attrs={
                'class': 'campo',
                'minlength': '1',  
                'maxlength': '100',
                'required': True
            }),

            'fecha_caducidad': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date', 
                'class': 'campo', 
                'required': True
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'campo_textarea', 
                'required': True
            }),

            'observaciones': forms.Textarea(attrs={'class': 'campo_textarea'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ubicacion'].queryset = Ubicacion.objects.filter(estado=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['presentacion'].queryset = Presentacion_Medicamento.objects.all()


