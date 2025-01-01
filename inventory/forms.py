# inventory/forms.py
from django import forms
from .models import InventoryItem, ItemCategory, StaffDepartment, Employee, StockHistory


class InventoryItemForm(forms.ModelForm):
    """
    This class represents a form for creating or updating inventory items.

    The `InventoryItemForm` class provides a Django ModelForm for handling the creation
    and editing of inventory item records. It is associated with the `InventoryItem` model
    and provides widgets for all specified fields, including a category selection dropdown.

    The form includes functionality for selecting an associated category from available item
    categories and for managing item-specific details such as expiration, depreciation, and engraving.

    :ivar category: A field allowing the user to select an item category from a list of available
        categories. If no selection is made, the field defaults to "Select Category".
    """
    # Define a field for category selection
    category = forms.ModelChoiceField(queryset=ItemCategory.objects.all(), empty_label="Select Category")

    class Meta:
        model = InventoryItem
        fields = ['item_name', 'description', 'category', 'expires', 'depreciates', 'engraved']  # Add 'expires' and 'depreciates' fields here



class ItemCategoryForm(forms.ModelForm):
    """
    Represents a form for handling ItemCategory model data.

    This class is used to validate and process data related to the `ItemCategory`
    model. It provides functionality to facilitate creation and updating of
    `ItemCategory` objects. Through its `Meta` inner class, it specifies the
    fields to be included in the form.

    :ivar model: Specifies the model (`ItemCategory`) bound to the form.
    :ivar fields: List of fields in the model to include in the form.
    """
    class Meta:
        model = ItemCategory
        fields = ['Category_name', 'description']

class StaffDepartmentForm(forms.ModelForm):
    """
    Handles the creation and validation of a form for the StaffDepartment model.

    This class represents a model form for creating or updating instances of the
    `StaffDepartment` model. It restricts the form to include only specific fields
    and ensures validation is handled automatically.

    :ivar Meta.model: Specifies the model associated with the form.
    :ivar Meta.fields: Defines the model fields to include in the form.
    """
    class Meta:
        model = StaffDepartment
        fields = ['Department_name']


class StockHistoryForm(forms.ModelForm):
    """
    This form represents the structure and validations for handling the stock history
    data linked to inventory management effectively.

    The form dynamically adjusts based on the item's properties such as whether it
    has an expiry date, depreciation date, or engraved number. This allows for flexibility
    in handling different types of inventory items with varying characteristics.

    :ivar expiry_date: Represents the expiry date of the stock item. Only included
        if the related inventory item has `expires` set to True.
    :ivar depreciation_date: Represents the depreciation date of the stock item. Only
        included if the related inventory item has `depreciates` set to True.
    :ivar date_added: Represents the date the stock item was added.
    """
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    depreciation_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    date_added = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = StockHistory
        fields = ['quantity', 'unit_cost', 'expiry_date', 'depreciation_date', 'lpo', 'supplied_by', 'delivery_number',
                  'department', 'date_added', 'engraved_number']

    def __init__(self, *args, **kwargs):
        item_id = kwargs.pop('item_id', None)
        super(StockHistoryForm, self).__init__(*args, **kwargs)

        if item_id:
            item = InventoryItem.objects.get(id=item_id)
            if not item.expires:
                self.fields.pop('expiry_date')
            if not item.depreciates:
                self.fields.pop('depreciation_date')
            if not item.engraved:
                self.fields.pop('engraved_number')

class EmployeeForm(forms.ModelForm):
    """
    EmployeeForm is a Django ModelForm used to manage the representation
    and validation of the Employee model in web forms.

    This class facilitates the creation and update of Employee model
    instances through a web interface. It includes pre-defined fields
    and assigns specific widgets to control the appearance of the fields
    on the rendered HTML form.

    :ivar Meta.model: The model associated with this form, which is
                      Employee.
    :ivar Meta.fields: The list of fields from the Employee model to
                       include in the form.
    :ivar Meta.widgets: A dictionary explicitly defining the widgets
                        for certain fields to enhance their HTML
                        presentation.
    """
    class Meta:
        model = Employee
        fields = ['name', 'department', 'office', 'Title']

        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'office': forms.TextInput(attrs={'class': 'form-control'}),
            'Title': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DateRangeForm(forms.Form):
    """
    Represents a form for selecting a date range.

    This class is used to create a form for selecting a date range with start and
    end dates using `forms.DateField` fields. It utilizes `forms.SelectDateWidget`
    for both fields to enable a user-friendly date selection interface. The form
    can be used in scenarios where users are required to input a date range for
    filtering or searching data.

    :ivar start_date: The start date of the date range.
    :ivar end_date: The end date of the date range.
    """
    start_date = forms.DateField(widget=forms.SelectDateWidget)
    end_date = forms.DateField(widget=forms.SelectDateWidget)

class EmployeeListForm(forms.ModelForm):
    """
    Represents a form for managing the employee list information, specifically
    tied to the `Employee` model. This form allows for input, validation, and
    handling of employee data, focusing on capturing the attributes such as
    name, department, title, and office. The department field provides a
    dropdown to choose from existing staff departments.

    :ivar department: A dropdown field to select a department from the existing
        `StaffDepartment` queryset. This field is required and labeled as
        "Department".
    """
    department = forms.ModelChoiceField(queryset=StaffDepartment.objects.all(), label="Department")

    class Meta:
        model = Employee
        fields = ['name', 'department', 'Title', 'office']

