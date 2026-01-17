## Plan: Sistema de Programas, Trámites y Solicitudes con Requisitos

Crear el flujo completo para que administradores gestionen programas sociales y trámites con sus requisitos, y para que ciudadanos puedan solicitar, subir documentación requerida y completar el proceso. Los modelos ya existen, solo falta implementar la capa API y validaciones.

### limitaciones técnicas

- el sistema está construido sobre Django y Django REST Framework y sera desplegado en un entorno con recursos limitados, por lo que las soluciones deben ser eficientes en términos de uso de memoria y procesamiento.

### Steps

1. **Crear API para gestión de Programas Sociales** - Implementar ViewSet, serializers y URLs en apoyos/api/ para CRUD de `ProgramaSocial` con sus requisitos anidados, accesible para administradores y funcionarios

2. **Implementar API de Solicitudes con carga de documentos** - Crear ViewSet completo en tramites/api/ para `Solicitud` y `DocumentoSolicitud`, incluyendo endpoints para crear solicitudes, subir archivos por requisito, y validar que todos los documentos requeridos estén completos

3. **Agregar API para gestión de Requisitos** - Crear endpoints en servicios/api/ para que administradores puedan agregar/editar requisitos asociados a tramites del catálogo o programas sociales

4. **Implementar permisos y validaciones** - Configurar permission classes basadas en roles (`CIUDADANO`, `FUNCIONARIO`, `ADMINISTRADOR`) para controlar quién puede crear programas/tramites vs quién puede solicitar, validar formatos de archivos (PDF, imágenes) y tamaños máximos

5. **Crear endpoints para flujo de ciudadano** - Implementar vistas especializadas: listar programas/tramites disponibles con requisitos, crear solicitud, verificar documentación completa, consultar estado de solicitudes propias

6. **Ampliar workflow de aprobación** - Extender `EstatusSolicitud` en core/choices.py con estados intermedios (EN_REVISION, REQUIERE_INFORMACION, APROBADO) y crear endpoints para que funcionarios cambien estados con comentarios/notas

### Further Considerations

1. **Validación de archivos** - ¿Qué formatos permitir (PDF, JPG, PNG)? ¿Límite de tamaño por archivo (ej: 5MB)? ¿Validar que el documento corresponda al requisito?

solo permitir pdf, jpg, png, max 5mb, validar tipo de documento 

2. **Notificaciones automáticas** - ¿Enviar emails automáticamente cuando cambie el estado de la solicitud usando el modelo `Notificacion` existente?

las notificaciones por email son importantes para mantener informado al ciudadano sobre el estado de su solicitud, pero también se debe considerar la posibilidad de notificaciones dentro de la plataforma

3. **Asignación de solicitudes** - ¿Asignar automáticamente solicitudes a funcionarios por dependencia, o permitir asignación manual? ¿Crear modelo SolicitudAsignacion?


la asignación automática puede agilizar el proceso, pero también es importante permitir la asignación manual para casos especiales o cargas de trabajo desiguales, se puede crear un modelo `SolicitudAsignacion` para registrar estas asignaciones y facilitar el seguimiento. Hay que considerar que cada solicitud puede requerir revisión por múltiples dependencias y que cada dependencia tiene varios funcionarios con diferentes cargas de trabajo.

4. **Historial de cambios** - ¿Registrar quién aprobó/rechazó y cuándo? ¿Usar HistoricalRecords en Solicitud o crear tabla de auditoría separada?

usar HistoricalRecords en Solicitud para mantener un historial completo de cambios, incluyendo quién realizó cada acción y cuándo, esto facilitará auditorías futuras y seguimiento de decisiones
