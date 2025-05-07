import csv
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from QualitySite.datos.models import YieldTurno  # Corregido: datos → QualitySite.datos

class Command(BaseCommand):
    help = "Importa datos de YieldTurno desde un archivo CSV"

    def handle(self, *args, **kwargs):
        # URL del CSV proporcionado
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSsIhdvsTlmQ2FQTiPJRLLw59vF5-uXwUZIguYAe2OFOTExm3TjtpxV_orvspHoDf7NN73MIq0vErR1/pub?gid=1321118416&single=true&output=csv"
        
        self.stdout.write("📥 Descargando datos de Yield...")
        registros_procesados = 0
        registros_actualizados = 0
        registros_existentes = 0
        
        try:
            # Obtener último registro de la base de datos
            last_record = YieldTurno.objects.order_by('-date', '-Name').first()
            if last_record:
                self.stdout.write(f"Último registro en BD: {last_record.date} - {last_record.Name} - {last_record.Line}")
                ultima_fecha = last_record.date
                ultimo_name = last_record.Name
            else:
                self.stdout.write("No hay registros previos en la base de datos")
                ultima_fecha = None
                ultimo_name = None

            # Descargar el archivo CSV desde la URL
            response = requests.get(csv_url)
            response.raise_for_status()  # Lanza una excepción si la solicitud falla

            # Convertir el contenido del CSV en una lista
            reader = list(csv.DictReader(response.text.splitlines()))
            total_rows = len(reader)
            self.stdout.write(self.style.SUCCESS(f"Procesando {total_rows} registros del CSV"))

            # Variable para controlar si ya encontramos el último registro procesado
            encontrado_ultimo = False if last_record else True
            
            # Contadores para diagnóstico
            registros_revisados = 0
            
            # Si hay registros previos, buscamos el punto de inicio por fecha
            max_busqueda = min(1000, total_rows)  # Limitar búsqueda inicial para evitar procesamiento infinito
            
            for index, row in enumerate(reader):
                registros_revisados += 1
                
                # Limitador de diagnóstico: Si pasamos 1000 registros sin encontrar, asumimos un problema
                if not encontrado_ultimo and index >= max_busqueda:
                    self.stdout.write(self.style.WARNING(f"⚠️ No se encontró el registro de inicio después de revisar {max_busqueda} filas. Comenzando desde aquí."))
                    encontrado_ultimo = True  # Forzar inicio después de búsqueda limitada
                
                # Mostrar progreso cada 1000 registros
                if index % 1000 == 0:
                    self.stdout.write(f"Procesando registro {index+1} de {total_rows}...")
                
                try:
                    # Verificar si alguno de los campos críticos está vacío
                    if not row.get("Date") or not row.get("Name") or not row.get("Line"):
                        self.stdout.write(self.style.WARNING(f"Fila {index+1} ignorada - campos críticos vacíos"))
                        continue

                    # Convertir fecha para comparación
                    try:
                        fecha = datetime.strptime(row["Date"], "%Y-%m-%d").date()
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f"Error de formato de fecha en fila {index+1}: {row['Date']}"))
                        continue
                        
                    name = row["Name"]
                    
                    # Si no hemos encontrado el último registro, buscar si este es
                    if not encontrado_ultimo:
                        # Verificar si este es el registro donde deberíamos comenzar
                        if fecha == ultima_fecha and name == ultimo_name:
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Encontrado último registro procesado en fila {index+1}. Continuando desde el siguiente registro."))
                            registros_existentes += 1
                            continue  # Ya está en la BD, pasar al siguiente
                        
                        # Segunda comprobación: solo por fecha si no se encuentra exactamente el mismo registro
                        elif fecha <= ultima_fecha:
                            # Probablemente es un registro que ya tenemos
                            registros_existentes += 1
                            continue
                        else:
                            # ¡Es un registro nuevo! (fecha posterior a la última en BD)
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Fecha nueva encontrada en fila {index+1}. Iniciando importación."))
                            
                    # DIAGNÓSTICO: imprimir algunos valores para verificar
                    if index < 5 or (registros_procesados < 5 and encontrado_ultimo):
                        self.stdout.write(f"DEBUG: Procesando {row['Date']} - {row['Name']} - {row['Line']}")
                            
                    # Convertir valores vacíos a 0 y validar
                    for key in ['Prime Pass', 'Prime Fail', 'Prime Handle', 'Prime NTF Count', 'Prime Defect Count']:
                        if key not in row or not row[key]:
                            row[key] = 0
                        else:
                            try:
                                row[key] = int(row[key])
                            except ValueError:
                                self.stdout.write(self.style.WARNING(f"Valor no numérico para {key} en fila {index+1}: {row[key]}"))
                                row[key] = 0

                    # Calcular FTY, DPHU y NTF con validación
                    prime_pass = int(row['Prime Pass'])
                    prime_fail = int(row['Prime Fail'])
                    prime_handle = max(1, int(row['Prime Handle']))  # Evitar división por cero
                    prime_ntf = int(row['Prime NTF Count'])

                    fty = (prime_pass * 100) / prime_handle if prime_handle else 0
                    dphu = ((prime_fail * 100) / prime_handle) - ((prime_ntf * 100) / prime_handle) if prime_handle else 0
                    ntf = (prime_ntf * 100) / prime_handle if prime_handle else 0

                    # Crear o actualizar el registro
                    obj, created = YieldTurno.objects.update_or_create(
                        Name=row['Name'],
                        date=fecha,
                        Turno=row['Turno'],
                        Line=row['Line'],
                        defaults={
                            'Jornada': row['Jornada'],
                            'Family': row['Family'],
                            'Process': row['Process'],
                            'Prime_Pass': prime_pass,
                            'Prime_Fail': prime_fail,
                            'Prime_Handle': prime_handle,
                            'Prime_NTF_Count': prime_ntf,
                            'Prime_Defect_Count': int(row['Prime Defect Count']),
                            'FTY': fty,
                            'DPHU': dphu,
                            'NTF': ntf,
                        }
                    )
                    
                    if created:
                        registros_procesados += 1
                        if registros_procesados % 100 == 0 or registros_procesados < 10:  # Mostrar primeros 10 y luego cada 100
                            self.stdout.write(self.style.SUCCESS(f"✅ Nuevos registros añadidos: {registros_procesados}"))
                    else:
                        registros_actualizados += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"❌ Error procesando fila {index+1}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Importación completada"))
            self.stdout.write(f"✅ Total registros nuevos añadidos: {registros_procesados}")
            self.stdout.write(f"✅ Total registros actualizados: {registros_actualizados}")
            self.stdout.write(f"ℹ️ Total registros saltados (ya existentes): {registros_existentes}")
            self.stdout.write(f"🔍 Total registros revisados: {registros_revisados}")
            
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"❌ Error descargando el archivo CSV: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error general: {str(e)}"))