from decouple import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon, Refund
from .forms import CheckoutForm, CouponForm, RefundForm

import random
import string
import stripe
stripe.api_key = config('STRIPE_SECRET_KEY')


# Create your views here.

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


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
    def get(self, *args, **kwargs):
        try:
            object = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('/')
        return render(self.request, 'order-summary.html', {'object': object})


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
            messages.info(
                request, 'This item quantity was updated to your cart')
        else:
            messages.info(request, 'This item was added to your cart')
            order.items.add(order_item)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart')
    return redirect('core:order-summary_url')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)

    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, 'This item was removed from your cart')
        else:
            messages.info(request, 'This item was not in your cart')
    else:
        messages.info(request, 'You do not have an active order')
    return redirect('core:product_url', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
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
                messages.info(request, 'This item quantity was updated')
            else:
                order.items.remove(order_item)
                messages.info(request, 'This item was removed from your cart')
        else:
            messages.info(request, 'This item was not in your cart')
    else:
        messages.info(request, 'You do not have an active order')
    return redirect('core:order-summary_url')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            form = CheckoutForm()
            return render(self.request, 'checkout-page.html', {'form': form,
                                                                'couponForm':CouponForm(),
                                                                'order':order,
                                                                'DISPLAY_COUPON_FORM':True})
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:checkout_url')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
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

                if payment_option == 'S':
                    return redirect('core:payment_url',payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment_url',payment_option='paypal')
                else:
                    messages.warning(self.request,"Invalid Payment Option Selected")
                    return redirect('core:checkout_url')

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:order-summary_url')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            return render(self.request, 'payment.html',{'order':order,'DISPLAY_COUPON_FORM':False})
        else:
            messages.warning(self.request, 'You have not added a billing addresss')
            return redirect('core:checkout_url')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)
        try:
            # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
                amount=amount,  # cents
                currency="usd",
                source=token,
                description="My First Test Charge (created for API docs)",
            )
            
            # create payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()
            
            messages.success(self.request,'Your order was successful')
            return redirect('/')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            messages.warning(self.request,f"{e.user_message}")
            print('Status is: %s' % e.http_status)
            print('Code is: %s' % e.code)
            # param is '' in this case
            print('Param is: %s' % e.param)
            print('Message is: %s' % e.user_message)
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request,"Rate Limit Error")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request,"Invalid Request")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request,"Not Authenticated")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request,"Network Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request,"Something went wrong. You were not charged. Please try again")
            return redirect('/')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.warning(self.request,"A serious error occurred. We've been notified")
            return redirect('/')

def get_coupon(request,code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.warning(request, 'This code does not exist')
        return redirect('core:checkout_url')


class AddCouponView(View):
    def post(self,*args,**kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user,ordered=False)
                order.coupon = get_coupon(self.request,code)
                order.save()
                messages.success(self.request, 'Successfully added coupon')
                return redirect('core:checkout_url')

            except ObjectDoesNotExist:
                messages.warning(self.request, 'You do not have an active order')
                return redirect('core:checkout_url')
        


def product(request):
    return render(request, 'product-page.html')

class RequestRefundView(View):
    def get(self,*args,**kwargs):
        form = RefundForm
        return render(self.request,'request-refund.html',{'form':form})

    def post(self,*args,**kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data['ref_code']
            message = form.cleaned_data['message']
            email = form.cleaned_data['email']

            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()
            
                refund = Refund(order=order,reason=message,email=email)
                refund.save()

                messages.info(self.request,'Your request was received')

            except ObjectDoesNotExist:
                messages.info(self.request, 'This order does not exist')
            
            return redirect('core:request-refund_url')

