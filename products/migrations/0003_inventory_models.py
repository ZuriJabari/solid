from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('products', '0002_productreview_updates'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductInventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_stock', models.PositiveIntegerField(default=0)),
                ('reorder_point', models.PositiveIntegerField(help_text='Stock level that triggers reorder alert')),
                ('reorder_quantity', models.PositiveIntegerField(help_text='Suggested quantity to reorder')),
                ('last_restock_date', models.DateTimeField(blank=True, null=True)),
                ('last_restock_quantity', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='products.product')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_number', models.CharField(max_length=50, unique=True)),
                ('quantity', models.PositiveIntegerField()),
                ('cost_per_unit', models.DecimalField(decimal_places=2, help_text='Cost price per unit for this batch', max_digits=10)),
                ('manufacturing_date', models.DateField()),
                ('expiry_date', models.DateField()),
                ('supplier', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='products.productinventory')),
            ],
            options={
                'ordering': ['expiry_date'],
            },
        ),
        migrations.CreateModel(
            name='StockAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('adjustment_type', models.CharField(choices=[('restock', 'Restock'), ('sale', 'Sale'), ('return', 'Return'), ('damage', 'Damage/Loss'), ('correction', 'Inventory Correction'), ('expired', 'Expired')], max_length=20)),
                ('quantity', models.IntegerField(help_text='Use positive for additions, negative for reductions')),
                ('reason', models.TextField()),
                ('reference_number', models.CharField(blank=True, help_text='Order number, return reference, etc.', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('adjusted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adjustments', to='products.inventorybatch')),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='products.productinventory')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['inventory', 'adjustment_type', 'created_at'], name='products_st_invento_823cf2_idx')],
            },
        ),
    ] 