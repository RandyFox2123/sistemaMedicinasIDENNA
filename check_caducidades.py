#!/usr/bin/env python
import os
import django
import time
from datetime import datetime, time as hora_tiempo
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_medicinas.settings')
django.setup()

from app_medicinas.models import Medicina

HORA_EJECUCION = hora_tiempo(10, 20)

def verificar_caducidades():
    """Verifica TODOS caducado=False o NULL"""
    hoy = timezone.now().date()
    
    # ✅ CORREGIDO: Busca False O NULL
    candidatos = Medicina.objects.filter(
        models.Q(caducado__isnull=True) | models.Q(caducado=False),  # ← FIX
        fecha_caducidad__isnull=False,
        fecha_caducidad__lte=hoy
    )
    
    print(f"🔍 [{datetime.now()}] Buscando caducados <= {hoy}")
    print(f"📊 Candidatos encontrados: {candidatos.count()}")
    
    if candidatos.exists():
        # MOSTRAR cuáles se van a actualizar
        for med in candidatos[:3]:  # Primeros 3
            print(f"   → {med.medicina} (caducado={med.caducado}, fecha={med.fecha_caducidad})")
        
        actualizados = candidatos.update(caducado=True)
        print(f"✅ [{datetime.now()}] ACTUALIZADOS: {actualizados} medicamentos")
    else:
        print(f"✅ [{datetime.now()}] No hay caducados pendientes")

def main():
    print("🚀 MONITOR CADUCIDADES INICIADO (FIX)")
    print(f"⏰ Se ejecutará diariamente a las {HORA_EJECUCION.hour:02d}:{HORA_EJECUCION.minute:02d}")
    
    while True:
        ahora = datetime.now().time()
        
        if ahora.hour == HORA_EJECUCION.hour and ahora.minute == HORA_EJECUCION.minute:
            print(f"🎯 HORA EJECUCIÓN: {ahora}")
            verificar_caducidades()
            time.sleep(60)
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        from django.db import models  # ← IMPORT FALTANTE
        main()
    except KeyboardInterrupt:
        print("\n🛑 Monitor detenido por usuario")
