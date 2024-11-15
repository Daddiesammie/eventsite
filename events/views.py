from django.utils import timezone
from django.db.models import Sum

import uuid
from django.views.generic import (
    TemplateView, CreateView, ListView, 
    DetailView, FormView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Event, Ticket, Purchase
from .forms import EventForm, PurchaseTicketForm, TicketForm
from .utils import initialize_payment, verify_payment
from .utils import initialize_payment, verify_payment, send_ticket_email  # Add send_ticket_email here


class HomeView(TemplateView):
    template_name = 'events/home.html'

class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 9

    def get_queryset(self):
        return Event.objects.filter(status='approved').order_by('-date')

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'events/ticket_form.html'

    def form_valid(self, form):
        event = get_object_or_404(Event, pk=self.kwargs['event_pk'])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('events:event_detail', kwargs={'pk': self.kwargs['event_pk']})

class PurchaseTicketView(LoginRequiredMixin, FormView):
    template_name = 'events/purchase_ticket.html'
    form_class = PurchaseTicketForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.ticket = get_object_or_404(Ticket, pk=self.kwargs['ticket_id'])
        kwargs['ticket'] = self.ticket
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ticket'] = self.ticket
        return context

    def form_valid(self, form):
        quantity = form.cleaned_data['quantity']
        if quantity <= self.ticket.available_quantity():
            total_price = self.ticket.price * quantity
            reference = f"TIX-{uuid.uuid4().hex[:8]}"

            purchase = Purchase.objects.create(
                ticket=self.ticket,
                user=self.request.user,
                quantity=quantity,
                total_price=total_price,
                payment_reference=reference
            )

            payment_data = initialize_payment(
                email=self.request.user.email,
                amount=float(total_price),
                reference=reference,
                request=self.request,
                purchase_id=purchase.id
            )

            if payment_data['status']:
                return redirect(payment_data['data']['authorization_url'])
            else:
                purchase.delete()
                messages.error(self.request, 'Payment initialization failed.')
        else:
            messages.error(self.request, 'Not enough tickets available.')
        return self.form_invalid(form)


class PaymentCallbackView(View):
    def get(self, request):
        reference = request.GET.get('reference')
        if reference:
            payment_data = verify_payment(reference)
            if payment_data['status'] and payment_data['data']['status'] == 'success':
                purchase = Purchase.objects.get(payment_reference=reference)
                purchase.payment_status = 'completed'
                purchase.save()
                
                # Add print statement to track email sending
                print(f"Sending ticket email for purchase {purchase.id}")
                send_ticket_email(purchase)
                print(f"Email sent successfully for purchase {purchase.id}")
                
                messages.success(request, 'Payment successful! Your tickets have been sent to your email.')
                return redirect('events:purchase_confirmation', purchase_id=purchase.id)


class PurchaseConfirmationView(LoginRequiredMixin, DetailView):
    model = Purchase
    template_name = 'events/purchase_confirmation.html'
    context_object_name = 'purchase'
    pk_url_kwarg = 'purchase_id'

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)


class PurchaseHistoryView(LoginRequiredMixin, ListView):
    template_name = 'events/purchase_history.html'
    context_object_name = 'purchases'
    paginate_by = 10

    def get_queryset(self):
        return Purchase.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_spent'] = self.get_queryset().filter(
            payment_status='completed'
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        return context

class MyTicketsView(LoginRequiredMixin, ListView):
    template_name = 'events/my_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 12

    def get_queryset(self):
        return Purchase.objects.filter(
            user=self.request.user,
            payment_status='completed'
        ).select_related('ticket', 'ticket__event').order_by('ticket__event__date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'upcoming_events': self.get_queryset().filter(
                ticket__event__date__gte=timezone.now()
            ).count(),
            'today': timezone.now().date(),
            'purchases': Purchase.objects.filter(user=self.request.user).order_by('-purchase_date'),
            'total_spent': Purchase.objects.filter(
                user=self.request.user,
                payment_status='completed'
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        })
        return context
