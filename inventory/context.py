from collections import defaultdict
import json
from datetime import timedelta
from django.db.models import Sum, F, DecimalField, OuterRef, Subquery, Max, Avg
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from inventory.models import Employee, InventoryItem, ItemCategory, Quantity, IssuedOutHistory, StockHistory, StaffDepartment
from inventory.forms import ItemCategoryForm, StaffDepartmentForm, EmployeeForm, StockHistoryForm

def get_dashboard_context():
    """
    Fetch and calculate a comprehensive dashboard context for an inventory management
    system. This function aggregates and processes various data such as department
    information, inventory statistics, stock trends, and recent activities, and
    formats them for use within a dashboard UI.

    :return: A dictionary containing the complete dashboard context data, including
        details on inventory, stock trends, turnover rates, department statistics,
        recent transactions, and other relevant contextual information for user
        interfaces.
    """
    now = timezone.now()
    current_month_start = now.replace(day=1)
    last_month_start = now - timedelta(days=30)
    six_months_ago = now - timedelta(days=180)

    departments = StaffDepartment.objects.annotate(stock_size=Sum('quantity__quantity'))
    total_items = InventoryItem.objects.count()
    new_items_last_month = InventoryItem.objects.filter(date_added__gte=last_month_start).count()
    new_items_this_month = InventoryItem.objects.filter(date_added__gte=current_month_start).count()
    monthly_change = ((new_items_this_month - new_items_last_month) / new_items_last_month * 100) if new_items_last_month else 0
    low_stock_items = Quantity.objects.filter(quantity__lt=10).count()
    low_stock_percentage = (low_stock_items / total_items) * 100 if total_items else 0
    items_issued = IssuedOutHistory.objects.filter(date__gte=last_month_start).aggregate(Sum('quantity_issued_out'))['quantity_issued_out__sum'] or 0
    current_stock = Quantity.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0
    turnover_rate = (items_issued / current_stock) * 100 if current_stock else 0
    top_issued_items = IssuedOutHistory.objects.values('item__item_name').annotate(total_issued=Sum('quantity_issued_out')).order_by('-total_issued')[:5]
    out_of_stock = Quantity.objects.filter(quantity=0)
    recent_transactions = StockHistory.objects.order_by('-date_added')[:10]
    stock_trends = StockHistory.objects.filter(date_added__gte=six_months_ago) \
        .annotate(month=TruncMonth('date_added')) \
        .values('month') \
        .annotate(total_added=Sum('quantity')) \
        .order_by('month')
    stock_trends = [{'month': trend['month'].strftime('%Y-%m'), 'total_added': trend['total_added']} for trend in stock_trends]
    expiring_soon = Quantity.objects.filter(expiry_date__lte=now + timedelta(days=30)).exclude(expiry_date__isnull=True)

    context = {
        'total_items': total_items,
        'new_items_last_month': new_items_last_month,
        'new_items_this_month': new_items_this_month,
        'monthly_change': round(monthly_change, 2),
        'low_stock_items': low_stock_items,
        'low_stock_percentage': round(low_stock_percentage, 2),
        'turnover_rate': round(turnover_rate, 2),
        'departments_list': json.dumps(list(departments.values()), cls=DjangoJSONEncoder),
        'top_issued_items': json.dumps(list(top_issued_items), cls=DjangoJSONEncoder),
        'out_of_stock': out_of_stock,
        'recent_transactions': recent_transactions,
        'stock_trends': json.dumps(stock_trends, cls=DjangoJSONEncoder),
        'expiring_soon': expiring_soon,
        'departments': departments,
    }
    return context

def get_inventory_context(form):
    """
    Generates an inventory context dictionary for rendering inventory-related data in a template.
    Aggregates comprehensive inventory statistics and initializes associated forms.

    :param form: The main form instance containing the form data being processed.
    :return: A dictionary containing inventory details, statistical data, associated forms, and additional context required for rendering.
    """
    current_date = timezone.now().date()

    def calculate_aggregate(queryset, field):
        return queryset.aggregate(total=Sum(field))['total'] or 0

    total_items = InventoryItem.objects.count()
    total_quantity = calculate_aggregate(Quantity.objects, 'quantity')

    out_of_stock_items = Quantity.objects.filter(quantity=0)
    expired_items = Quantity.objects.filter(expiry_date__lt=current_date)
    depreciated_items = Quantity.objects.filter(depreciation_date__lt=current_date)
    low_stock_items = Quantity.objects.filter(quantity__gt=0, quantity__lt=50)

    def calculate_percentage(part, whole):
        return (part / whole) * 100 if whole > 0 else 0

    context = {
        'form': form,
        'category_form': ItemCategoryForm(),
        'department_form': StaffDepartmentForm(),
        'employee_form': EmployeeForm(),
        'items': InventoryItem.objects.all(),
        'departments': StaffDepartment.objects.all(),
        'total_items': total_items,
        'total_quantity': total_quantity,
        'out_of_stock_percentage': calculate_percentage(calculate_aggregate(out_of_stock_items, 'quantity'), total_quantity),
        'expired_percentage': calculate_percentage(calculate_aggregate(expired_items, 'quantity'), total_quantity),
        'depreciated_percentage': calculate_percentage(calculate_aggregate(depreciated_items, 'quantity'), total_quantity),
        'low_stock_percentage': calculate_percentage(calculate_aggregate(low_stock_items, 'quantity'), total_quantity),
        'out_of_stock_count': out_of_stock_items.count(),
        'expired_count': expired_items.count(),
        'depreciated_count': depreciated_items.count(),
        'low_stock_count': low_stock_items.count(),
    }
    return context

def get_item_details_context(item_id, stock_form):
    """
    Fetches and prepares context data related to a specific inventory item based on its ID.
    The context dictionary includes details such as the inventory item, stock form,
    quantities, employees, stock history, issued out history, and engraved numbers,
    along with additional helper forms and datasets.

    :param item_id: Identifier for the specific inventory item
    :param stock_form: Form instance to manage stock actions for the item
    :return: Dictionary containing item details and related context data
    """
    item = get_object_or_404(InventoryItem, id=item_id)
    employee_form = EmployeeForm()

    engraved_numbers = StockHistory.objects.filter(item=item, issued=False).values_list('engraved_number', flat=True).distinct()
    quantities = Quantity.objects.filter(item=item)
    employees = list(Employee.objects.values('id', 'name', 'department_id'))
    stock_history = StockHistory.objects.filter(item=item).order_by('date_added')
    issued_out_history = IssuedOutHistory.objects.filter(item=item).order_by('date')

    return {
        'item': item,
        'stock_form': stock_form,
        'quantities': quantities,
        'employees': employees,
        'employee_form': employee_form,
        'stock_history': stock_history,
        'issued_out_history': issued_out_history,
        'engraved_numbers': engraved_numbers,
    }

def get_combined_report_context():
    """
    Provides a comprehensive report context derived from inventory data. The function summarizes various metrics on
    inventory stock, including total items, quantities, values, costs, stock movements, supplier data, departmental
    usage, inflow, and expiration details. Additionally, it generates data for visual charts using stock movement and
    supplier information.

    :return: Dictionary containing detailed inventory-related metrics, structured summaries for categories, departments,
             suppliers, stock movements, along with chart data serialized as JSON.
    """
    # Calculate total items and total quantity in inventory
    total_items = InventoryItem.objects.count()
    total_quantity = Quantity.objects.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate total value and cost of stock history
    total_value_and_cost = StockHistory.objects.aggregate(
        total_value=Coalesce(Sum(F('quantity') * F('unit_cost')), 0, output_field=DecimalField()),
        total_cost=Coalesce(Sum('total_cost'), 0, output_field=DecimalField())
    )
    total_value = total_value_and_cost['total_value']
    total_cost = total_value_and_cost['total_cost']

    # Summarize categories and departments
    category_summary = InventoryItem.objects.values('category').annotate(
        total_quantity=Coalesce(Sum('quantity__quantity'), 0),
        total_value=Coalesce(Sum(F('quantity__quantity') * F('stockhistory__unit_cost')), 0, output_field=DecimalField())
    )

    department_summary = Quantity.objects.values('department__Department_name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Coalesce(Sum(F('quantity') * F('item__stockhistory__unit_cost')), 0, output_field=DecimalField())
    )

    # Fetch stock history and issued out history
    today = timezone.now().date()
    stock_history = StockHistory.objects.order_by('-date_added')
    issued_out_history = IssuedOutHistory.objects.order_by('-date')

    # Calculate stock movement
    stock_movement = defaultdict(lambda: {'added': 0, 'issued': 0, 'value_added': 0, 'value_issued': 0})
    for stock in stock_history:
        date_key = stock.date_added.strftime("%Y-%m-%d")
        stock_movement[date_key]['added'] += stock.quantity
        stock_movement[date_key]['value_added'] += stock.total_cost
    for issued in issued_out_history:
        date_key = issued.date.strftime("%Y-%m-%d")
        stock_movement[date_key]['issued'] += issued.quantity_issued_out
        stock_movement[date_key]['value_issued'] += issued.quantity_issued_out * issued.item.stockhistory_set.latest('date_added').unit_cost

    # Prepare data for charts
    stock_dates = list(stock_movement.keys())
    stock_added = [value['added'] for value in stock_movement.values()]
    stock_issued = [value['issued'] for value in stock_movement.values()]
    value_added = [value['value_added'] for value in stock_movement.values()]
    value_issued = [value['value_issued'] for value in stock_movement.values()]

    # Get items expiring and depreciating soon
    expiring_soon = Quantity.objects.filter(expiry_date__lte=today + timezone.timedelta(days=30)).select_related('item', 'department')
    depreciating_soon = Quantity.objects.filter(depreciation_date__lte=today + timezone.timedelta(days=30)).select_related('item', 'department')

    # Summarize suppliers and deliveries
    supplier_summary = StockHistory.objects.values('supplied_by').annotate(
        total_quantity=Sum('quantity'),
        total_cost=Sum('total_cost')
    ).order_by('-total_quantity')

    delivery_summary = StockHistory.objects.values('delivery_number', 'supplied_by').annotate(
        total_quantity=Sum('quantity'),
        total_cost=Sum('total_cost')
    ).order_by('-total_quantity')

    # Prepare data for supplier chart
    labels = [entry['supplied_by'] for entry in supplier_summary]
    data = [entry['total_quantity'] for entry in supplier_summary]

    # Summarize departmental usage and inflow
    departmental_usage = IssuedOutHistory.objects.values('department__Department_name').annotate(
        total_issued=Sum('quantity_issued_out'),
        total_value=Coalesce(Sum(F('quantity_issued_out') * F('item__stockhistory__unit_cost')), 0, output_field=DecimalField())
    ).order_by('-total_issued')

    departmental_inflow = StockHistory.objects.values('department__Department_name').annotate(
        total_added=Sum('quantity'),
        total_cost=Sum('total_cost')
    ).order_by('-total_added')

    # Prepare chart data
    chart_data = {
        'stock_dates': stock_dates,
        'stock_added': stock_added,
        'stock_issued': stock_issued,
        'value_added': [float(value) for value in value_added],
        'value_issued': [float(value) for value in value_issued]
    }

    # Serialize chart data to JSON
    chart_data_json = json.dumps(chart_data, cls=DjangoJSONEncoder)

    # Prepare context dictionary
    context = {
        'total_items': total_items,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_quantity': total_quantity,
        'category_summary': category_summary,
        'department_summary': department_summary,
        'stock_dates': stock_dates,
        'stock_added': stock_added,
        'stock_issued': stock_issued,
        'value_added': value_added,
        'value_issued': value_issued,
        'stock_history': stock_history,
        'issued_out_history': issued_out_history,
        'expiring_soon': expiring_soon,
        'depreciating_soon': depreciating_soon,
        'supplier_summary': supplier_summary,
        'delivery_summary': delivery_summary,
        'departmental_usage': departmental_usage,
        'labels': labels,
        'data': data,
        'departmental_inflow': departmental_inflow,
        'chart_data_json': chart_data_json,
    }
    return context

def get_department_report_context(department_id, decimal_default=None):
    """
    Generate context data for reporting a department, including details about item
    distribution, stock movement, issued items, and related charts.

    :param department_id: Identifier of the department for which the report context
                          should be generated.
    :param decimal_default: Optional default function for serializing decimal values
                            to JSON.
    :return: The context dictionary containing department details, stock movement,
             item distributions, issued items distributions, and serialized chart
             data.
    """
    department = get_object_or_404(StaffDepartment, pk=department_id)
    items_in_department = Quantity.objects.filter(department=department)
    stock_history = StockHistory.objects.filter(department=department)
    issued_history = IssuedOutHistory.objects.filter(department=department)

    item_distribution = defaultdict(lambda: {'quantity': 0, 'value': 0})
    stock_movement = defaultdict(lambda: {'added': 0, 'issued': 0, 'value_added': 0, 'value_issued': 0})
    issued_items_distribution = defaultdict(lambda: {'quantity': 0, 'value': 0})

    for quantity in items_in_department:
        item_name = quantity.item.item_name
        item_distribution[item_name]['quantity'] += quantity.quantity
        latest_stock = StockHistory.objects.filter(item=quantity.item).order_by('-date_added').first()
        if latest_stock:
            item_distribution[item_name]['value'] += quantity.quantity * latest_stock.unit_cost

    for stock in stock_history:
        date_key = stock.date_added.strftime("%Y-%m-%d")
        stock_movement[date_key]['added'] += stock.quantity
        stock_movement[date_key]['value_added'] += stock.total_cost

    for issued in issued_history:
        date_key = issued.date.strftime("%Y-%m-%d")
        stock_movement[date_key]['issued'] += issued.quantity_issued_out
        latest_stock = StockHistory.objects.filter(item=issued.item).order_by('-date_added').first()
        if latest_stock:
            stock_movement[date_key]['value_issued'] += issued.quantity_issued_out * latest_stock.unit_cost

    for issued in issued_history:
        item_name = issued.item.item_name
        issued_items_distribution[item_name]['quantity'] += issued.quantity_issued_out
        latest_stock = StockHistory.objects.filter(item=issued.item).order_by('-date_added').first()
        if latest_stock:
            issued_items_distribution[item_name]['value'] += issued.quantity_issued_out * latest_stock.unit_cost

    total_quantity = sum(item['quantity'] for item in item_distribution.values())
    total_value = sum(item['value'] for item in item_distribution.values())
    total_issued_quantity = sum(item['quantity'] for item in issued_items_distribution.values())
    total_issued_value = sum(item['value'] for item in issued_items_distribution.values())

    chart_data = {
        'item_distribution': {
            'labels': list(item_distribution.keys()),
            'quantities': [item['quantity'] for item in item_distribution.values()],
            'values': [float(item['value']) for item in item_distribution.values()]
        },
        'stock_movement': {
            'dates': list(stock_movement.keys()),
            'added': [value['added'] for value in stock_movement.values()],
            'issued': [value['issued'] for value in stock_movement.values()],
            'value_added': [float(value['value_added']) for value in stock_movement.values()],
            'value_issued': [float(value['value_issued']) for value in stock_movement.values()]
        },
        'issued_items_distribution': {
            'labels': list(issued_items_distribution.keys()),
            'quantities': [item['quantity'] for item in issued_items_distribution.values()],
            'values': [float(item['value']) for item in issued_items_distribution.values()]
        }
    }

    context = {
        'department': department,
        'items_in_department': items_in_department,
        'stock_history': stock_history,
        'issued_history': issued_history,
        'item_distribution': chart_data['item_distribution'],
        'stock_dates': chart_data['stock_movement']['dates'],
        'stock_added': chart_data['stock_movement']['added'],
        'stock_issued': chart_data['stock_movement']['issued'],
        'value_added': chart_data['stock_movement']['value_added'],
        'value_issued': chart_data['stock_movement']['value_issued'],
        'issued_items_distribution': chart_data['issued_items_distribution'],
        'total_quantity': total_quantity,
        'total_value': total_value,
        'total_issued_quantity': total_issued_quantity,
        'total_issued_value': total_issued_value,
        'chart_data_json': json.dumps(chart_data, default=decimal_default)
    }
    return context

def get_inflow_report_context():
    """
    Generates a comprehensive context dictionary containing several metrics and summaries
    derived from stock history data. This includes various aggregated totals for quantities
    and values organized by items, categories, suppliers, deliveries, departments, and
    overall totals.

    The returned context is also prepared for chart representation via JSON serialization
    for frontend consumption.

    :raises: Does not explicitly raise errors but assumes proper database connections and
             existence of the necessary data models.

    :return: A dictionary with keys representing various stock inflow metrics and summaries:
        - `total_quantities` (List[Dict]): Total quantities and values calculated for each item.
        - `categories` (List[Dict]): Total quantities and values grouped by item categories.
        - `suppliers` (List[Dict]): Total quantities and values grouped by suppliers.
        - `total_quantities_chart` (str): JSON-encoded representation of `total_quantities` for charts.
        - `categories_chart` (str): JSON-encoded representation of `categories` for charts.
        - `suppliers_chart` (str): JSON-encoded representation of `suppliers` for charts.
        - `stock_history` (QuerySet): All stock history records from the database.
        - `stock_history_table` (QuerySet): All stock history records ordered by `date_added`.
        - `delivery_summary` (QuerySet): Summarized deliveries organized by supplier and delivery number.
        - `labels` (List[str]): List of supplier names acting as labels for chart generation.
        - `quantities` (List): Numeric quantities corresponding to suppliers in `labels`.
        - `values` (List[float]): Numeric total values corresponding to suppliers in `labels`.
        - `departmental_inflow` (QuerySet): Total quantities and values calculated for each department.
        - `overall_totals` (Dict): Aggregated overall total quantities and values.
        - `departmental_inflow_chart` (str): JSON-encoded representation of `departmental_inflow` for charts.
        - `overall_totals_chart` (str): JSON-encoded representation of `overall_totals` for charts.
    """
    # Fetch all stock history records
    stock_history = StockHistory.objects.all()
    stock_history_table = StockHistory.objects.all().order_by('-date_added')

    # Calculate total quantities and values for each item
    total_quantities = stock_history.values('item__item_name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    )

    # Calculate total quantities and values for each category
    categories = stock_history.values('item__category').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    )

    # Calculate total quantities and values for each supplier
    suppliers = stock_history.values('supplied_by').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    )

    # Summarize deliveries by delivery number and supplier
    delivery_summary = StockHistory.objects.values('delivery_number', 'supplied_by').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    ).order_by('-total_quantity')

    # Calculate quantities and values by supplier
    quantities_by_supplier = StockHistory.objects.values('supplied_by').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    )

    # Prepare data for supplier chart
    labels = [entry['supplied_by'] for entry in quantities_by_supplier]
    quantities = [entry['total_quantity'] for entry in quantities_by_supplier]
    values = [float(entry['total_value']) for entry in quantities_by_supplier]

    # Calculate total added quantities and values for each department
    departmental_inflow = StockHistory.objects.values('department__Department_name').annotate(
        total_added=Sum('quantity'),
        total_value=Sum(F('quantity') * F('unit_cost'))
    ).order_by('-total_added')

    # Calculate overall totals for quantities and values
    overall_totals = stock_history.aggregate(
        total_quantity=Coalesce(Sum('quantity'), 0),
        total_value=Coalesce(Sum(F('quantity') * F('unit_cost')), 0, output_field=DecimalField())
    )

    # Prepare context dictionary
    context = {
        'total_quantities': list(total_quantities),
        'categories': list(categories),
        'suppliers': list(suppliers),
        'total_quantities_chart': json.dumps(list(total_quantities), cls=DjangoJSONEncoder),
        'categories_chart': json.dumps(list(categories), cls=DjangoJSONEncoder),
        'suppliers_chart': json.dumps(list(suppliers), cls=DjangoJSONEncoder),
        'stock_history': stock_history,
        'stock_history_table': stock_history_table,
        'delivery_summary': delivery_summary,
        'labels': labels,
        'quantities': quantities,
        'values': values,
        'departmental_inflow': departmental_inflow,
        'overall_totals': overall_totals,
        'departmental_inflow_chart': json.dumps(list(departmental_inflow), cls=DjangoJSONEncoder),
        'overall_totals_chart': json.dumps(overall_totals, cls=DjangoJSONEncoder),
    }
    return context

def get_outflow_report_context():
    """
    Generates a detailed context report related to the outflow of issued items, including
    statistics and aggregated data such as costs, departmental breakdown, and category
    summarization. The function fetches and processes various pieces of information from
    the database, annotating and aggregating fields to prepare a comprehensive dictionary
    for reporting purposes.

    :return: Dictionary containing the following keys and their respective data:
             - total_cost: The total cost of all issued items after aggregation.
             - avg_cost_per_item: The average cost per single item issued out.
             - highest_single_item_cost: The highest unit cost among all issued-out items.
             - department_data: Aggregated data grouped by department including total
               costs, quantities, and the last issued date.
             - category_data: Aggregated data grouped by item category including total
               quantities and costs.
             - top_categories: A list of the top 5 categories of items based on total cost.
             - recent_items: The 5 most recent issued-out items with additional related
               information.
    """
    # Get the latest stock for each item
    latest_stock = StockHistory.objects.filter(
        item=OuterRef('item')
    ).order_by('-date_added')

    # Annotate issued out history with unit cost and total cost
    issued_out_with_cost = IssuedOutHistory.objects.annotate(
        annotated_unit_cost=Subquery(latest_stock.values('unit_cost')[:1]),
        calculated_total_cost=F('quantity_issued_out') * F('annotated_unit_cost')
    )

    # Calculate total cost of issued items
    total_cost = issued_out_with_cost.aggregate(
        total=Coalesce(Sum('calculated_total_cost'), 0, output_field=DecimalField())
    )['total']

    # Calculate average cost per item
    avg_cost_per_item = issued_out_with_cost.aggregate(
        avg=Coalesce(Avg('annotated_unit_cost'), 0, output_field=DecimalField())
    )['avg']

    # Find the highest single item cost
    highest_single_item_cost = issued_out_with_cost.aggregate(
        max=Coalesce(Max('annotated_unit_cost'), 0, output_field=DecimalField())
    )['max']

    # Aggregate data by department
    department_data = issued_out_with_cost.values('department__Department_name').annotate(
        total_outflow=Sum('quantity_issued_out'),
        total_cost=Sum('calculated_total_cost'),
        last_issue_date=Max('date')
    ).order_by('-total_cost')

    # Aggregate data by category
    category_data = issued_out_with_cost.values('item__category').annotate(
        total_outflow=Sum('quantity_issued_out'),
        total_cost=Sum('calculated_total_cost')
    ).order_by('-total_cost')

    # Get top 5 categories by total cost
    top_categories = category_data[:5]

    # Get the 5 most recent issued items
    recent_items = issued_out_with_cost.select_related('item', 'issued_to', 'department').order_by('-date')[:5]

    # Prepare context dictionary
    context = {
        'total_cost': total_cost,
        'avg_cost_per_item': avg_cost_per_item,
        'highest_single_item_cost': highest_single_item_cost,
        'department_data': department_data,
        'category_data': category_data,
        'top_categories': top_categories,
        'recent_items': recent_items,
    }
    return context

def get_department_dashboard_context(department_id):
    """
    Fetches and calculates various metrics and percentages for the inventory of a specific
    department, such as total items, total quantity, out of stock items, expired items,
    depreciated items, and low stock items. These metrics are then packaged into a
    dictionary for further use in creating dashboards or reports.

    :param department_id: The ID of the department for which inventory metrics and
        summaries are to be gathered.
    :return: A dictionary containing calculated inventory data and summarized
        statistics, such as percentages and counts for various inventory status
        metrics like out of stock, expired, depreciated, and low stock items, along
        with their respective percentages, and information about the department's
        inventory items.
    """
    # Fetch the department by ID
    department = get_object_or_404(StaffDepartment, id=department_id)
    current_date = timezone.now().date()

    # Fetch items in the department
    department_items = InventoryItem.objects.filter(quantity__department=department)
    total_items = department_items.distinct().count()
    total_quantity = Quantity.objects.filter(department=department).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate out of stock items and their quantity
    out_of_stock_count = Quantity.objects.filter(department=department, quantity=0).count()
    out_of_stock_items_quantity = Quantity.objects.filter(department=department, quantity=0).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate expired items and their quantity
    expired_items = Quantity.objects.filter(department=department, expiry_date__lt=current_date)
    expired_count = expired_items.count()
    expired_items_quantity = expired_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate depreciated items and their quantity
    depreciated_items = Quantity.objects.filter(department=department, depreciation_date__lt=current_date)
    depreciated_count = depreciated_items.count()
    depreciated_items_quantity = depreciated_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate low stock items and their quantity
    low_stock_items = Quantity.objects.filter(department=department, quantity__gt=0, quantity__lt=50)
    low_stock_count = low_stock_items.count()
    low_stock_items_quantity = low_stock_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate various percentages
    out_of_stock_percentage = (out_of_stock_items_quantity / total_quantity) * 100 if total_quantity > 0 else 0
    expired_percentage = (expired_items_quantity / total_quantity) * 100 if total_quantity > 0 else 0
    depreciated_percentage = (depreciated_items_quantity / total_quantity) * 100 if total_quantity > 0 else 0
    low_stock_percentage = (low_stock_items_quantity / total_quantity) * 100 if total_quantity > 0 else 0

    # Prepare context dictionary
    context = {
        'department_items': department_items,
        'department': department,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'out_of_stock_percentage': out_of_stock_percentage,
        'expired_percentage': expired_percentage,
        'depreciated_percentage': depreciated_percentage,
        'low_stock_percentage': low_stock_percentage,
        'out_of_stock_count': out_of_stock_count,
        'expired_count': expired_count,
        'depreciated_count': depreciated_count,
        'low_stock_count': low_stock_count,
    }
    return context

def get_department_item_details_context(item_id, department_id=None):
    """
    Fetches and prepares all necessary details and context for displaying or processing
    an inventory item's information, which might include department-specific data, stock
    history, issued out history, and employee data. Builds and returns a structured
    dictionary containing this information.

    :param item_id: The identifier of the inventory item for which details are being fetched.
    :param department_id: The identifier of the department, if any, to filter the details.
        Can be None if no department filtering is needed.
    :return: A dictionary with inventory item details, including item data, department data,
        forms, stock and issuance histories, quantities, and employee data.
    """
    # Fetch the item by ID
    item = get_object_or_404(InventoryItem, id=item_id)

    # Fetch the department by ID if provided
    department = None if department_id is None else get_object_or_404(StaffDepartment, id=department_id)

    # Initialize forms
    stock_form = StockHistoryForm(initial={'item': item})
    employee_form = EmployeeForm()

    # Fetch quantities for the item, filtered by department if provided
    quantities = Quantity.objects.filter(item=item)
    if department:
        quantities = quantities.filter(department=department)

    # Fetch all employees
    employees = list(Employee.objects.values('id', 'name', 'department_id'))

    # Fetch stock history and issued out history for the item, filtered by department if provided
    stock_history = StockHistory.objects.filter(item=item)
    issued_out_history = IssuedOutHistory.objects.filter(item=item)
    if department:
        stock_history = stock_history.filter(department=department)
        issued_out_history = issued_out_history.filter(department=department)

    # Order stock history and issued out history by date
    stock_history = stock_history.order_by('date_added')
    issued_out_history = issued_out_history.order_by('date')

    # Prepare context dictionary
    context = {
        'item': item,
        'department': department,
        'stock_form': stock_form,
        'quantities': quantities,
        'employees': employees,
        'employee_form': employee_form,
        'stock_history': stock_history,
        'issued_out_history': issued_out_history,
    }
    return context

def get_outflow_dashboard_context():
    """
    Generates a context dictionary containing various aggregated and annotated data
    related to issued out stock items. The function calculates financial metrics,
    groups issued items by departments and categories, and provides summary items
    for recent transactions. This is useful for constructing a dashboard interface
    for outflow reporting and analysis.

    :return: A dictionary with the aggregated data, including:

        - Total cost of all issued items.
        - Average cost per item across all issued items.
        - Highest single item cost for issued out history.
        - Aggregated data by department with total outflow, total cost, and last issue date.
        - Aggregated data by category with total outflow and total cost.
        - Top 5 categories by total cost.
        - The 5 most recent issued items.
    """
    # Get the latest stock for each item
    latest_stock = StockHistory.objects.filter(
        item=OuterRef('item')
    ).order_by('-date_added')

    # Annotate issued out history with unit cost and total cost
    issued_out_with_cost = IssuedOutHistory.objects.annotate(
        annotated_unit_cost=Subquery(latest_stock.values('unit_cost')[:1]),
        calculated_total_cost=F('quantity_issued_out') * F('annotated_unit_cost')
    )

    # Calculate total cost of issued items
    total_cost = issued_out_with_cost.aggregate(
        total=Coalesce(Sum('calculated_total_cost'), 0, output_field=DecimalField())
    )['total']

    # Calculate average cost per item
    avg_cost_per_item = issued_out_with_cost.aggregate(
        avg=Coalesce(Avg('annotated_unit_cost'), 0, output_field=DecimalField())
    )['avg']

    # Find the highest single item cost
    highest_single_item_cost = issued_out_with_cost.aggregate(
        max=Coalesce(Max('annotated_unit_cost'), 0, output_field=DecimalField())
    )['max']

    # Aggregate data by department
    department_data = issued_out_with_cost.values('department__Department_name').annotate(
        total_outflow=Sum('quantity_issued_out'),
        total_cost=Sum('calculated_total_cost'),
        last_issue_date=Max('date')
    ).order_by('-total_cost')

    # Aggregate data by category
    category_data = issued_out_with_cost.values('item__category').annotate(
        total_outflow=Sum('quantity_issued_out'),
        total_cost=Sum('calculated_total_cost')
    ).order_by('-total_cost')

    # Get top 5 categories by total cost
    top_categories = category_data[:5]

    # Get the 5 most recent issued items
    recent_items = issued_out_with_cost.select_related('item', 'issued_to', 'department').order_by('-date')[:5]

    # Prepare context dictionary
    context = {
        'total_cost': total_cost,
        'avg_cost_per_item': avg_cost_per_item,
        'highest_single_item_cost': highest_single_item_cost,
        'department_data': department_data,
        'category_data': category_data,
        'top_categories': top_categories,
        'recent_items': recent_items,
    }
    return context

def get_cost_report_context():
    """
    Fetches and prepares context data for a cost report, including information about departments,
    categories, items, and the total inventory cost. The data is aggregated from various
    database models, such as StockHistory, IssuedOutHistory, InventoryItem, and their associated
    relationships.

    This function calculates:
    - Total cost and issued out value for each department.
    - Total cost and issued out value for each category.
    - Total cost and issued out value for each item.
    - Total inventory cost across all records.

    Additionally, the function organizes and formats the retrieved data into a dictionary
    suitable for further use or reporting.

    :return: A dictionary containing aggregated and organized context data. The structure includes:
        - 'department_data': A list of dictionaries, each containing:
            - 'department': Department instance.
            - 'total_cost': Total cost for stocks associated with the department.
            - 'issued_out_value': Total issued out value for items associated with the department.
            - 'items': Queryset of InventoryItems associated with the department.
        - 'category_data': A list of dictionaries, each containing:
            - 'category': Category instance.
            - 'total_cost': Total cost for items belonging to the category.
            - 'issued_out_value': Total issued out value for items belonging to the category.
            - 'items': Queryset of InventoryItems belonging to the category.
        - 'item_data': A list of dictionaries, each containing:
            - 'item': Item instance.
            - 'total_cost': Total cost for the specific item.
            - 'issued_out_value': Total issued out value for the specific item.
        - 'total_inventory_cost': The aggregate total cost of all inventory items.
    """
    # Fetch all departments
    departments = StaffDepartment.objects.all()
    department_data = []

    # Calculate total cost and issued out value for each department
    for department in departments:
        total_cost = StockHistory.objects.filter(department=department).aggregate(total_cost=Sum('total_cost'))['total_cost'] or 0
        issued_out_value = IssuedOutHistory.objects.filter(department=department).aggregate(total_issued_value=Sum('quantity_issued_out'))['total_issued_value'] or 0
        items = InventoryItem.objects.filter(quantity__department=department).annotate(total_item_cost=Sum('stockhistory__total_cost'))
        department_data.append({
            'department': department,
            'total_cost': total_cost,
            'issued_out_value': issued_out_value,
            'items': items,
        })

    # Fetch all categories
    categories = ItemCategory.objects.all()
    category_data = []

    # Calculate total cost and issued out value for each category
    for category in categories:
        items = InventoryItem.objects.filter(category=category.Category_name)
        total_cost = StockHistory.objects.filter(item__in=items).aggregate(total_cost=Sum('total_cost'))['total_cost'] or 0
        issued_out_value = IssuedOutHistory.objects.filter(item__in=items).aggregate(total_issued_value=Sum('quantity_issued_out'))['total_issued_value'] or 0
        category_data.append({
            'category': category,
            'total_cost': total_cost,
            'issued_out_value': issued_out_value,
            'items': items,
        })

    # Fetch all items
    items = InventoryItem.objects.all()
    item_data = []

    # Calculate total cost and issued out value for each item
    for item in items:
        total_cost = StockHistory.objects.filter(item=item).aggregate(total_cost=Sum('total_cost'))['total_cost'] or 0
        issued_out_value = IssuedOutHistory.objects.filter(item=item).aggregate(total_issued_value=Sum('quantity_issued_out'))['total_issued_value'] or 0
        item_data.append({
            'item': item,
            'total_cost': total_cost,
            'issued_out_value': issued_out_value,
        })

    # Calculate total inventory cost
    total_inventory_cost = StockHistory.objects.aggregate(total_cost=Sum('total_cost'))['total_cost'] or 0

    # Prepare context dictionary
    context = {
        'department_data': department_data,
        'category_data': category_data,
        'item_data': item_data,
        'total_inventory_cost': total_inventory_cost,
    }
    return context

def get_all_delivered_view_context():
    """
    Fetches and prepares a detailed context containing information about delivered items,
    their related data, and aggregated totals, including remaining quantities, costs, and
    associated metadata for category and department information.

    The function performs the following:
    1. Calculates the total issued quantity for each stock item up to the point of addition.
    2. Annotates delivered stock items with the issued quantity, remaining quantity, and
       total calculated costs.
    3. Aggregates overall totals for delivered stock items regarding quantity, cost, and
       leftover inventory.
    4. Retrieves all item categories and staff departments for contextual reference.
    5. Compiles these results into a comprehensive dictionary format for usage in views.

    :return: A dictionary containing lists of detailed information about delivered items,
        aggregated totals, categories, and departments.
    """
    # Calculate the total issued quantity for each item up to the date added
    issued_quantity = IssuedOutHistory.objects.filter(
        item=OuterRef('item'),
        date__lte=OuterRef('date_added')
    ).values('item').annotate(
        total_issued=Sum('quantity_issued_out')
    ).values('total_issued')

    # Fetch delivered items and annotate with calculated total cost, issued quantity, and remaining quantity
    delivered_items = StockHistory.objects.select_related(
        'item', 'department', 'added_by'
    ).annotate(
        calculated_total_cost=F('quantity') * F('unit_cost'),
        issued_quantity=Coalesce(Subquery(issued_quantity), 0),
        remaining_quantity=F('quantity') - Coalesce(Subquery(issued_quantity), 0)
    ).order_by('-date_added')

    # Aggregate totals for delivered items
    totals = delivered_items.aggregate(
        total_items=Sum('quantity'),
        total_cost=Sum('total_cost'),
        total_remaining=Sum('remaining_quantity')
    )

    # Fetch all categories and departments
    categories = ItemCategory.objects.all()
    departments = StaffDepartment.objects.all()

    # Prepare context dictionary with detailed information about delivered items
    context = {
        'delivered_items': [
            {
                'stock': item,
                'item_name': item.item.item_name,
                'category': item.item.category,
                'department': item.department.Department_name,
                'engraved_number': item.engraved_number,
                'quantity': item.quantity,
                'unit_cost': item.unit_cost,
                'total_cost': item.total_cost,
                'remaining_quantity': item.remaining_quantity,
                'date_added': item.date_added,
                'added_by': item.added_by.username,
                'lpo': item.lpo,
                'supplied_by': item.supplied_by,
                'delivery_number': item.delivery_number,
            }
            for item in delivered_items
        ],
        'totals': totals,
        'categories': categories,
        'departments': departments,
    }
    return context
