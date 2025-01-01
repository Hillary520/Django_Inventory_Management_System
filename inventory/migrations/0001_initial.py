# Generated by Django 5.0.7 on 2024-12-30 17:55

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('Title', models.CharField(default='Attorney', max_length=100)),
                ('office', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(default='Uncategorized', max_length=100)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires', models.BooleanField(default=False)),
                ('depreciates', models.BooleanField(default=False)),
                ('engraved', models.BooleanField(default=False)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ItemCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Category_name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StaffDepartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Department_name', models.CharField(max_length=200)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Quantity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('depreciation_date', models.DateField(blank=True, null=True)),
                ('engraved_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Engraved Number')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryitem')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.staffdepartment')),
            ],
        ),
        migrations.CreateModel(
            name='IssuedOutHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('engraved_number', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.CharField(max_length=255)),
                ('quantity_issued_out', models.PositiveIntegerField()),
                ('issue_voucher_number', models.CharField(max_length=50)),
                ('office', models.CharField(max_length=100, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('issued_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('issued_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.employee')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryitem')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.staffdepartment')),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.staffdepartment'),
        ),
        migrations.CreateModel(
            name='StockHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('depreciation_date', models.DateField(blank=True, null=True)),
                ('unit_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('lpo', models.CharField(max_length=100, verbose_name='LPO')),
                ('supplied_by', models.CharField(max_length=100)),
                ('delivery_number', models.CharField(max_length=100)),
                ('engraved_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Engraved Number')),
                ('issued', models.BooleanField(default=False)),
                ('date_added', models.DateField(blank=True, null=True)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.staffdepartment')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryitem')),
            ],
            options={
                'indexes': [models.Index(fields=['item'], name='inventory_s_item_id_a2a098_idx'), models.Index(fields=['department'], name='inventory_s_departm_568ef1_idx'), models.Index(fields=['date_added'], name='inventory_s_date_ad_d217e4_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='stockhistory',
            constraint=models.CheckConstraint(check=models.Q(('quantity__gte', 0)), name='quantity_gte_0'),
        ),
    ]