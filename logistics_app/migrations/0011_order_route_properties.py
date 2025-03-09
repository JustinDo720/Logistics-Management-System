# Generated by Django 4.2.19 on 2025-03-09 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics_app', '0010_inventory_notified_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='route_coords',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='route_eta',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='route_miles',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
