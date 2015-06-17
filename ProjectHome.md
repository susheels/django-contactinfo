# django-contactinfo #

django-contactinfo is a set of models and forms for managing international locations.  It taps into the localflavor contrib app in Django to provide phone and address validation for all the localities that Django supports.

## Installation ##

To use django-contactinfo, add it to your Python path and INSTALLED\_APPS, then create a view that uses the create\_edit\_location helper, e.g.:

```
from contactinfo import models as contactinfo
from contactinfo import helpers

@permission_required('contactinfo.change_location')
def create_edit_location(request, location_id=None):
    """ 
    This is an example of how to use the create_edit_location helper in your
    own view.  Substitute your own template and action to perform once
    the object is saved.
    """
    if location_id:
        location = get_object_or_404(contactinfo.Location, pk=location_id)
    else:
        location = None
    location, saved, context = helpers.create_edit_location(
        request, 
        location, 
        True,
    )
    if saved:
        if 'next' in request.GET:
            return HttpResponseRedirect(request.GET['next'])
        else:
            edit_url = reverse('edit_location', args=(location.id,))
            return HttpResponseRedirect(edit_url)
    else:
        return render_to_response(
            'contactinfo/create_edit_location.html',
            context,
            context_instance=RequestContext(request)
        )
```