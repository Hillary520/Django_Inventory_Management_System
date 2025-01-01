from django.urls import path
from inventory.views import dashboard, inventory, add_category, add_department, item_details, add_employee, issue_out, \
    combined_report, department_report, inflow_report, outflow_report, department_dashboard, department_item_details, \
    cost_report, outflow_dashboard, ivn_list_view, ivn_detail_view, all_delivered_view, delivery_numbers_list, \
    get_delivery_details, lpo_numbers_list, get_lpo_details, add_engraved_stock, engraved_issue_out, AllIssuedOutView, \
    AssetView, employee_list, employee_create, employee_update, employee_delete

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('inventory/', inventory, name='inventory'),
    path('add/', inventory, name='add_item'),
    path('add-category/', add_category, name='add_category'),
    path('add-department/', add_department, name='add_department'),
    path('item-details/<int:item_id>', item_details, name='item_details'),
    path('item/<int:item_id>/add_stock/', item_details, name='add_stock'),
    path('add_stock/<int:item_id>/', add_engraved_stock, name='add_engraved_stock'),
    path('add-employee', add_employee, name='add_employee'),
    path('issue_out/', issue_out, name='issue_out'),
    path('issue_out_engraved/', engraved_issue_out, name='issue_out_engraved'),
    path('report/combined/', combined_report, name='combined_report'),
    path('report/department/<int:department_id>/', department_report, name='department_report'),
    path('report/in-flow/', inflow_report, name='in_flow_report'),
    path('report/outflow-report/', outflow_report, name='outflow_report'),
    path('report/cost-report/', cost_report, name='cost-report'),
    path('department/<int:department_id>/', department_dashboard, name='department_dashboard'),
    path('department/<int:department_id>/item/<int:item_id>/', department_item_details, name='department_item_details'),
    path('inventory/issued-out', outflow_dashboard, name='outflow_dashboard'),
    path('ivn-list/', ivn_list_view, name='ivn_list'),
    path('ivn-detail/', ivn_detail_view, name='ivn_detail'),
    path('all-delivered/', all_delivered_view, name='all_delivered'),
    path('delivery_numbers/', delivery_numbers_list, name='delivery_numbers_list'),
    path('get_delivery_details/<str:delivery_number>/', get_delivery_details, name='get_delivery_details'),
    path('lpo_numbers/', lpo_numbers_list, name='lpo_numbers_list'),
    path('get_lpo_details/<str:lpo_number>/', get_lpo_details, name='get_lpo_details'),
    path('all-issued-out/', AllIssuedOutView.as_view(), name='all_issued_out'),
    path('asset-register/', AssetView.as_view(), name='asset_register'),
    path('employees/', employee_list, name='employee_list'),
    path('employees/create/', employee_create, name='employee_create'),
    path('employees/<int:pk>/update/', employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', employee_delete, name='employee_delete'),
]