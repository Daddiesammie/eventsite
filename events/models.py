from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_pics/', default='default_avatar.png')
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'event']


class Event(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    title = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_fee_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='events/', null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'pk': self.pk})
    


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=100)  # e.g., "VIP", "Early Bird", "General Admission"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    def available_quantity(self):
        sold = self.purchases.aggregate(total=models.Sum('quantity'))['total'] or 0
        return self.quantity - sold

class Purchase(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='purchases')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_purchases')
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    confirmation_code = models.CharField(max_length=50, unique=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_reference = models.CharField(max_length=100, unique=True, null=True)


    def __str__(self):
        return f"{self.user.username} - {self.ticket.name}"

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        super().save(*args, **kwargs)

    def generate_confirmation_code(self):
        import uuid
        return str(uuid.uuid4()).split('-')[0].upper()

