
# 📄 Sistema de Gestión de Documentos

Este proyecto implementa un sistema de gestión de documentos con:

- Usuarios con UUID ('accounts' app)
- Compañías con UUID
- Documentos asociados a compañías y entidades de negocio (vehículos, empleados, etc.)
- Subida de archivos **local** (simula bucket)
- Descarga de archivos vía URL local ('GET /api/documents/<uuid>/download')
- Flujo de validación jerárquico con estados 'P' (pendiente), 'A' (aprobado), 'R' (rechazado)
- API construida con Django REST Framework
- Seguridad básica: solo usuarios con acceso pueden operar sobre documentos

---

## Estructura General del Proyecto

djangoProject/
│ manage.py
│ README.md
│ requirements.txt
│
├── djangoProject/ → Configuración principal de Django
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
│
├── accounts/ → Modelo de usuario con UUID
│ ├── models.py
│ ├── admin.py
│ ├── apps.py
│ └── serializers.py
│
├── documentos/ → Gestión de documentos, subida, descarga y validación
│ ├── models.py
│ ├── views.py
│ ├── serializers.py
│ ├── urls.py
│ ├── utils/presign.py
│ └── services/validation.py
│
└── media/ → Archivos subidos localmente

## Cómo levantar proyecto
1. python -m venv venv
2. activate venv
3. pip install -r requirements.txt

## Cómo correr migraciones
4. python manage.py makemigrations
5. python manage.py migrate

## Cómo correr pruebas
6. python manage.py createsuperuser (Para poder entrar al panel de administrador)
7. python manage.py runserver

En mi caso fui a /admin/ y cree unos datos de ejemplo para poder ejecutar las siguientes pruebas
como una compañia llamada ACME, una entidad vehiculo relacionada a la compañia ACME

### Prueba crear documento
- POST /api/documents/ -> crear documento
{
  "company_id": <company_id>,
  
  "entity": {"entity_type":"vehicle","entity_id":<entity_id>},
  
  "document": 
  	{"name":"soat.pdf",
  	"mime_type":"application/pdf",
  	"size_bytes":123,
  	"bucket_key":"companies/<company_id>/vehicles/<entity_id>/soat.pdf"},
  "validation_flow":
  	{"enabled": true,
  	 "steps":
  	 	[{"order":1,"approver_user_id":<user1_id>},
  	 	 {"order":2,"approver_user_id":<user2_id>}]}
 }
### Prueba aprobar documento
- POST /api/documents/<id>/approve/ -> aprobar
{ "actor_user_id": <user1_id>, "reason": "Cumple requisitos." }

### Prueba rechazar documento
- POST /api/documents/<id>/reject/ -> rechazar
{ "actor_user_id": <user2_id>, "reason": "Documento ilegible." }

### Pruebar descargar documento
- GET /api/documents/<id>/download/

Me debe retornar la URL
