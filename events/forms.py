from django import forms
from .models import Event, Ticket, Profile

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'category', 'capacity', 'image']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['name', 'price', 'quantity', 'description']

class PurchaseTicketForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Number of tickets'
            }
        )
    )

    def __init__(self, ticket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket = ticket
        self.fields['quantity'].max_value = ticket.available_quantity()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'phone', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
