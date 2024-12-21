# TaskFlow

TaskFlow es una plataforma open source que democratiza la automatización de notebooks y scripts Python, permitiendo a científicos de datos y desarrolladores programar ejecuciones sin necesidad de conocimientos en infraestructura o cron, con un enfoque en la simplicidad y la colaboración comunitaria.

## Características Principales

- 📊 Automatización de notebooks (.ipynb) y scripts Python (.py)
- 🔄 Sistema de versionado ligero
- ⏰ Scheduling avanzado con interfaz visual
- 📱 Sistema de notificaciones (Email, Slack, Telegram)
- 📈 Monitoreo y métricas en tiempo real
- 🔐 Gestión segura de secretos y configuraciones
- 🌍 Marketplace comunitario de templates

## Requisitos Previos

- Docker y Docker Compose
- Git
- Make (opcional, pero recomendado)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/taskflow.git
cd taskflow
```

2. Copiar el archivo de variables de entorno:
```bash
cp .env.example .env
```

3. Configurar las variables de entorno en el archivo `.env` según tus necesidades.

4. Instalar dependencias del frontend:
```bash
make frontend-install
```

5. Construir los contenedores:
```bash
make build
```

6. Iniciar los servicios:
```bash
make up
```

7. Aplicar las migraciones de la base de datos:
```bash
make migrate
```

## URLs de Servicios (Local)

- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/admin
- **Nginx (Proxy)**: http://localhost
- **Base de datos**: localhost:5432
- **Redis**: localhost:6379

## Estructura del Proyecto

```
taskflow/
├── docker/                  # Configuraciones de Docker
├── backend/                 # API Django y lógica de negocio
│   ├── apps/               # Aplicaciones Django
│   ├── config/             # Configuraciones del proyecto
│   └── requirements/       # Dependencias por ambiente
├── frontend/               # Aplicación Next.js
│   ├── src/               # Código fuente
│   └── public/            # Archivos estáticos
└── docker-compose.yml     # Configuración de servicios
```

## Comandos Útiles

```bash
# Iniciar servicios
make up

# Detener servicios
make down

# Ver logs
make logs

# Acceder al shell de Django
make shell

# Acceder al shell del frontend
make frontend-shell

# Ejecutar pruebas
make test

# Formatear código
make format

# Verificar estilo de código
make lint

# Agregar componente UI (shadcn)
make frontend-add-component component=button
```

## Desarrollo

### Backend
- Django 5.0 con Django REST Framework
- Celery para tareas asíncronas
- PostgreSQL como base de datos
- Redis para caché y mensajería

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui para componentes
- React Query para gestión de estado

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 