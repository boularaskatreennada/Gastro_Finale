from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404

from restaurant.decorators import *
from .models import Offer
from .forms import OfferForm
from .models import OfferStatus
from django.utils import timezone

@pdg_required
def offer_list(request):
    today = timezone.now().date()
    
    all_offers = Offer.objects.all()
    
    active_offers = [o for o in all_offers if o.status == OfferStatus.ACTIVE]
    upcoming_offers = [o for o in all_offers if o.status == OfferStatus.UPCOMING]
    expired_offers = [o for o in all_offers if o.status == OfferStatus.EXPIRED]

    context = {
        'all_offers': all_offers,
        'active_offers': active_offers,
        'upcoming_offers': upcoming_offers,
        'expired_offers': expired_offers,
    }
    return render(request, 'pdg/offers.html', context)


@pdg_required
def add_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)  # <-- include request.FILES here
        if form.is_valid():
            form.save()
            return redirect('offers')
    else:
        form = OfferForm()
    return render(request, 'pdg/addOffer.html', {'form': form})


@pdg_required
def edit_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES, instance=offer)

        if form.is_valid():
            form.save()
            return redirect('offers')
    else:
        form = OfferForm(instance=offer)
    return render(request, 'pdg/addOffer.html', {'form': form})

@pdg_required
def delete_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.method == 'POST':
        offer.delete()
        return redirect('offers')
    return render(request, 'pdg/offers.html', {'offer': offer})



def client_offer_list(request):
    today = timezone.now().date()
    offers = Offer.objects.all()

    active_offers = [o for o in offers if o.status == OfferStatus.ACTIVE]

    return render(request, 'client/offers.html', {'active_offers': active_offers})








