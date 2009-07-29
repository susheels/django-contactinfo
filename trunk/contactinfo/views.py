from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from contactinfo.forms import LocationForm, AddressForm
from countries.models import Country
from contactinfo import models as contactinfo

def create_edit_location(request, location_id=None):
    default_country = Country.objects.get(iso='US')
    if request.POST:
        location_form = LocationForm(request.POST)
        if location_form.is_valid():
            country = location_form.cleaned_data['country']
            address_form = AddressForm(request.POST, country=country)
            if address_form.is_valid():
                location = location_form.save()
                address = address_form.save(commit=False)
                address.location = location
                address.save()
                if 'next' in request.GET:
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    return HttpResponseRedirect('/')
        else:
            address_form = AddressForm(request.POST, country=default_country)
    else:
        location_form = LocationForm()
        address_form = AddressForm(country=default_country)
    context = {
        'address_form': address_form,
        'location_form': location_form,
    }
    return render_to_response(
        'contactinfo/create_edit_location.html',
        context,
        context_instance=RequestContext(request)
    )

def get_address_form_html(request, country_iso):
    country = get_object_or_404(Country, iso=country_iso.upper())
    return HttpResponse(AddressForm(country=country).as_table())
    
    