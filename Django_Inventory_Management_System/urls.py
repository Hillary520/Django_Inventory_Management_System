"""

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from inventory.views import dashboard, inventory, add_category, add_department, item_details, add_employee, issue_out, \
    combined_report, department_report, inflow_report, outflow_report, department_dashboard, department_item_details, \
    cost_report, outflow_dashboard, ivn_list_view, ivn_detail_view, all_delivered_view, delivery_numbers_list, \
    get_delivery_details, lpo_numbers_list, get_lpo_details, add_engraved_stock, engraved_issue_out, AllIssuedOutView, \
    AssetView, employee_list, employee_create, employee_update, employee_delete

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('inventory.urls'))
]
