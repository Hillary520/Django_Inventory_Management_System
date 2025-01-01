from django.contrib import admin
from .models import InventoryItem, ItemCategory, StaffDepartment, Employee, Quantity, StockHistory, IssuedOutHistory
# Register your models here.
admin.site.register(InventoryItem)
admin.site.register(ItemCategory)
admin.site.register(StaffDepartment)
admin.site.register(Employee)
admin.site.register(Quantity)
admin.site.register(StockHistory)
admin.site.register(IssuedOutHistory)