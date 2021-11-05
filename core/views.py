from django.conf import settings
import stripe
from django.db import models
from django.http import request
from stripe.api_resources import order, source
from .models import Item, Order, OrderItem, Address, Payment, Coupon, Refund, UserProfile
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, CouponForm, RefundForm,PaymentForm
import string
import random

stripe.api_key = settings.STRIPE_PRIVATE_KEY
# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token

# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def products (request):
    context = {
        'items' : Item.objects.all()
    }
    return render(request, 'products.html',context)

def is_valid_form(values):
    valid=True
    for field in values:
        if field == '':
            valid=False
    return valid

class checkoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form':form,
                'couponform':CouponForm(),
                'order':order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'S',
                default = True
            )

            if shipping_address_qs.exists():
                context.update({'default_shipping_address': shipping_address_qs[0]})


            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'B',
                default = True
            )

            if billing_address_qs.exists():
                context.update({'default_billing_address': billing_address_qs[0]})

            return render(self.request,'checkout-page.html',context)


        except ObjectDoesNotExist:
            messages.info(self.request, 'you do not have an active order')
            return redirect("core:checkoutView")
    
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get("use_default_shipping")
                if use_default_shipping:
                    print("Using default shippimg address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type = 'S',
                        default = True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request,"No default shipping address available")
                        return redirect('core:checkoutView')
                else:
                    print("User is entering a new shipping address")
                    shipping_address = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    """ same_shipping_address = form.cleaned_data.get('same_shipping_address')
                    save_info = form.cleaned_data.get('save_info') """
                    if is_valid_form([shipping_address,shipping_country,shipping_zip]):

                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address,
                            apartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip,
                            address_type = 'S'
                        )
                        shipping_address.save()
                        
                        order.shipping_address = shipping_address
                        order.save()
                        
                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default=True
                            shipping_address.save()
                    else:
                        messages.info(self.request,'Please fill in the required shipping address fields')
                
                use_default_billing = form.cleaned_data.get("use_default_billing")
                same_billing_address = form.cleaned_data.get("same_billing_address")

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using default billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type = 'B',
                        default = True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request,"No default billing address available")
                        return redirect('core:checkoutView')
                else:
                    print("User is entering a new billing address")
                    billing_address = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')
                    """ same_shipping_address = form.cleaned_data.get('same_shipping_address')
                    save_info = form.cleaned_data.get('save_info') """
                    if is_valid_form([billing_address,billing_country,billing_zip]):

                        billing_address = Address(
                            user = self.request.user,
                            street_address = billing_address,
                            apartment_address = billing_address2,
                            country = billing_country,
                            zip = billing_zip,
                            address_type = 'B'
                        )
                        billing_address.save()
                        
                        order.billing_address = billing_address
                        order.save()
                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default=True
                            billing_address.save()
                    else:
                        messages.info(self.request,'Please fill in the required billing address fields')        

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'D':
                    return redirect('core:payment', payment_option='Debit')
                elif payment_option == 'C':
                    return redirect('core:payment', payment_option='Credit')
                else:
                    messages.warning(self.request,'invalid payment option selected')
                    return redirect('core:checkoutView')

        except ObjectDoesNotExist:
            messages.warning(self.request,'you do not have active order')
            return redirect('core:order_summary')
        # print(self.request.POST)
        
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order':order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                cards = stripe.Customer.list_sources(userprofile.stripe_customer_id, limit=3, object='card')
                card_list = cards['data']
                if len(card_list) > 0:
                    context.update({
                        'card':card_list[0]
                    })

            return render(self.request, 'payment.html', context)
        else:
            messages.warning(self.request,'you have not added a billing address')
            return redirect('core:checkoutView')
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            print(token)
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if not userprofile.stripe_customer_id:
                    customer = stripe.Customer.create(email=self.request.user.email,source='tok_visa' )
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

                else:
                    stripe.Customer.create_source(
                        userprofile.stripe_customer_id,source='tok_visa'
                    )

            amount = int(order.get_total())
            try:
                if use_default:
    # Use Stripe's library to make requests...
                    charge = stripe.Charge.create(
                            amount = amount,
                            currency="inr",
                            source= userprofile.stripe_customer_id,
                    )
                else:
                    charge = stripe.Charge.create(
                            amount = amount,
                            currency="inr",
                            source= 'tok_visa',
                    )
                    #create payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()


                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request,'successful')
                return redirect('/')

            except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

                print('Status is: %s' % e.http_status)
                print('Code is: %s' % e.code)
                # param is '' in this case
                print('Param is: %s' % e.param)
                print('Message is: %s' % e.user_message)
            except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
                messages.warning(self.request,'Rate limit error')
                return redirect('/')
            except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
                messages.warning(self.request,'invalid request')
                return redirect('/')
            except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
                messages.warning(self.request,'Authentication error')
                return redirect('/')
            except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
                messages.warning(self.request,'Network error')
                return redirect('/')
            except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
                messages.warning(self.request,'Something went wrong you were not charged. Please try again.')
                return redirect('/')
            except Exception as e:
            # Something else happened, completely unrelated to Stripe
                messages.warning(self.request,'A serious error occurred, we have been notified.')
                return redirect('/')
        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")

class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home-page.html'

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object':order
            }
            return render(self.request, 'order_summary.html',context)

        except ObjectDoesNotExist:
            messages.error(self.request,'you do not have active order')
            return render(self.request, 'order_summary.html')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'products.html'

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered = False
        )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request,"This item quantity was updated.")
            return redirect('core:order_summary')

        else:
            order.items.add(order_item)
            messages.info(request,"This item was added to your cart.")
            return redirect('core:order_summary')

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)    
        messages.info(request,"This item was added to your cart.")
    return redirect('core:order_summary')    

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered = False
            )[0]
            order.items.remove(order_item)
            messages.info(request,"This item was removed from your cart.")
            return redirect('core:order_summary')
            
        else:
            messages.info(request,"This item was not in your cart.")
            return redirect('core:products', slug=slug)    
    else:
        messages.info(request,"you do not have an active order")
        return redirect('core:products', slug=slug)
    

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered = False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request,"This item quantity was updated.")
            return redirect('core:order_summary')
            
        else:
            messages.info(request,"This item was not in your cart.")
            return redirect('core:products', slug=slug)    
    else:
        messages.info(request,"you do not have an active order")
        return redirect('core:products', slug=slug )

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, 'this coupon does not exist')
        return redirect("core:checkoutView")



class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if self.request.method == 'POST':
            if form.is_valid():
                try:
                    code = form.cleaned_data.get('code')
                    order = Order.objects.get(user=self.request.user, ordered=False)
                    order.coupon = get_coupon(self.request, code)
                    order.save()
                    messages.success(self.request, 'Successfully added coupon')
                    return redirect("core:checkoutView")

                except ObjectDoesNotExist:
                    messages.info(self.request, 'you do not have an active order')
                    return redirect("core:checkoutView")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, 'request_refund.html',context)

    def post(self, *args, **kwargs):
      form = RefundForm(self.request.POST)
      if form.is_valid():
          ref_code = form.cleaned_data.get('ref_code')
          message = form.cleaned_data.get('message')
          email = form.cleaned_data.get('email')
          try:
              order = Order.objects.get(ref_code=ref_code)
              order.refund_request = True
              order.save()

              refund = Refund()
              refund.order = order
              refund.reason = message
              refund.email = email
              refund.save()
              messages.info(self.request, "Your order request recieved")
              return redirect("core:request_refund")

          except ObjectDoesNotExist:
              messages.info(self.request, "this order does not exist")
              return redirect("core:request_refund")