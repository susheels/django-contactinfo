import sys

from django import forms
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.utils.safestring import mark_safe

from caktus.decorators import requires_kwarg

from contactinfo import models as contactinfo
from countries.models import Country

class CountrySelect(widgets.Select):
    class Media:
        js = (
            'js/jquery-1.3.2.min.js',
        )
    
    def _javascript(self, name):
        url_base = reverse('get_address_form_html', args=('COUNTRY_TOKEN',))
        return mark_safe("""
<script type="text/javascript">
jQuery(function ($) {
    $('select[name=%s]').change(function (e) {
        var url_base = '%s';
        var country = $(e.target).val();
        var url = url_base.replace('COUNTRY_TOKEN', country);
        $.get(url, function(data, textStatus) {
            var street = $('#id_street').val();
            var city = $('#id_city').val();
            var state_province = $('#id_state_province').val();
            var postal_code = $('#id_postal_code').val();
            
            $('tbody.address_form').html(data);
            
            $('#id_street').val(street);
            $('#id_city').val(city);
            $('#id_state_province').val(state_province);
            $('#id_postal_code').val(postal_code);
        });
    });
});
</script>""" % (name, url_base))

    def render(self, name, value, attrs=None, choices=()):
        return super(CountrySelect, self).render(
            name, value, attrs, choices,
        ) + self._javascript(name)


class LocationForm(forms.ModelForm):
    class Meta:
        model = contactinfo.Location
        fields = ('type', 'country',)

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['country'].widget = \
          CountrySelect(choices=self.fields['country'].widget.choices)

  
class AddressForm(forms.ModelForm):
    """
    Model form for international postal addresses in localflavor countries.
    """
    IMPORT_BASE = 'django.contrib.localflavor.%s.forms'
    class Media:
        css = {
            'all': ('css/django-contactinfo.css',),
        }
    
    class Meta:
        model = contactinfo.Address
        fields = ('street', 'city', 'state_province', 'postal_code',)
    
    def _get_class(self, iso, field_name):
        path = AddressForm.IMPORT_BASE % iso.lower()
        try:
            __import__(path)
        except ImportError:
            return None
        module = sys.modules[path]
        try:
            return getattr(module, iso.upper() + field_name)
        except AttributeError:
            return None
        
    def _get_state_province_field(self, iso):
        field_names = (
            (_('State'), 'StateField', 'StateSelect'),
            (_('Province'), 'ProvinceField', 'ProvinceSelect'),
            (_('Department'), 'DepartmentField', 'DepartmentSelect'),
        )
        widget = None
        field = None
        for label, field_name, widget_name in field_names:
            field = self._get_class(iso, field_name)
            widget = self._get_class(iso, widget_name)
            if field or widget:
                break
        if not field and not widget:
            label = _('State or Province')
        if not field:
            field = forms.CharField
        if widget:
            return field(label=label, widget=widget)
        else:
            return field(label=label)
        
    def _get_postal_code_field(self, iso):
        field_names = (
            (_('Zip Code'), 'ZipCodeField'),
            (_('Postcode'), 'PostcodeField'),
            (_('Post Code'), 'PostCodeField'),
            (_('Postal Code'), 'PostalCodeField'),
        )
        for label, field_name in field_names:
            field = self._get_class(iso, field_name)
            if field:
                break
        if not field:
            field = forms.CharField
            label = _('Postal Code')
        return field(label=label)
    
    @requires_kwarg('country')
    def __init__(self, *args, **kwargs):
        self.country = kwargs.pop('country')
        super(AddressForm, self).__init__(*args, **kwargs)
        
        if self.country and self.country.iso:
            self.fields['postal_code'] = \
              self._get_postal_code_field(self.country.iso)
            self.fields['state_province'] = \
              self._get_state_province_field(self.country.iso)


class PhoneForm(forms.ModelForm):
    """
    Model form for Phones.  The required type argument to __init__ should be
    one of the types defined in Phone.PHONE_TYPES, and the label on the
    form field will be set accordingly.  The profile is passed into save()
    instead of __init__ because it may not exist at the time __init__
    is called.
    """
    
    class Meta:
        model = contactinfo.Phone
        fields = ('number', )
    
    @requires_kwarg('type')
    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop('type')
        super(PhoneForm, self).__init__(*args, **kwargs)
        
        self.fields['number'].label = \
          dict(crm.Phone.PHONE_TYPES)[self.type]
        if self.type != 'fax':
            self.fields['number'].label += " phone"
        self.fields['number'].required = False
        
    @transaction.commit_on_success
    def save(self, profile):
        instance = super(PhoneForm, self).save(commit=False)
        new_instance = not instance.id
        if self.cleaned_data['number']:
            instance.profile = profile
            instance.type = self.type
            instance.save()
            self.save_m2m()
        else:
            if not new_instance:
                # if the number was removed, delete the instance
                instance.delete()
            instance = None
        return instance
