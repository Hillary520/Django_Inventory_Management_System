from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Max, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import ListView
from django import forms
from inventory.forms import InventoryItemForm, ItemCategoryForm, StaffDepartmentForm, StockHistoryForm, EmployeeForm
from inventory.models import InventoryItem, Quantity, Employee, StockHistory, StaffDepartment, IssuedOutHistory, \
    ItemCategory
from inventory.context import get_dashboard_context, get_inventory_context, get_item_details_context, get_combined_report_context, get_department_report_context, get_inflow_report_context, get_outflow_report_context, get_department_dashboard_context, get_department_item_details_context, get_cost_report_context, get_outflow_dashboard_context, get_all_delivered_view_context


def is_ajax(request):
    """
    Check if the provided request is an AJAX request.

    This function checks the headers of the given request to determine whether
    it is an AJAX request. Specifically, it looks for the 'X-Requested-With'
    header and checks if its value is 'XMLHttpRequest'.

    :param request: The HTTP request object. It should have a `headers` attribute
        that contains the HTTP headers of the request.
    :return: A boolean value indicating whether the request is identified as an AJAX
        request (True) or not (False).
    """
    # Check if the request is an AJAX request by looking for the 'X-Requested-With' header
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@login_required
def dashboard(request):
    """
    Handles the rendering of the dashboard view for logged-in users. The function
    retrieves the necessary data for the dashboard through a helper function and
    renders the 'inventory/dashboard.html' template with the context data.

    :param request: The HTTP request object containing metadata about the request
        made by the user.
    :return: An HTTP response object that renders the 'inventory/dashboard.html'
        template with the context data.
    """
    context = get_dashboard_context()
    return render(request, 'inventory/dashboard.html', context)


@login_required
def inventory(request):
    """
    Handles the inventory management functionality of the web application. This
    view manages the creation of new inventory items through a form submission.
    It validates the form data, saves valid inventory items, and renders the
    appropriate response in case of errors.

    The function supports both GET and POST requests:
    - For GET requests, it initializes a new inventory form and renders the
      inventory template with context data.
    - For POST requests, it processes the submitted form data, validates it, and
      either saves a new inventory item upon success or returns an error response
      with the form errors.

    :param request: Django's HttpRequest object representing the received request.
    :return: An HTTP response object. For GET requests, it renders the inventory
        HTML view with context. For POST requests, it returns a JSON response
        indicating success or failure, with additional form HTML in case of a
        failure.
    """
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.added_by = request.user
            item.date_added = timezone.now()
            item.save()
            return JsonResponse({'success': True})
        else:
            # Render the form with errors and return as HTML
            form_html = render_to_string('inventory/inventory.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = InventoryItemForm()

    context = get_inventory_context(form)  # Get context data for the inventory view
    return render(request, 'inventory/inventory.html', context)

@login_required
def add_category(request):
    """
    Handles the addition of a new category through an HTTP request. If the request
    method is POST and the submitted form data is valid, it saves the category
    with the current user and timestamp, then returns a JSON response indicating
    success. If the form is not valid, it renders the form with errors and returns
    the corresponding HTML as part of a JSON response. For non-POST requests, it
    renders a blank form for adding a category.

    :param request: The HTTP request object containing method and form data relevant
        for adding a new category.
    :return: A JSON response indicating success if the category was added
        successfully, or containing rendered HTML of the form if the data was invalid.
        For non-POST requests, renders and returns the category addition form within
        an HTML response.
    """
    if request.method == 'POST':
        form = ItemCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.added_by = request.user
            category.date_added = timezone.now()
            category.save()
            return JsonResponse({'success': True})
        else:
            form_html = render_to_string('inventory/inventory.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = ItemCategoryForm()

    return render(request, 'inventory/inventory.html', {'category_form': form})


@login_required
def add_department(request):
    """
    Handles the addition of a new department in the system. This view processes both
    GET and POST requests. For POST requests, it validates the form data and saves
    the department to the database. For GET requests, it renders the department
    form.

    :param request: The HTTP request object.

    :return: A JsonResponse indicating success or failure during form submission in
        case of a POST request. For a GET request, renders a template with the
        department form.
    """
    if request.method == 'POST':
        form = StaffDepartmentForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.added_by = request.user
            category.date_added = timezone.now()
            category.save()
            return JsonResponse({'success': True})
        else:
            form_html = render_to_string('inventory/inventory.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        department_form = StaffDepartmentForm()

    return render(request, 'inventory/inventory.html', {'department_form': department_form})


@login_required
def item_details(request, item_id):
    """
    Handles the details and management of a specific inventory item based on the
    provided item identifier. Enables creating and updating stock history entries
    and associated quantity records for the specific item and its departments. This
    view supports both HTTP POST and GET methods for handling stock data.

    :param request: The HTTP request object, required for matching the state of the
        HTTP request (either GET or POST) and``` accessingpython associated
     user"""
    if request.method == 'POST':
        stock_form = StockHistoryForm(request.POST, item_id=item_id)
        if stock_form.is_valid():
            new_stock = stock_form.save(commit=False)
            new_stock.added_by = request.user
            new_stock.item = get_object_or_404(InventoryItem, id=item_id)

            # Set optional fields if provided
            if 'expiry_date' in stock_form.cleaned_data:
                new_stock.expiry_date = stock_form.cleaned_data['expiry_date']
            if 'depreciation_date' in stock_form.cleaned_data:
                new_stock.depreciation_date = stock_form.cleaned_data['depreciation_date']
            new_stock.save()

            department = stock_form.cleaned_data['department']
            try:
                # Update existing quantity for the item in the department
                existing_quantity = Quantity.objects.get(item=new_stock.item, department=department)
                existing_quantity.quantity += stock_form.cleaned_data['quantity']
                if 'expiry_date' in stock_form.cleaned_data:
                    existing_quantity.expiry_date = stock_form.cleaned_data['expiry_date']
                if 'depreciation_date' in stock_form.cleaned_data:
                    existing_quantity.depreciation_date = stock_form.cleaned_data['depreciation_date']
                existing_quantity.save()
            except Quantity.DoesNotExist:
                # Create a new quantity record if it does not exist
                new_quantity = Quantity(
                    item=new_stock.item,
                    department=department,
                    quantity=stock_form.cleaned_data['quantity'],
                )
                if 'expiry_date' in stock_form.cleaned_data:
                    new_quantity.expiry_date = stock_form.cleaned_data['expiry_date']
                if 'depreciation_date' in stock_form.cleaned_data:
                    new_quantity.depreciation_date = stock_form.cleaned_data['depreciation_date']
                new_quantity.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'form_html': stock_form.as_p()})
    else:
        stock_form = StockHistoryForm(item_id=item_id)

    context = get_item_details_context(item_id, stock_form)
    return render(request, 'inventory/item_details.html', context)


def add_employee(request):
    """
    Handles the addition of an employee to the system. Processes POST requests
    containing employee information via an EmployeeForm. On successful form
    validation, it saves the data and returns a JSON response indicating success.
    If the form is invalid, it returns the form with errors in the response. For
    handling GET requests, it renders the form on the inventory page.

    :param request: The HTTP request object containing metadata about the request
        and any submitted data.
    :return: For a POST request, returns a JsonResponse indicating success or
        failure, and optionally includes the form HTML with errors. For a GET
        request, renders a template containing the employee form.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'form_html': form.as_p()})

    # For initial GET request (if needed to render the form directly)
    form = EmployeeForm()
    return render(request, 'inventory/inventory.html', {'form': form})


@login_required
def issue_out(request):
    """
    Handles the issuance of inventory items to employees by processing POST
    requests. Updates the available quantity of items and logs the transaction
    in the IssuedOutHistory model. Verifies that the issued quantity does not
    exceed the current stock.

    :param request: The HTTP request object containing the details of the
        issuance transaction, such as item ID, quantity, department, and
        employee to whom the item is issued.
    :returns: A JsonResponse indicating the success or failure of the operation.
        In case of failure, an error message explaining the reason is included.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity_id = request.POST.get('quantity_id')
        department_id = request.POST.get('department_id')
        issued_quantity = int(request.POST.get('quantity'))
        issue_voucher_number = request.POST.get('issue_voucher_number')
        issued_to_id = request.POST.get('issued_to')

        # Fetch the quantity entry for the item and department
        quantity_entry = get_object_or_404(Quantity, id=quantity_id)
        # Fetch the employee to whom the item is issued
        issued_to = get_object_or_404(Employee, id=issued_to_id, department__id=department_id)
        # Fetch the office of the employee
        office = Employee.objects.get(id=issued_to_id).office
        # Fetch the department
        department = get_object_or_404(StaffDepartment, id=department_id)
        # Fetch the inventory item
        item = get_object_or_404(InventoryItem, id=item_id)

        # Check if the issued quantity exceeds the available quantity
        if issued_quantity > quantity_entry.quantity:
            return JsonResponse({'success': False, 'error': 'Issued quantity cannot exceed available quantity.'})

        # Reduce the available quantity
        quantity_entry.quantity -= issued_quantity
        quantity_entry.save()

        # Create an IssuedOutHistory record
        IssuedOutHistory.objects.create(
            item=item,
            description=item.description,
            quantity_issued_out=issued_quantity,
            issue_voucher_number=issue_voucher_number,
            issued_to=issued_to,
            department=department,
            office=office,
            issued_by=request.user
        )

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def combined_report(request):
    """
    Generate and render a combined report view.

    This function generates the context for the combined report view
    based on the application's business rules and renders the
    corresponding HTML template with the generated context. The
    combined report provides users with an overview of aggregated
    data from multiple sources or modules.

    :param request: The HTTP request object providing metadata about
                    the request such as headers, user details, and
                    request method.
    :return: An HTTP response object rendering the 'combined_report.html'
             template populated with the generated context.
    """
    context = get_combined_report_context()
    return render(request, 'reports/combined_report.html', context)


def department_report(request, department_id, decimal_default=None):
    """
    Generates and renders a department-specific report based on the provided
    department ID and optional decimal default parameter.

    The function fetches the required data utilizing the department ID and an
    optional decimal default value to structure the department's report context.
    The function then renders a report page with the generated context.

    :param request: The HTTP request object that triggered this
        function, typically containing metadata about the request.
    :param department_id: A unique identifier representing the department
        for which the report will be generated.
    :param decimal_default: Optional. A decimal value to be used as a
        default parameter for calculation or data presentation purposes.
        Defaults to None if not provided.
    :return: An HTTP response object containing the rendered department
        report page.
    """
    context = get_department_report_context(department_id, decimal_default)
    return render(request, 'reports/department_report.html', context)


def inflow_report(request):
    """
    Generate and render the inflow report based on the provided request.

    This function prepares the necessary context for the inflow report by
    utilizing the `get_inflow_report_context` helper function. Once the
    context is created, the function renders the 'inflow_report.html' template
    along with the generated context and returns the response.

    :param request: The HTTP request object containing the request data.
    :return: An HTTP response rendering the inflow report page.
    """
    context = get_inflow_report_context()
    return render(request, 'reports/inflow_report.html', context)


def outflow_report(request):
    """
    Generate an outflow report by preparing the required context and rendering a template.

    This function retrieves the necessary context data for an outflow report and
    renders the "inventory/outflow_dashboard.html" template using the retrieved
    context.

    :param request: The HTTP request object containing metadata and user information
        associated with the request.
    :return: An HTTP response object that contains the rendered "inventory/outflow_dashboard.html"
        template.
    """
    context = get_outflow_report_context()
    return render(request, 'inventory/outflow_dashboard.html', context)


def department_dashboard(request, department_id):
    """
    Renders the department dashboard page with relevant context data.

    The function fetches context data related to the given department
    ID and renders it into the specified HTML template.

    :param request: The HTTP request object.
    :param department_id: The unique identifier for the department.
    :return: The rendered HTML page as an HTTP response.
    """
    context = get_department_dashboard_context(department_id)
    return render(request, 'inventory/department_dashboard.html', context)


def department_item_details(request, item_id, department_id=None):
    """
    Retrieve and render the details of a specific item within a department. This function
    fetches the necessary context data for an item in a given department and renders it
    to the corresponding template for display.

    :param request: The HTTP request object containing metadata about the HTTP request.
    :param item_id: The ID of the item whose details are to be retrieved.
    :param department_id: (Optional) The ID of the department to which the item belongs.
        Defaults to None if not provided.
    :return: An HTTP response object containing the rendered HTML page with the
        department item details.
    """
    context = get_department_item_details_context(item_id, department_id)
    return render(request, 'inventory/department_item_details.html', context)


def cost_report(request):
    """
    Generates the cost report view by preparing the necessary context and rendering it to
    the specified HTML template. This function utilizes a helper method to gather context
    data required for rendering the cost report.

    :param request: Django HttpRequest object representing the incoming HTTP request.

    :return: HttpResponse object containing the rendered cost report page.
    """
    context = get_cost_report_context()
    return render(request, 'reports/cost_report.html', context)

def outflow_dashboard(request):
    """
    Renders the Outflow Dashboard page for inventory management.

    This function retrieves the necessary context data needed to display the
    outflow dashboard of the inventory management system and renders the designated
    HTML page with this information.

    :param request: Django HTTP request object. Contains metadata about the HTTP
        request that triggered this view.
    :return: Rendered HTML response object. Displays the populated outflow dashboard
        template with the retrieved context.
    """
    context = get_outflow_dashboard_context()
    return render(request, 'inventory/outflow_dashboard.html', context)

def ivn_list_view(request):
    """
    Fetches unique Issue Voucher Numbers (IVNs) along with their latest issue date
    and the corresponding department, and renders them in the provided template.

    The function queries the `IssuedOutHistory` model to retrieve distinct IVNs,
    annotating them with the latest associated date and department name. The results
    are sorted in descending order by the latest date before being passed to the template.

    :param request: Django HttpRequest object containing metadata about the request.
    :return: HttpResponse object rendering the `ivn_list.html` template populated
             with a list of unique IVNs, latest dates, and department names.
    """
    # Get unique IVNs with their latest date and department
    ivns = IssuedOutHistory.objects.values('issue_voucher_number').annotate(
        latest_date=Max('date'),
        department=F('department__Department_name')
    ).order_by('-latest_date')

    return render(request, 'inventory/ivn_list.html', {'ivns': ivns})


def ivn_detail_view(request):
    """
    Fetches and returns details associated with a specific Issue Voucher Number (IVN) requested by the user.
    This includes items issued under the given IVN, their descriptions, quantities, the person issued to,
    and the overall total value of these items at the time of issuance.

    :param request: HttpRequest object containing metadata about the request, including the IVN
        as a GET parameter.
    :return: A JsonResponse containing details of the IVN, such as the total number of items,
        total value of items issued, and an array of detailed item data.
    """
    ivn = request.GET.get('ivn')
    if not ivn:
        return JsonResponse({'error': 'No IVN provided'}, status=400)

    # Fetch items associated with the given IVN
    items = IssuedOutHistory.objects.filter(issue_voucher_number=ivn).select_related('item', 'issued_to', 'department')

    # Calculate total value of the items issued under this IVN
    total_value = StockHistory.objects.filter(
        item__in=items.values('item'),
        date_added__lte=items.first().date  # Assume we want the stock value at the time of issuance
    ).aggregate(total_value=Sum(F('unit_cost') * F('quantity')))['total_value'] or 0

    # Prepare item data for the response
    item_data = [{
        'item': item.item.item_name,
        'description': item.description,
        'quantity': item.quantity_issued_out,
        'issued_to': item.issued_to.name,
        'office': item.office,
    } for item in items]

    # Prepare the response data
    data = {
        'ivn': ivn,
        'total_items': len(item_data),
        'total_value': float(total_value),
        'items': item_data,
    }

    return JsonResponse(data)


def all_delivered_view(request):
    """
    Retrieves the context for all delivered items and renders the respective HTML page.

    This function is used to manage the view for displaying all delivered items
    within an inventory system. It fetches the context data needed for the
    template and renders `all_delivered.html`.

    :param request: The HTTP request object containing metadata about the request.

    :return: The HTTP response object containing the rendered HTML page.
    """
    context = get_all_delivered_view_context()
    return render(request, 'inventory/all_delivered.html', context)

def delivery_numbers_list(request):
    """
    Retrieves a list of distinct delivery numbers and their associated 'date_added'
    from the StockHistory database. The results are ordered in descending order
    by 'date_added' and are sent to the 'delivery_numbers.html' template for
    rendering.

    :param request: The HTTP request object representing the client’s request.
    :return: An HTTP response object with the rendered list of delivery numbers.
    """
    delivery_numbers = StockHistory.objects.values('delivery_number', 'date_added').distinct().order_by('-date_added')
    return render(request, 'inventory/delivery_numbers.html', {'delivery_numbers': delivery_numbers})


def get_delivery_details(request, delivery_number):
    """
    Fetch delivery details for the specified delivery number, including the list of stock
    items associated with it, their details, and overall statistics like total value
    and item count. This includes converting decimal values into float for JSON
    serialization and aggregating data for summary metrics.

    :param request: The HTTP request object, typically containing metadata about the user
        or session and additional request-related information.
    :param delivery_number: The identifier for the delivery whose details need to be
        retrieved.
    :return: A JSON response containing the delivery details including item count,
        total value of stock items, and a list of the items with their respective
        details.
    """
    # Fetch stock items associated with the given delivery number
    stock_items = StockHistory.objects.filter(delivery_number=delivery_number)

    # Extract relevant fields from the stock items
    items = stock_items.values(
        'item__item_name',
        'quantity',
        'unit_cost',
        'total_cost'
    )

    # Convert Decimal fields to float for JSON serialization
    items = [
        {
            'item_name': item['item__item_name'],
            'quantity': item['quantity'],
            'unit_cost': float(item['unit_cost']),
            'total_cost': float(item['total_cost'])
        }
        for item in items
    ]

    # Calculate the total value of the stock items
    total_value = stock_items.aggregate(total=Sum('total_cost'))['total'] or 0
    # Count the number of distinct items in the stock items
    item_count = stock_items.aggregate(count=Count('item', distinct=True))['count'] or 0

    # Prepare the response data
    data = {
        'item_count': item_count,
        'total_value': float(total_value),
        'items': items
    }

    return JsonResponse(data)


def lpo_numbers_list(request):
    """
    Fetches a distinct list of LPO numbers along with their 'date added',
    ordered by the most recent 'date added', and renders the results
    into the 'lpo_numbers.html' template.

    :param request: The HTTP request object provided in the current context.
                    This is required to handle the incoming HTTP request and
                    render the associated response.

    :return: An HTTP response object rendering the 'lpo_numbers.html' template
             with the context containing the distinct LPO numbers and their
             respective 'date added'.
    """
    # Fetch distinct LPO numbers along with their date added, ordered by the most recent date added
    lpo_numbers = StockHistory.objects.values('lpo', 'date_added').distinct().order_by('-date_added')
    return render(request, 'inventory/lpo_numbers.html', {'lpo_numbers': lpo_numbers})

def get_lpo_details(request, lpo_number):
    """
    Fetches and returns details related to the specified LPO (Local Purchase Order).

    The function retrieves stock items associated with the provided LPO number,
    extracts relevant fields (such as item name, quantity, unit cost, and total
    cost), and calculates the total value of all items and the count of distinct
    items. It also determines the supplier of the stock items. The data is
    returned as a JSON response.

    :param request: The HTTP request object containing request metadata.
    :param lpo_number: The LPO number used to fetch the associated stock details.
    :return: JSON response containing the stock item details, total value, item
        count, and supplier information.
    """
    # Fetch stock items associated with the given LPO number
    stock_items = StockHistory.objects.filter(lpo=lpo_number)

    # Extract relevant fields from the stock items
    items = stock_items.values(
        'item__item_name',
        'quantity',
        'unit_cost',
        'total_cost'
    )

    # Convert Decimal fields to float for JSON serialization
    items = [
        {
            'item_name': item['item__item_name'],
            'quantity': item['quantity'],
            'unit_cost': float(item['unit_cost']),
            'total_cost': float(item['total_cost'])
        }
        for item in items
    ]

    # Calculate the total value of the stock items
    total_value = stock_items.aggregate(total=Sum('total_cost'))['total'] or 0
    # Count the number of distinct items in the stock items
    item_count = stock_items.aggregate(count=Count('item', distinct=True))['count'] or 0
    # Get the supplier of the first stock item, or 'N/A' if no stock items exist
    supplier = stock_items.first().supplied_by if stock_items.exists() else 'N/A'

    # Prepare the response data
    data = {
        'item_count': item_count,
        'total_value': float(total_value),
        'supplier': supplier,
        'items': items
    }

    return JsonResponse(data)

def add_engraved_stock(request, item_id):
    """
    Adds new engraved stock items to the inventory.

    This function processes an HTTP POST request to add stock corresponding to an
    inventory item with engraved numbers. It validates the given data to ensure
    the quantity of stock matches the provided engraved numbers and updates both
    the `StockHistory` and `Quantity` tables. If the record associated with the
    specified item and department already exists, the quantity is updated. Otherwise,
    a new record in the `Quantity` table is created. It also provides appropriate
    responses in case of errors or successful operation.

    :param request:
        The HTTP request object containing the data related to the stock addition.
        Must be a POST request containing necessary fields for the stock addition.
    :param item_id:
        The identifier of the inventory item for which engraved stock
        is to be added.
    :return:
        A JsonResponse indicating success or failure of the operation. If the
        operation is successful, a response containing 'success': True is returned.
        Otherwise, an error message and 'success': False are provided in the response.

    """
    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == "POST":
        quantity = int(request.POST.get('quantity'))
        engraved_numbers = request.POST.getlist('engraved_numbers[]')

        # Ensure the number of engraved numbers matches the quantity
        if len(engraved_numbers) != quantity:
            return JsonResponse({'success': False, 'error': 'Number of engraved numbers does not match quantity.'})

        department_id = request.POST.get('department')
        unit_cost = request.POST.get('unit_cost')
        lpo = request.POST.get('lpo')
        supplied_by = request.POST.get('supplied_by')
        delivery_number = request.POST.get('delivery_number')
        date_added = request.POST.get('date_added')

        department = get_object_or_404(StaffDepartment, id=department_id)

        for engraved_number in engraved_numbers:
            new_stock = StockHistory(
                item=item,
                department_id=department_id,
                quantity=1,  # Each item has a quantity of 1
                unit_cost=unit_cost,
                total_cost=unit_cost,
                lpo=lpo,
                supplied_by=supplied_by,
                delivery_number=delivery_number,
                engraved_number=engraved_number,
                date_added=date_added,
                added_by=request.user
            )
            new_stock.save()

            # Update the Quantity table
            try:
                existing_quantity = Quantity.objects.get(item=item, department=department)
                existing_quantity.quantity += 1
                existing_quantity.save()
            except Quantity.DoesNotExist:
                new_quantity = Quantity(
                    item=item,
                    department=department,
                    quantity=1,
                )
                new_quantity.save()

        return JsonResponse({'success': True})

    else:
        form = StockHistoryForm()

    return JsonResponse({'success': True})


def engraved_issue_out(request):
    """
    Handles the issuance of engraved inventory items. This function processes a POST
    request to issue an item, updates inventory quantities, marks the item as
    issued, and records the transaction history. The function ensures that the
    issued quantity does not exceed the available stock and associates the issued
    item with the relevant employee, department, and office.

    :param request: Django HttpRequest object containing POST data required to process
        the issuance.
        - item_id: ID of the inventory item to be issued (str)
        - engraved_number: Unique identifier for the engraved item (str)
        - quantity_id: ID of the quantity entry in the database (str)
        - department_id: ID of the staff department issuing the item (str)
        - issue_voucher_number: Voucher number for the issuance transaction (str)
        - issued_to: ID of the employee to whom the item is being issued (str)
    :return: JsonResponse indicating the success or failure of the method.

    :return: JSON response with a success flag. If successful, it returns
        `{'success': True}`. If there is an error, it includes an error message,
        such as `{'success': False, 'error': 'description of the error'}`.

    :raises Http404: If any of the provided IDs (item_id, engraved_number,
        quantity_id, department_id, issued_to) do not correspond to existing
        records in the database.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        engraved_number = request.POST.get('engraved_number')
        quantity_id = request.POST.get('quantity_id')
        department_id = request.POST.get('department_id')
        issued_quantity = 1
        issue_voucher_number = request.POST.get('issue_voucher_number')
        issued_to_id = request.POST.get('issued_to')

        # Fetch the quantity entry for the item and department
        quantity_entry = get_object_or_404(Quantity, id=quantity_id)
        # Fetch the employee to whom the item is issued
        issued_to = get_object_or_404(Employee, id=issued_to_id, department__id=department_id)
        # Fetch the office of the employee
        office = Employee.objects.get(id=issued_to_id).office
        # Fetch the department
        department = get_object_or_404(StaffDepartment, id=department_id)
        # Fetch the inventory item
        item = get_object_or_404(InventoryItem, id=item_id)

        # Check if the issued quantity exceeds the available quantity
        if issued_quantity > quantity_entry.quantity:
            return JsonResponse({'success': False, 'error': 'Issued quantity cannot exceed available quantity.'})

        # Reduce the available quantity
        quantity_entry.quantity -= issued_quantity
        quantity_entry.save()

        # Get the StockHistory instance or return a 404 error if not found
        item_stock_history = get_object_or_404(StockHistory, engraved_number=engraved_number)
        # Mark the item as issued
        item_stock_history.issued = True
        item_stock_history.save()

        # Create an IssuedOutHistory record
        IssuedOutHistory.objects.create(
            item=item,
            description=item.description,
            engraved_number=engraved_number,
            quantity_issued_out=issued_quantity,
            issue_voucher_number=issue_voucher_number,
            issued_to=issued_to,
            department=department,
            office=office,
            issued_by=request.user  # The current logged-in user
        )

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})



class IssuedOutFilterForm(forms.Form):
    """
    Form for filtering issued out items.

    This form is used to filter issued out items based on various criteria such as
    engraved number, item name, category, department, and a date range (start_date to
    end_date). It is primarily used in contexts where detailed and customizable filtering
    on issued out items is required.

    :ivar engraved_number: Filter field for specifying engraved number associated with
                           the issued out items.
    :type engraved_number: forms.CharField
    :ivar item_name: Filter field for specifying the name of the item.
    :type item_name: forms.CharField
    :ivar category: Filter field for specifying the category of the item.
    :type category: forms.ModelChoiceField
    :ivar department: Filter field for specifying the department related to the
                      issued out items.
    :type department: forms.ModelChoiceField
    :ivar start_date: Filter field for specifying the start date of the issue period.
    :type start_date: forms.DateField
    :ivar end_date: Filter field for specifying the end date of the issue period.
    :type end_date: forms.DateField
    """
    engraved_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Filter by engraved number"
    )
    item_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Filter by item name"
    )
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Categories",
        help_text="Filter by item category"
    )
    department = forms.ModelChoiceField(
        queryset=StaffDepartment.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Departments",
        help_text="Filter by department"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Filter by start date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Filter by end date"
    )



class AllIssuedOutView(ListView):
    """
    View for displaying a paginated list of issued-out items with filtering capabilities.

    This class handles the functionality for listing issued-out inventory items. It uses
    filtering options provided by the `IssuedOutFilterForm` to enable users to narrow
    down the displayed queryset of issued-out items. The filtered and paginated results
    are rendered on the specified template. Additional context, such as the filtering
    form itself, is provided to the template for rendering.

    :ivar model: The model representing issued-out items in the database.
    :type model: IssuedOutHistory
    :ivar template_name: The path to the HTML template for the view.
    :type template_name: str
    :ivar context_object_name: The name of the context variable used in the template
        for the queryset of issued-out items.
    :type context_object_name: str
    :ivar paginate_by: The number of queryset items displayed per page in the template.
    :type paginate_by: int
    """
    model = IssuedOutHistory
    template_name = 'inventory/all_issued_out.html'
    context_object_name = 'issued_out_items'
    paginate_by = 20  # Adjust as needed

    def get_queryset(self):
        """
        Returns the queryset of issued out items, filtered based on the form inputs.

        Returns:
            QuerySet: The filtered queryset of issued out items.
        """
        queryset = super().get_queryset()
        form = IssuedOutFilterForm(self.request.GET)

        if form.is_valid():
            engraved_number = form.cleaned_data.get('engraved_number')
            item_name = form.cleaned_data.get('item_name')
            category = form.cleaned_data.get('category')
            department = form.cleaned_data.get('department')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            # Apply filters based on form inputs
            if engraved_number:
                queryset = queryset.filter(engraved_number__icontains=engraved_number)
            if item_name:
                queryset = queryset.filter(item__item_name__icontains=item_name)
            if category:
                queryset = queryset.filter(item__category=category)
            if department:
                queryset = queryset.filter(department=department)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = IssuedOutFilterForm(self.request.GET)
        return context

class AssetFilterForm(forms.Form):
    """
    Provides a form for filtering assets in the database based on various criteria.

    This class is designed for creating a Django form that allows users
    to filter assets by item name, category, department, start date,
    and end date. Each form field includes appropriate widgets and help
    text to guide the user. The form can be utilized in views to perform
    filtering operations.

    :ivar item_name: An optional char field used for filtering by the name of the item.
    :type item_name: forms.CharField

    :ivar category: An optional model choice field for filtering by the item's category.
    :type category: forms.ModelChoiceField

    :ivar department: An optional model choice field for filtering by the department.
    :type department: forms.ModelChoiceField

    :ivar start_date: An optional date field for filtering assets starting from the provided date.
    :type start_date: forms.DateField

    :ivar end_date: An optional date field for filtering assets up to the provided date.
    :type end_date: forms.DateField
    """
    item_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Filter by item name"
    )
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Categories",
        help_text="Filter by item category"
    )
    department = forms.ModelChoiceField(
        queryset=StaffDepartment.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Departments",
        help_text="Filter by department"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Filter by start date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Filter by end date"
    )



class AssetView(ListView):
    """
    Handles the presentation of issued out items via a paginated view. It filters the
    issued out items based on user-submitted parameters in the GET request.

    This view connects a model, a template, and a queryset to create a filtered list of
    items that the user can search for and interact with through the web interface.

    :ivar model: The model to be used in the list view.
    :type model: Type[Model]

    :ivar template_name: The template name to render the view.
    :type template_name: str

    :ivar context_object_name: The name of the object used to reference the list in the template.
    :type context_object_name: str

    :ivar paginate_by: The number of items displayed per page in the list view.
    :type paginate_by: int
    """
    model = IssuedOutHistory
    template_name = 'inventory/asset_register.html'
    context_object_name = 'issued_out_items'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        form = IssuedOutFilterForm(self.request.GET)

        if form.is_valid():
            item_name = form.cleaned_data.get('item_name')
            category = form.cleaned_data.get('category')
            department = form.cleaned_data.get('department')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            # Apply filters based on form inputs
            if item_name:
                queryset = queryset.filter(item__item_name__icontains=item_name)
            if category:
                queryset = queryset.filter(item__category=category)
            if department:
                queryset = queryset.filter(department=department)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the filter form to the context
        context['form'] = AssetFilterForm(self.request.GET)
        return context


def employee_list(request):
    """
    Fetches and returns a list of employees in JSON format if the request is an AJAX call. Otherwise, it
    renders the employee list HTML template. The response includes employee details such as ID, name,
    department, title, and office.

    :param request: The HttpRequest object containing metadata about the request.
    :return: A JsonResponse object containing employee data if the request is an AJAX call, otherwise
        an HttpResponse object rendering the employee list HTML template.
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        employees = Employee.objects.all()
        data = []
        for employee in employees:
            data.append({
                'id': employee.id,
                'name': employee.name,
                'department': employee.department.Department_name,
                'title': employee.Title,
                'office': employee.office,
            })
        return JsonResponse({'data': data})
    return render(request, 'inventory/employee_list.html')

def save_employee_form(request, form, template_name):
    """
    Saves the employee form data if the request is a POST request and the form is valid.
    Renders an updated employee list and returns a JSON response containing the updated
    form status and employee list.

    :param request: The HTTP request object.
    :param form: The form instance containing the data to be saved.
    :param template_name: The name of the template to be used for rendering the form.
    :return: A JsonResponse containing the form validation status and rendered HTML.
    """
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            employees = Employee.objects.all()
            data['html_employee_list'] = render_to_string('inventory/partial_employee_list.html', {
                'employees': employees
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)

def employee_create(request):
    """
    Handles the creation of an employee by rendering a form and saving the form data if the
    request is a POST. It is responsible for using the `EmployeeForm` to process the input
    and returning a partial HTML template for the response.

    :param request: The HTTP request object that contains metadata about the request,
        including the method type and any POST data submitted with the form.
    :return: A rendered partial template for employee creation passed through
        the `save_employee_form` function.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
    else:
        form = EmployeeForm()
    return save_employee_form(request, form, 'inventory/partial_employee_create.html')

def employee_update(request, pk):
    """
    Handles the update operation for the Employee object. The function retrieves
    an instance of the Employee object using its primary key (pk) and processes
    the submitted form data if the request method is POST. Otherwise, a form
    is initialized with the instance for display.

    Renders a partial HTML template to display the form or to reflect the changes
    made upon successful submission.

    :param request: HttpRequest object that contains metadata about the request.
    :param pk: int, Primary key of the Employee object to be updated.
    :return: HttpResponse object containing the rendered partial HTML for the
        employee update process.
    """
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
    else:
        form = EmployeeForm(instance=employee)
    return save_employee_form(request, form, 'inventory/partial_employee_update.html')

def employee_delete(request, pk):
    """
    Deletes an employee from the database if the HTTP request method is POST. If the
    employee is deleted successfully, the response will include updated employee list HTML.
    If the request method is not POST, a confirmation form will be rendered in the response.

    :param request: The HTTP request object representing the client request.
    :param pk: The primary key that identifies the employee to be deleted.
    :return: JSON response containing either the updated employee list or the confirmation
        form HTML.
    """
    employee = get_object_or_404(Employee, pk=pk)
    data = dict()
    if request.method == 'POST':
        employee.delete()
        data['form_is_valid'] = True
        employees = Employee.objects.all()
        data['html_employee_list'] = render_to_string('inventory/partial_employee_list.html', {
            'employees': employees
        })
    else:
        context = {'employee': employee}
        data['html_form'] = render_to_string('inventory/partial_employee_delete.html', context, request=request)
    return JsonResponse(data)

