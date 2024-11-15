from django.contrib import admin
from .models import Event, Ticket, Purchase

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'date', 'status', 'registration_fee_paid', 'total_tickets']
    list_filter = ['status', 'registration_fee_paid', 'category']
    search_fields = ['title', 'description', 'organizer__username']
    inlines = [TicketInline]

    def total_tickets(self, obj):
        return obj.tickets.count()
    total_tickets.short_description = 'Ticket Types'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'price', 'quantity', 'available_quantity']
    list_filter = ['event']
    search_fields = ['name', 'event__title']

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['confirmation_code', 'user', 'ticket', 'quantity', 'total_price', 'purchase_date']
    list_filter = ['purchase_date', 'ticket__event']
    search_fields = ['confirmation_code', 'user__username', 'ticket__event__title']
    readonly_fields = ['confirmation_code']