from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/create/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:event_pk>/tickets/add/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:ticket_id>/purchase/', views.PurchaseTicketView.as_view(), name='purchase_ticket'),
    path('purchases/<int:purchase_id>/', views.PurchaseConfirmationView.as_view(), name='purchase_confirmation'),
    path('payment/callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),
    path('my-tickets/', views.MyTicketsView.as_view(), name='my_tickets'),
    path('purchase-history/', views.PurchaseHistoryView.as_view(), name='purchase_history'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('events/<int:event_id>/bookmark/', views.BookmarkView.as_view(), name='bookmark_event'),
    path('bookmarks/', views.BookmarkedEventsView.as_view(), name='bookmarked_events'),


]
