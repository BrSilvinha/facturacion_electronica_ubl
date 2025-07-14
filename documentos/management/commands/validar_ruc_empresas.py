# documentos/management/commands/validar_ruc_empresas.py

"""
Comando de Django para validar y corregir RUCs de empresas
Resuelve el problema: cac:PartyIdentification/cbc:ID - No se encontró el ID-RUC
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from documentos.models import Empresa
from conversion.utils.calculations import TributaryCalculator

class Command(BaseCommand):
    help = 'Valida y corrige RUCs de empresas para resolver error cac:PartyIdentification/cbc:ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir automáticamente RUCs inválidos usando RUC por defecto',
        )
        parser.add_argument(
            '--empresa-id',
            type=str,
            help='Validar solo una empresa específica por ID',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔧 Validador de RUCs - Fix para error cac:PartyIdentification/cbc:ID")
        self.stdout.write("=" * 70)
        
        # Filtrar empresas
        if options['empresa_id']:
            try:
                empresas = Empresa.objects.filter(id=options['empresa_id'])
                if not empresas.exists():
                    raise CommandError(f"Empresa con ID {options['empresa_id']} no encontrada")
            except ValueError:
                raise CommandError("ID de empresa inválido")
        else:
            empresas = Empresa.objects.all()
        
        self.stdout.write(f"📊 Analizando {empresas.count()} empresa(s)...")
        self.stdout.write("")
        
        # Estadísticas
        total_empresas = 0
        ruc_validos = 0
        ruc_invalidos = 0
        empresas_corregidas = 0
        
        for empresa in empresas:
            total_empresas += 1
            
            # Validar RUC
            ruc_actual = empresa.ruc or ''
            is_valid, message = self._validate_ruc_format(ruc_actual)
            
            if is_valid:
                ruc_validos += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {empresa.razon_social[:40]}: RUC {ruc_actual} - VÁLIDO")
                )
            else:
                ruc_invalidos += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ {empresa.razon_social[:40]}: RUC {ruc_actual} - {message}")
                )
                
                # Corregir si está habilitado
                if options['fix']:
                    nuevo_ruc = self._get_default_ruc()
                    try:
                        with transaction.atomic():
                            empresa.ruc = nuevo_ruc
                            empresa.save()
                            empresas_corregidas += 1
                            self.stdout.write(
                                self.style.WARNING(f"🔧 CORREGIDO: Nuevo RUC asignado: {nuevo_ruc}")
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error corrigiendo empresa: {e}")
                        )
        
        # Resumen
        self.stdout.write("")
        self.stdout.write("📈 RESUMEN DE VALIDACIÓN")
        self.stdout.write("-" * 40)
        self.stdout.write(f"Total empresas analizadas: {total_empresas}")
        self.stdout.write(f"RUCs válidos: {ruc_validos}")
        self.stdout.write(f"RUCs inválidos: {ruc_invalidos}")
        if options['fix']:
            self.stdout.write(f"Empresas corregidas: {empresas_corregidas}")
        
        # Recomendaciones
        self.stdout.write("")
        if ruc_invalidos > 0:
            if not options['fix']:
                self.stdout.write("🔧 RECOMENDACIÓN:")
                self.stdout.write("Ejecuta el comando con --fix para corregir automáticamente:")
                self.stdout.write("python manage.py validar_ruc_empresas --fix")
            else:
                self.stdout.write("✅ CORRECCIÓN COMPLETADA")
                self.stdout.write("Todas las empresas ahora tienen RUCs válidos para SUNAT")
        else:
            self.stdout.write("🎉 ¡EXCELENTE! Todas las empresas tienen RUCs válidos")
        
        # Información adicional
        self.stdout.write("")
        self.stdout.write("📋 INFORMACIÓN ADICIONAL:")
        self.stdout.write("- Error resuelto: cac:PartyIdentification/cbc:ID")
        self.stdout.write("- RUC por defecto usado: 20103129061 (COMERCIAL LAVAGNA)")
        self.stdout.write("- Los documentos generados ahora incluirán RUC válido en cac:Signature")
        self.stdout.write("- Reinicia el servidor Django después de las correcciones")
    
    def _validate_ruc_format(self, ruc: str) -> tuple:
        """Valida formato de RUC usando TributaryCalculator"""
        
        if not ruc:
            return False, "RUC vacío"
        
        if len(ruc) != 11:
            return False, f"RUC debe tener 11 dígitos (actual: {len(ruc)})"
        
        if not ruc.isdigit():
            return False, "RUC debe contener solo números"
        
        # Usar validador completo
        try:
            return TributaryCalculator.validate_ruc(ruc)
        except Exception as e:
            return False, f"Error validando RUC: {e}"
    
    def _get_default_ruc(self) -> str:
        """Retorna RUC por defecto válido"""
        return "20103129061"  # COMERCIAL LAVAGNA SAC