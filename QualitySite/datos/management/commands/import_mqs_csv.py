import csv
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from QualitySite.datos.models import MQS  # Corregido: datos → QualitySite.datos

class Command(BaseCommand):
    help = "Importa datos del MQS desde un archivo CSV, con opciones mejoradas de detección de registros nuevos"

    def handle(self, *args, **kwargs):
        # URL del archivo CSV
        csv_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTbxUgc5VVgjlMwC6raz_fVWgVr2YvITNwWQEvtETd7n37-Vbu1SjqhrIrEfN-AoFT9B-xrJeiRwc2q/pub?gid=572560726&single=true&output=csv'

        self.stdout.write(self.style.SUCCESS(f"📥 Descargando datos desde: {csv_url}"))

        try:
            # Descargar el archivo CSV
            response = requests.get(csv_url)
            response.raise_for_status()
            csv_data = response.text.splitlines()

            # Leer el archivo CSV
            reader = list(csv.DictReader(csv_data))
            total_rows = len(reader)
            
            # Validar encabezados
            expected_headers = [
                'Name', 'ProcessQty', 'Date', 'Time', 'Line', 'Family', 'Model', 'Process',
                'Station', 'Fixture', 'TrackId', 'NTF?', 'Prime?', 'Testcode', 'Testcode Desc',
                'Fail Desc', 'TestTime', 'Test Val', 'LL', 'UL'
            ]
            if reader[0].keys() != expected_headers:
                self.stdout.write(self.style.WARNING(f"⚠️ Advertencia: Los encabezados no coinciden exactamente."))
                self.stdout.write(f"Esperados: {expected_headers}")
                self.stdout.write(f"Encontrados: {list(reader[0].keys())}")

            # Obtener el último registro de la base de datos
            last_record = MQS.objects.order_by('-date', '-Time').first()  # Mejor criterio: fecha y hora, no ID
            
            # Variables para seguimiento
            encontrado_ultimo = False
            registros_procesados = 0
            registros_existentes = 0
            registros_con_error = 0
            
            # Inicializar datos del último registro
            if last_record:
                self.stdout.write(f"Último registro en BD: {last_record.date} {last_record.Time} - {last_record.TrackId}")
                ultima_fecha = last_record.date
                ultima_hora = last_record.Time
                last_track_id = last_record.TrackId
                # Fecha límite alternativa: importar últimos 7 días
                fecha_limite = datetime.now().date() - timedelta(days=7)
            else:
                self.stdout.write("No hay registros previos en la base de datos")
                ultima_fecha = None
                ultima_hora = None
                last_track_id = None
                fecha_limite = None
                encontrado_ultimo = True  # Si no hay registros previos, importar todo
            
            # Contador para diagnóstico
            max_busqueda = min(1000, total_rows)  # Límite para evitar búsqueda infinita
            
            # Procesar las filas del CSV
            for index, row in enumerate(reader):
                # Mostrar progreso
                if index % 1000 == 0:
                    self.stdout.write(f"Procesando registro {index+1} de {total_rows}...")
                
                # Si llevamos demasiados registros revisados sin encontrar coincidencia
                if not encontrado_ultimo and index >= max_busqueda:
                    self.stdout.write(self.style.WARNING(f"⚠️ No se encontró el último registro después de {max_busqueda} filas. Comenzando desde aquí."))
                    encontrado_ultimo = True
                
                try:
                    # Convertir fecha para comparación
                    if row.get('Date'):
                        try:
                            fecha = datetime.strptime(row['Date'], '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f"Error en formato de fecha en fila {index+1}: {row['Date']}"))
                            registros_con_error += 1
                            continue
                    else:
                        self.stdout.write(self.style.WARNING(f"Falta fecha en fila {index+1}"))
                        registros_con_error += 1
                        continue
                    
                    # Convertir hora
                    if row.get('Time'):
                        try:
                            hora = datetime.strptime(row['Time'], '%H:%M:%S').time()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f"Error en formato de hora en fila {index+1}: {row['Time']}"))
                            registros_con_error += 1
                            continue
                    else:
                        self.stdout.write(self.style.WARNING(f"Falta hora en fila {index+1}"))
                        registros_con_error += 1
                        continue
                        
                    # Si estamos buscando el punto de inicio
                    if not encontrado_ultimo:
                        # Opción 1: Verificar por TrackId exacto
                        if row.get('TrackId') == last_track_id:
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Encontrado último registro por TrackId en fila {index+1}"))
                            registros_existentes += 1
                            continue
                            
                        # Opción 2: Verificar por fecha y hora exactas
                        if fecha == ultima_fecha and hora == ultima_hora:
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Encontrado último registro por fecha/hora en fila {index+1}"))
                            registros_existentes += 1
                            continue
                            
                        # Opción 3: Verificar por fecha límite (registros de últimos 7 días)
                        if fecha_limite and fecha >= fecha_limite:
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Iniciando importación desde fecha reciente: {fecha} (fila {index+1})"))
                        else:
                            # Si no cumple ninguna condición, seguir buscando
                            registros_existentes += 1
                            continue
                    
                    # Preparar los valores para crear el registro
                    track_id = row.get('TrackId') or '0'
                    station = row.get('Station') or '0'
                    ntf_val = True if row.get('NTF?') == 'Y' else False
                    
                    try:
                        test_val = float(row.get('Test Val', 0)) if row.get('Test Val') else 0.0
                    except ValueError:
                        test_val = 0.0
                    
                    # DEBUG: Mostrar primeros registros procesados
                    if registros_procesados < 3:
                        self.stdout.write(f"DEBUG: Procesando {fecha} {hora} - {track_id}")
                    
                    # Crear o actualizar registro
                    obj, created = MQS.objects.get_or_create(
                        TrackId=track_id,
                        date=fecha,
                        Time=hora,
                        Station=station,
                        defaults={
                            'NTF': ntf_val,
                            'Test_Val': test_val,
                            'Line': row.get('Line') or '0',
                            'Family': row.get('Family') or '0',
                            'Model': row.get('Model') or '0',
                            'Process': row.get('Process') or '0',
                            'Fixture': row.get('Fixture') or '0',
                            'Testcode': row.get('Testcode') or '0',
                            'Testcode_Desc': row.get('Testcode Desc') or '0',
                            'Fail_Desc': row.get('Fail Desc') or '',
                            'TestTime': float(row.get('TestTime', 0)) if row.get('TestTime') else 0.0,
                            'LL': float(row.get('LL', 0)) if row.get('LL') else 0.0,
                            'UL': float(row.get('UL', 0)) if row.get('UL') else 0.0,
                            'Prime': True if row.get('Prime?') == 'Y' else False
                        }
                    )
                    
                    if created:
                        registros_procesados += 1
                        if registros_procesados % 20 == 0 or registros_procesados < 5:
                            self.stdout.write(self.style.SUCCESS(f"✅ Nuevo registro: {track_id} {fecha} {hora}"))
                    else:
                        registros_existentes += 1
                        
                except Exception as e:
                    registros_con_error += 1
                    self.stderr.write(self.style.ERROR(f"❌ Error procesando fila {index+1}: {str(e)}"))

            # Resumen final
            self.stdout.write(self.style.SUCCESS('✅ Proceso completado'))
            self.stdout.write(f"✅ Total registros nuevos añadidos: {registros_procesados}")
            self.stdout.write(f"ℹ️ Total registros ya existentes: {registros_existentes}")
            self.stdout.write(f"❌ Total registros con error: {registros_con_error}")

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"❌ Error al descargar el archivo CSV: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error inesperado: {str(e)}"))
