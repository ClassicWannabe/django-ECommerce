from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .models import Item, OrderItem, Order, BillingAddress
from .forms import CheckoutForm

# Create your views here.


class HomeView(ListView):
    model = Item
    paginate_by = 5
    template_name = 'home-page.html'
    context_object_name = 'items'


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product-page.html'
    context_object_name = 'item'

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self,*args,**kwargs):
        try:
            object = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.error(self.request,'You do not have an active order')
            return redirect('/')
        return render(self.request,'order-summary.html',{'object':object})


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request,'This item quantity was updated to your cart')
        else:
            messages.info(request,'This item was added to your cart')
            order.items.add(order_item)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,'This item was added to your cart')
    return redirect('core:order-summary_url')

@login_required
def remove_from_cart(request,slug):
    item = get_object_or_404(Item, slug=slug)

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                        item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request,'This item was removed from your cart')
        else:
            messages.info(request,'This item was not in your cart')
    else:
        messages.info(request,'You do not have an active order')
    return redirect('core:product_url', slug=slug)

@login_required
def remove_single_item_from_cart(request,slug):
    item = get_object_or_404(Item, slug=slug)

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                        item=item, user=request.user, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request,'This item quantity was updated')
            else:
                order.items.remove(order_item)
                messages.info(request,'This item was removed from your cart')       
        else:
            messages.info(request,'This item was not in your cart')
    else:
        messages.info(request,'You do not have an active order')
    return redirect('core:order-summary_url')

class CheckoutView(View):
    def get(self,*args,**kwargs):
        form = CheckoutForm()
        return render(self.request, 'checkout-page.html',{'form':form})
    
    def post(self,*args,**kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            object = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: add functionality
                # same_shiping_address = form.cleaned_data.get('same_shiping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                return redirect('core:checkout_url')
        except ObjectDoesNotExist:
            messages.error(self.request,'You do not have an active order')
            return redirect('core:order-summary_url')
        
class PaymentView(View):
    def get(self,*args,**kwargs):
        return render(self.request,'payment.html')


def product(request):
    return render(request, 'product-page.html')
