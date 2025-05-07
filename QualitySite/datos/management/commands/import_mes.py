import csv
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from QualitySite.datos.models import MES  # Corregido: datos → QualitySite.datos

class Command(BaseCommand):
    help = "Importa registros MES desde CSV de Google Sheets"

    def handle(self, *args, **kwargs):
        csv_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQoBW5pYMPZPF4_77hDMBaIMJpfdO--8mreybh3xo1NXEnmYgMUl9jf85U2jW_XKk0rLUorFddMg7_M/pub?gid=572560726&single=true&output=csv'

        self.stdout.write("📥 Descargando datos MES...")
        registros_pendientes = 0
        registros_procesados = 0
        registros_existentes = 0
        
        try:
            # Obtener último registro de la base de datos
            last_record = MES.objects.order_by('-FECHA_REPARACION', '-HORA_REPARACION').first()
            if last_record:
                self.stdout.write(f"Último registro en BD: {last_record.FECHA_REPARACION} {last_record.HORA_REPARACION} - {last_record.NS}")
                ultima_fecha = last_record.FECHA_REPARACION
                ultima_hora = last_record.HORA_REPARACION
                ultimo_ns = last_record.NS
            else:
                self.stdout.write("No hay registros previos en la base de datos")
                ultima_fecha = None
                ultima_hora = None
                ultimo_ns = None

            response = requests.get(csv_url)
            response.raise_for_status()

            # Convertir el contenido del CSV en una lista
            reader = list(csv.DictReader(response.text.splitlines()))
            total_rows = len(reader)
            self.stdout.write(self.style.SUCCESS(f"Procesando {total_rows} registros del CSV"))

            # Variable para controlar si ya encontramos el último registro procesado
            encontrado_ultimo = False if last_record else True
            
            # Contador para limitar la búsqueda
            max_busqueda = min(1000, total_rows)
            registros_revisados = 0
            
            # SOLUCIÓN ALTERNATIVA: Importar los últimos 7 días
            if last_record and not encontrado_ultimo:
                # Usar una fecha límite en vez de buscar registro específico
                fecha_limite = datetime.now().date() - timedelta(days=7)
                self.stdout.write(self.style.WARNING(f"Configurado para importar registros desde: {fecha_limite}"))
            
            for index, row in enumerate(reader):
                registros_revisados += 1
                
                # Limitador de diagnóstico: Si pasamos max_busqueda registros sin encontrar, asumimos problema
                if not encontrado_ultimo and index >= max_busqueda:
                    self.stdout.write(self.style.WARNING(f"⚠️ No se encontró el registro de inicio después de revisar {max_busqueda} filas. Comenzando desde aquí."))
                    encontrado_ultimo = True  # Forzar inicio después de búsqueda limitada
                
                # Mostrar progreso cada 1000 registros
                if index % 1000 == 0:
                    self.stdout.write(f"Procesando registro {index+1} de {total_rows}...")
                
                try:
                    # Verificar si alguno de los campos críticos está vacío
                    if not row.get("MODELO") or not row.get("NS") or not row.get("FECHA REPARACION") or not row.get("HORA REPARACION"):
                        self.stdout.write(self.style.WARNING(f"Fila ignorada - campos críticos vacíos en fila {index+1}"))
                        continue  # Saltar esta fila y continuar con la siguiente
                    
                    # Convertir fechas y horas para comparación
                    try:
                        fecha_rep = datetime.strptime(row["FECHA REPARACION"], "%Y-%m-%d").date()
                        hora_rep = datetime.strptime(row["HORA REPARACION"], "%H:%M").time()
                    except ValueError as e:
                        self.stdout.write(self.style.WARNING(f"Error en formato de fecha/hora en fila {index+1}: {e}"))
                        continue
                    
                    # SOLUCIÓN ALTERNATIVA: Verificar por fecha límite
                    if last_record and not encontrado_ultimo:
                        if fecha_rep >= fecha_limite:
                            self.stdout.write(self.style.SUCCESS(f"Encontrada fecha reciente ({fecha_rep}) en fila {index+1}. Comenzando importación."))
                            encontrado_ultimo = True
                        else:
                            # Fecha demasiado antigua, seguir buscando
                            registros_existentes += 1
                            continue
                    
                    # Si no hemos encontrado el último registro, buscar si este es
                    if not encontrado_ultimo:
                        # Verificar si este es el registro donde deberíamos comenzar (coincide con el último en BD)
                        if (fecha_rep == ultima_fecha and 
                            hora_rep == ultima_hora and 
                            row["NS"] == ultimo_ns):
                            
                            encontrado_ultimo = True
                            self.stdout.write(self.style.SUCCESS(f"Encontrado último registro procesado en fila {index+1}. Continuando desde el siguiente registro."))
                            continue  # Ya está en la BD, pasar al siguiente
                        else:
                            # No es el último registro, seguir buscando
                            registros_existentes += 1
                            continue
                    
                    # DEBUG: Mostrar los primeros registros importados
                    if registros_procesados < 5:
                        self.stdout.write(f"DEBUG: Procesando fila {index+1}: {fecha_rep} {hora_rep} - {row['NS']}")
                    
                    # Verificar si alguno de los campos tiene valor "PENDIENTE"
                    if (row.get("FUNCION", "").strip().upper() == "PENDIENTE" or 
                        row.get("POSICION", "").strip().upper() == "PENDIENTE" or 
                        row.get("ACCION CORRECTIVA", "").strip().upper() == "PENDIENTE" or 
                        row.get("ORIGEN", "").strip().upper() == "PENDIENTE"):
                        
                        registros_pendientes += 1
                        self.stdout.write(self.style.WARNING(f"Registro pendiente no importado: {row['NS']}"))
                        continue  # Saltar este registro y continuar con el siguiente
                    
                    # Convertir fecha de rechazo
                    try:
                        fecha_rec = datetime.strptime(row["FECHA RECHAZO"], "%d/%m/%Y").date()
                        hora_rec = datetime.strptime(row["HORA RECHAZO"], "%H:%M").time()
                    except ValueError as e:
                        self.stdout.write(self.style.WARNING(f"Error en formato de fecha/hora de rechazo en fila {index+1}: {e}"))
                        # Usar valores por defecto en caso de error
                        fecha_rec = fecha_rep
                        hora_rec = hora_rep
                    
                except Exception as e:
                    self.stderr.write(f"Error al procesar la fila {index+1}: {e}")
                    continue

                # Crear registro en la base de datos
                try:
                    obj, created = MES.objects.get_or_create(
                        FECHA_REPARACION=fecha_rep,
                        HORA_REPARACION=hora_rep,
                        NS=row["NS"],
                        CODIGO_FALLA=row.get("CODIGO DE FALLA REPARACION", ""),
                        defaults={
                            "MODELO": row.get("MODELO", ""),
                            "FECHA_RECHAZO": fecha_rec,
                            "HORA_RECHAZO": hora_rec,
                            "POSICION": row.get("POSICION", "").strip(),
                            "FUNCION": row.get("FUNCION", ""),
                            "CAUSA": row.get("CAUSA DE REPARACION", ""),
                            "ACCION": row.get("ACCION CORRECTIVA", ""),
                            "ORIGEN": row.get("ORIGEN", ""),
                            "IMAGEN": row.get("IMAGEN", "0") if row.get("IMAGEN") else "0",
                            "REPARADOR": row.get("REPARADOR", ""),
                            "COMENTARIO": row.get("COMENTARIO", "") if row.get("COMENTARIO") else ""
                        }
                    )
                    if created:
                        registros_procesados += 1
                        if registros_procesados % 20 == 0 or registros_procesados < 5:  # Mostrar primeros 5 y luego cada 20
                            self.stdout.write(self.style.SUCCESS(f"Nuevos registros añadidos: {registros_procesados}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error al guardar registro de fila {index+1}: {e}"))
                    continue

            self.stdout.write(self.style.SUCCESS(f"✅ Importación completada"))
            self.stdout.write(f"✅ Total registros nuevos añadidos: {registros_procesados}")
            self.stdout.write(f"ℹ️ Total registros ya existentes: {registros_existentes}")
            self.stdout.write(f"⏳ Total registros pendientes (no importados): {registros_pendientes}")
            self.stdout.write(f"🔍 Total registros revisados: {registros_revisados}")

        except requests.exceptions.RequestException as e:
            self.stderr.write(f"❌ Error al descargar el archivo CSV: {e}")
        except Exception as e:
            self.stderr.write(f"❌ Error general: {e}")