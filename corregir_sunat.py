#!/usr/bin/env python
"""
Script de corrección automática para problemas comunes
"""

import subprocess
import sys

def instalar_dependencias():
    """Instalar dependencias faltantes"""
    dependencias = [
        'zeep',
        'lxml', 
        'requests',
        'cryptography'
    ]
    
    for dep in dependencias:
        print(f"Instalando {dep}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])

def verificar_certificados():
    """Verificar que los certificados estén en su lugar"""
    from pathlib import Path
    
    cert_real = Path('certificados/production/cert_20103129061.pfx')
    if not cert_real.exists():
        print("❌ Certificado real no encontrado")
        print("💡 Coloca tu certificado .pfx en certificados/production/")
        return False
    
    print("✅ Certificado real encontrado")
    return True

def main():
    print("🔧 CORRECCIÓN AUTOMÁTICA DE PROBLEMAS SUNAT")
    print("=" * 50)
    
    try:
        print("1. Instalando dependencias...")
        instalar_dependencias()
        
        print("2. Verificando certificados...")
        verificar_certificados()
        
        print("3. Ejecutando diagnóstico...")
        from diagnostico_sunat_completo import DiagnosticoSUNAT
        diagnostico = DiagnosticoSUNAT()
        diagnostico.ejecutar_diagnostico_completo()
        
    except Exception as e:
        print(f"❌ Error en corrección: {e}")

if __name__ == '__main__':
    main()
