# Generated by Django 5.2 on 2025-05-06 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MES',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MODELO', models.CharField(max_length=255)),
                ('NS', models.CharField(max_length=100)),
                ('FECHA_REPARACION', models.DateField()),
                ('HORA_REPARACION', models.TimeField()),
                ('FECHA_RECHAZO', models.DateField()),
                ('HORA_RECHAZO', models.TimeField()),
                ('POSICION', models.CharField(max_length=100)),
                ('FUNCION', models.CharField(max_length=100)),
                ('CODIGO_FALLA', models.CharField(max_length=200)),
                ('CAUSA', models.CharField(max_length=200)),
                ('ACCION', models.CharField(max_length=200)),
                ('ORIGEN', models.CharField(max_length=50)),
                ('IMAGEN', models.TextField(default='0')),
                ('REPARADOR', models.CharField(max_length=100)),
                ('COMENTARIO', models.TextField(blank=True, default='')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('NS', 'FECHA_REPARACION', 'HORA_REPARACION', 'CODIGO_FALLA'), name='uq_mes_reparacion_codigo')],
            },
        ),
        migrations.CreateModel(
            name='MQS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TrackId', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('Time', models.TimeField()),
                ('Line', models.CharField(max_length=255)),
                ('Family', models.CharField(max_length=255)),
                ('Model', models.CharField(max_length=255)),
                ('Process', models.CharField(max_length=255)),
                ('Station', models.CharField(max_length=255)),
                ('Fixture', models.CharField(max_length=255)),
                ('NTF', models.BooleanField()),
                ('Prime', models.BooleanField()),
                ('Testcode', models.CharField(max_length=255)),
                ('Testcode_Desc', models.TextField()),
                ('Fail_Desc', models.TextField()),
                ('TestTime', models.FloatField(blank=True, null=True)),
                ('Test_Val', models.FloatField(blank=True, null=True)),
                ('LL', models.FloatField(blank=True, null=True)),
                ('UL', models.FloatField(blank=True, null=True)),
            ],
            options={
                'db_table': 'quality_mqs',
                'indexes': [models.Index(fields=['date', 'Time'], name='quality_mqs_date_fa8af4_idx'), models.Index(fields=['TrackId'], name='quality_mqs_TrackId_cbd027_idx')],
                'constraints': [models.UniqueConstraint(fields=('TrackId', 'date', 'Time'), name='unique_mqs_trackid_datetime')],
            },
        ),
        migrations.CreateModel(
            name='YieldTurno',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('date', models.DateField()),
                ('Jornada', models.CharField(max_length=50)),
                ('Turno', models.CharField(max_length=50)),
                ('Line', models.CharField(max_length=50)),
                ('Family', models.CharField(max_length=50)),
                ('Process', models.CharField(max_length=100)),
                ('Prime_Pass', models.IntegerField(default=0)),
                ('Prime_Fail', models.IntegerField(default=0)),
                ('Prime_Handle', models.IntegerField(default=0)),
                ('Prime_NTF_Count', models.IntegerField(default=0)),
                ('Prime_Defect_Count', models.IntegerField(default=0)),
                ('FTY', models.FloatField(default=0.0)),
                ('DPHU', models.FloatField(default=0.0)),
                ('NTF', models.FloatField(default=0.0)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('Name', 'date', 'Turno', 'Line'), name='unique_yield_turno')],
            },
        ),
    ]
