# Generated by Django 4.2.19 on 2025-03-11 01:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('logistics_app', '0012_route_and_routehistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderstatushistory',
            options={'verbose_name': 'Order Status History', 'verbose_name_plural': 'Order Status Histories'},
        ),
        migrations.AddField(
            model_name='orderstatushistory',
            name='last_updated',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='route',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
