# 🔐 Gestión de Certificados Digitales

## Estructura de Directorios

- `test/` - Certificados auto-firmados para desarrollo y testing
- `production/` - Certificados reales (NO incluir en git)
- `backup/` - Respaldos de certificados
- `templates/` - Plantillas y configuraciones

## Certificados de Test

Los certificados en `test/` son auto-firmados y solo para desarrollo.
**NO USAR EN PRODUCCIÓN**.

Generar certificados de test:
```bash
python certificados/generate_test_certs.py
```

## Certificados de Producción

Los certificados reales deben:
1. Ser emitidos por una CA autorizada por SUNAT
2. Estar en formato PFX con password
3. Almacenarse de forma segura
4. **NUNCA** incluirse en control de versiones

## Seguridad

- Los certificados de producción están en `.gitignore`
- Los passwords se almacenan encriptados en la BD
- Los certificados se cargan en memoria solo cuando se necesitan

## Estado del Nivel 2

✅ Estructura creada
⏳ Generador de certificados de test
⏳ Gestor de certificados
⏳ Implementación XML-DSig
⏳ Integración con API
