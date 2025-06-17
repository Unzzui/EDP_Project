# 🌳 Estrategia de Branches - EDP MVP

## Estructura de Branches

```
main (estable, releases oficiales)
├── production (deploy automático a Render)
├── development (desarrollo activo)
└── feature/* (características específicas)
```

## 🔄 Workflow Recomendado

### Para nuevas características:

1. `git checkout development`
2. `git pull origin development`
3. `git checkout -b feature/nueva-caracteristica`
4. Desarrollar y commit
5. `git push origin feature/nueva-caracteristica`
6. Crear Pull Request hacia `development`

### Para deploy a producción:

1. Merge `development` → `main` (vía PR)
2. Merge `main` → `production` (deploy automático)

### Para hotfixes urgentes:

1. `git checkout production`
2. `git checkout -b hotfix/bug-critico`
3. Fix y commit
4. Merge hacia `production` Y `development`

## 🚀 Configuración de Deploy

### Production Branch → Render

- Branch: `production`
- Auto-deploy: ✅ Habilitado
- Environment: Production
- Secret Files: ✅ Configurados

### Development Branch → Render (Opcional)

- Branch: `development`
- Auto-deploy: ✅ Habilitado
- Environment: Staging
- Base de datos separada

## 📋 Checklist de Release

Antes de merge `development` → `main`:

- [ ] Todos los tests pasan
- [ ] Code review completado
- [ ] Documentación actualizada
- [ ] Variables de entorno verificadas
- [ ] Secret Files configurados (si aplica)

Antes de merge `main` → `production`:

- [ ] Testing en staging exitoso
- [ ] Backup de base de datos (si aplica)
- [ ] Notificar al equipo del deploy
- [ ] Monitorear logs post-deploy

## 🛡️ Protección de Branches

Recomendado configurar en GitHub:

- `main`: Protegida, requiere PR
- `production`: Protegida, requiere PR
- `development`: Abierta para commits directos del equipo

## 🔧 Comandos Útiles

```bash
# Cambiar a development para nuevo trabajo
git checkout development
git pull origin development

# Crear feature branch
git checkout -b feature/mi-nueva-feature

# Deploy a producción
git checkout main
git merge development
git push origin main
git checkout production
git merge main
git push origin production

# Ver todas las branches
git branch -a

# Limpiar branches merged
git branch -d feature/completed-feature
```

## 📊 Estado Actual

- ✅ `main`: Branch principal estable
- ✅ `production`: Conectada a Render para deploy automático
- ✅ `development`: Para desarrollo activo del equipo
- ✅ Todas las branches sincronizadas con el remoto
