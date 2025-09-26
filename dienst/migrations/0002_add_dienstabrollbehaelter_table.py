from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),         # ggf. an deine letzte core-Migration anpassen
        ('dienst', '0001_initial'),       # baut auf der bereits angewendeten 0001 auf
    ]

    operations = [
        migrations.CreateModel(
            name='DienstAbrollbehaelter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('erforderlich', models.BooleanField(default=False)),
                ('abrollbehaelter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.abrollbehaelter')),
                ('dienst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dienst.dienst')),
            ],
            options={
                'unique_together': {('dienst', 'abrollbehaelter')},
            },
        ),
    ]
