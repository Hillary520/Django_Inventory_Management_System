from datetime import date

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models



class InventoryItem(models.Model):
    """
    Represents an item in the inventory system.

    This model keeps track of inventory items, their details, and associated metadata.
    Used in scenarios where inventory management, tracking, and categorization of items
    are required. Each item is associated with a user who added it to the inventory,
    and it includes additional attributes like expiration, depreciation, and engraving status.

    :ivar item_name: Name of the inventory item.
    :type item_name: CharField
    :ivar description: Detailed description of the inventory item.
    :type description: TextField
    :ivar category: Category associated with the inventory item. Defaults to
       'Uncategorized'.
    :type category: CharField
    :ivar date_added: The datetime when the item was added to the inventory. Defaults
       to the current time.
    :type date_added: DateTimeField
    :ivar added_by: Reference to the user who added the item. Related to the User
       model using a foreign key.
    :type added_by: ForeignKey
    :ivar expires: Indicates whether the item has an expiration date.
    :type expires: BooleanField
    :ivar depreciates: Indicates whether the item undergoes depreciation.
    :type depreciates: BooleanField
    :ivar engraved: Indicates whether the item is engraved.
    :type engraved: BooleanField
    """
    item_name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, default='Uncategorized')
    date_added = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    expires = models.BooleanField(default=False)
    depreciates = models.BooleanField(default=False)
    engraved = models.BooleanField(default=False)

    def __str__(self):
        return self.item_name


class ItemCategory(models.Model):
    """
    Represents an item category model in the database.

    This model is used to categorize items with a specific name, description,
    and additional metadata such as the date it was added and who added it.
    It provides the primary structure for organizing item categories.

    :ivar Category_name: Name of the category.
    :type Category_name: models.CharField
    :ivar description: Detailed description of the category.
    :type description: models.TextField
    :ivar date_added: Timestamp when the category was added.
    :type date_added: models.DateTimeField
    :ivar added_by: User who added the category.
    :type added_by: models.ForeignKey
    """
    Category_name = models.CharField(max_length=200)
    description = models.TextField()
    date_added = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.Category_name

class StaffDepartment(models.Model):
    """
    Represents a department within a staff management system.

    This model is designed to encapsulate the details of a staff department, including its
    name, the date it was added, and the user who added it. It serves as a representation
    of department data for relational operations and administrative tasks.

    :ivar Department_name: The name of the department.
    :type Department_name: models.CharField
    :ivar date_added: The timestamp indicating when the department was added.
    :type date_added: models.DateTimeField
    :ivar added_by: A reference to the user who added the department.
    :type added_by: models.ForeignKey
    """
    Department_name = models.CharField(max_length=200)
    date_added = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.Department_name

class Quantity(models.Model):
    """
    Represents the quantity of an inventory item available in a specific department, along with
    additional metadata such as expiry and depreciation dates and an optional engraved number.

    This model is designed to link inventory items with departments, enabling tracking of
    item quantities, depreciation, and expiration. It is used as a key component in inventory
    management systems to ensure reliable tracking of stock levels and associated details.

    :ivar item: The inventory item associated with this quantity.
    :type item: ForeignKey to InventoryItem
    :ivar department: The department associated with this quantity record.
    :type department: ForeignKey to StaffDepartment
    :ivar quantity: The quantity of the inventory item available in the department.
    :type quantity: PositiveIntegerField
    :ivar expiry_date: The optional expiry date for the inventory item.
    :type expiry_date: DateField, optional
    :ivar depreciation_date: The optional depreciation date for the inventory item.
    :type depreciation_date: DateField, optional
    :ivar engraved_number: An optional engraved identification number for the inventory item.
    :type engraved_number: CharField, optional
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    department = models.ForeignKey(StaffDepartment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    depreciation_date = models.DateField(null=True, blank=True)
    engraved_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Engraved Number")

    def __str__(self):
        return f"{self.quantity}"

class StockHistory(models.Model):
    """
    Represents stock history, providing details about inventory items, departments,
    and related transaction data.

    This class is used to track the history of stock-related transactions for an inventory
    item and its associated department. It stores various details such as quantity,
    cost, supplier information, and transaction-specific metadata. Additionally, it
    provides methods to calculate the total cost and derive the condition of the stock item.

    :ivar item: The inventory item associated with this stock history.
    :type item: InventoryItem
    :ivar department: The department responsible for this stock transaction.
    :type department: StaffDepartment
    :ivar quantity: The quantity of the inventory item involved in the transaction.
    :type quantity: int
    :ivar expiry_date: The date when the stock item expires, if applicable.
    :type expiry_date: date or None
    :ivar depreciation_date: The date when the stock item undergoes depreciation,
        if applicable.
    :type depreciation_date: date or None
    :ivar unit_cost: The cost per unit of the inventory item.
    :type unit_cost: Decimal
    :ivar total_cost: The total cost derived from quantity and unit cost.
    :type total_cost: Decimal
    :ivar lpo: The Local Purchase Order (LPO) reference for the transaction.
    :type lpo: str
    :ivar supplied_by: The name of the supplier providing the inventory item.
    :type supplied_by: str
    :ivar delivery_number: The delivery number reference for the stock transaction.
    :type delivery_number: str
    :ivar engraved_number: The engraved identification number of the inventory item, if provided.
    :type engraved_number: str or None
    :ivar issued: Indicates whether the inventory item has been issued or not.
    :type issued: bool
    :ivar date_added: The date when the stock transaction was recorded.
    :type date_added: date or None
    :ivar added_by: The user who created this stock history record.
    :type added_by: User
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    department = models.ForeignKey(StaffDepartment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    depreciation_date = models.DateField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    lpo = models.CharField(max_length=100, verbose_name="LPO")
    supplied_by = models.CharField(max_length=100)
    delivery_number = models.CharField(max_length=100)
    engraved_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Engraved Number")
    issued = models.BooleanField(default=False)
    date_added = models.DateField(null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['department']),
            models.Index(fields=['date_added']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gte=0), name='quantity_gte_0'),
        ]

    def save(self, *args, **kwargs):
        # Set the date_added to the current date if not provided
        if not self.date_added:
            self.date_added = timezone.now().date()
        # Calculate the total cost based on quantity and unit cost
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item} - {self.department} - {self.quantity} - {self.date_added}"

    @property
    def condition(self):
        # Calculate the age of the stock item in days
        age = (date.today() - self.date_added).days
        # Determine the condition based on the age
        if age < 365:
            return 'Newly Purchased'
        elif age < 1825:
            return 'Functional'
        else:
            return 'Obsolete'

class Employee(models.Model):
    """
    Represents an employee within an organization.

    This class is used to define the attributes and relationship between an
    employee and their department. Each employee has a name, title, office location,
    and is linked to a specific department. The information about the employee can
    be utilized for tracking organizational structure and other administrative
    purposes.

    :ivar name: The name of the employee.
    :type name: models.CharField
    :ivar department: A foreign key reference to the employee's department.
    :type department: models.ForeignKey
    :ivar Title: The job title of the employee. Defaults to "Attorney".
    :type Title: models.CharField
    :ivar office: The office location associated with the employee.
    :type office: models.CharField
    """
    name = models.CharField(max_length=100)
    department = models.ForeignKey(StaffDepartment, on_delete=models.CASCADE)
    Title = models.CharField(max_length=100, default='Attorney')
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class IssuedOutHistory(models.Model):
    """
    Representation of the history of issued-out inventory items, recording key details about the issuance.

    Tracks inventory items that have been issued out, including the item details, the recipient, and issuance
    information. The class provides several properties that infer additional information about the issued items
    from related models.

    :ivar item: Reference to the inventory item that has been issued out.
    :type item: ForeignKey
    :ivar engraved_number: Optional engraved number associated with the issued item.
    :type engraved_number: str
    :ivar description: Description of the issued item.
    :type description: str
    :ivar quantity_issued_out: Quantity of the item that has been issued.
    :type quantity_issued_out: int
    :ivar issue_voucher_number: Voucher number associated with the issuance.
    :type issue_voucher_number: str
    :ivar issued_to: Reference to the employee to whom the items were issued.
    :type issued_to: ForeignKey
    :ivar department: Reference to the staff department associated with the issuance.
    :type department: ForeignKey
    :ivar office: Optional office location tied to the issuance.
    :type office: str
    :ivar date: Timestamp indicating when the items were issued.
    :type date: datetime
    :ivar issued_by: Reference to the user who issued the items. Can be null if the user is not recorded.
    :type issued_by: ForeignKey
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    engraved_number = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity_issued_out = models.PositiveIntegerField()
    issue_voucher_number = models.CharField(max_length=50)
    issued_to = models.ForeignKey(Employee, on_delete=models.CASCADE)
    department = models.ForeignKey(StaffDepartment, on_delete=models.CASCADE)
    office = models.CharField(max_length=100, null=True)
    date = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.item.item_name} - {self.quantity_issued_out} issued to {self.issued_to.name}"

    @property
    def condition(self):
        try:
            # Get the latest stock history for the item to determine its condition
            stock_history = StockHistory.objects.filter(item=self.item).latest('date_added')
            return stock_history.condition
        except StockHistory.DoesNotExist:
            return 'No Stock History'

    @property
    def unit_cost(self):
        try:
            # Get the latest stock history for the item to determine its unit cost
            stock_history = StockHistory.objects.filter(item=self.item).latest('date_added')
            return stock_history.unit_cost
        except StockHistory.DoesNotExist:
            return 0

    @property
    def date_purchased(self):
        try:
            # Get the latest stock history for the item to determine its purchase date
            stock_history = StockHistory.objects.filter(item=self.item).latest('date_added')
            return stock_history.date_added
        except StockHistory.DoesNotExist:
            return None

    @property
    def user_title(self):
        try:
            # Get the title of the employee to whom the item was issued
            employee = Employee.objects.get(name=self.issued_to)
            return employee.Title
        except Employee.DoesNotExist:
            return None
        except Employee.MultipleObjectsReturned:
            # Handle the case where multiple employees are found
            return "Multiple employees found"


