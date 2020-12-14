from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField

# Create your models here.


class Item(models.Model):
    SHIRT = 'S'
    SPORT_WEAR = 'SW'
    OUTWEAR = 'OW'
    CATEGORY_CHOICES = [
        (SHIRT, 'Shirt'),
        (SPORT_WEAR, 'Sport Wear'),
        (OUTWEAR, 'Outwear'),
    ]

    PRIMARY = 'P'
    SECONDARY = 'S'
    DANGER = 'D'
    LABEL_CHOICES = [
        (PRIMARY, 'primary'),
        (SECONDARY, 'secondary'),
        (DANGER, 'danger'),
    ]
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product_url", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("core:add-product_url", kwargs={"slug": self.slug})
    
    def get_remove_from_cart_url(self):
        return reverse("core:remove-product_url", kwargs={"slug": self.slug})



class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} of {self.item.title}'
    
    def get_total_price(self):
        if self.item.discount_price:
            return self.quantity * self.item.discount_price
        return self.quantity * self.item.price


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20,blank=True,null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('Address',related_name='billing_address',on_delete=models.SET_NULL,blank=True,null=True)
    shipping_address = models.ForeignKey('Address',related_name='shipping_address',on_delete=models.SET_NULL,blank=True,null=True)
    payment = models.ForeignKey('Payment',on_delete=models.SET_NULL,blank=True,null=True)
    coupon = models.ForeignKey('Coupon',on_delete=models.SET_NULL,blank=True,null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_price()
        if self.items.all() and self.coupon:
            total -= self.coupon.amount
        return total


class Address(models.Model):
    BILLING = 'B'
    SHIPPING = 'S'
    ADDRESS_CHOICES = [
        (BILLING, 'billing'),
        (SHIPPING, 'shipping')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1,choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,blank=True,null=True)
    amount = models.FloatField()
    timestap = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f'{self.pk}'