from inventory.models import StaffDepartment


def global_context(request):
    """
    Fetches all staff departments and returns them in a dictionary format.

    The method retrieves all instances of the StaffDepartment model from the
    database and provides them in a context dictionary, which can be used
    in templates or other parts of the application.

    :param request: The HTTP request object that triggers this function.
    :return: A dictionary containing a key 'departments' with a queryset of
        all StaffDepartment instances.
    """
    departments = StaffDepartment.objects.all()
    return {
        'departments': departments,
    }