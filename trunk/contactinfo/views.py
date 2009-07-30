from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required

from contactinfo.forms import LocationForm, AddressFormSet, PhoneFormSet
from countries.models import Country
from contactinfo import models as contactinfo

@permission_required('contactinfo.change_location')
def create_edit_location(request, location_id=None):
    if location_id:
        location = get_object_or_404(contactinfo.Location, pk=location_id)
    else:
        location = None
    if request.POST:
        location_form = LocationForm(request.POST, instance=location)
        if location_form.is_valid():
            location = location_form.save(commit=False)
            address_formset = AddressFormSet(
                request.POST, 
                instance=location, 
                prefix='addresses',
            )
            phone_formset = PhoneFormSet(
                request.POST, 
                instance=location, 
                prefix='phones',
            )
            if address_formset.is_valid() and phone_formset.is_valid():
                location.save()
                addresses = address_formset.save(commit=False)
                for address in addresses:
                    address.location = location
                    address.save()
                phones = phone_formset.save(commit=False)
                for phone in phones:
                    phone.location = location
                    phone.save()
                if 'next' in request.GET:
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    edit_url = reverse('edit_location', args=(location.id,))
                    return HttpResponseRedirect(edit_url)
        else:
            address_formset = AddressFormSet(
                request.POST, 
                prefix='addresses',
                instance=location or contactinfo.Location(),
            )
            phone_formset = PhoneFormSet(
                request.POST,
                prefix='phones',
                instance=location or contactinfo.Location(),
            )
    else:
        location_form = LocationForm(instance=location)
        address_formset = AddressFormSet(
            prefix='addresses',
            instance=location or contactinfo.Location(),
        )
        phone_formset = PhoneFormSet(
            prefix='phones',
            instance=location or contactinfo.Location(),
        )
    
    context = {
        'location': location,
        'location_form': location_form,
        'address_formset': address_formset,
        'phone_formset': phone_formset,
    }
    return render_to_response(
        'contactinfo/create_edit_location.html',
        context,
        context_instance=RequestContext(request)
    )


@permission_required('contactinfo.change_location')
def get_address_formset_html(request):
    default_iso = getattr(settings, 'DEFAULT_COUNTRY_ISO', 'US')
    country_iso = request.GET.get('country', default_iso)
    country = get_object_or_404(Country, iso=country_iso.upper())
    if 'location_id' in request.GET:
        location_id = request.GET['location_id']
        location = get_object_or_404(contactinfo.Location, pk=location_id)
    else:
        location = contactinfo.Location()
    location.country = country
    address_formset = AddressFormSet(instance=location)
    return render_to_response(
        'contactinfo/_address_formset.html',
        {'address_formset': address_formset},
        context_instance=RequestContext(request)
    )
    
    