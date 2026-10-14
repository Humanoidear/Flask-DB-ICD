# Práctica 5 — pfSense (DMZ + Intranet)

Dos servicios Docker, uno en cada segmento:

| Servicio          | Carpeta    | Segmento  | IP           | Puerto |
| ----------------- | ---------- | --------- | ------------ | ------ |
| Web DMZ (HTML)    | `landing/` | DMZ       | 192.168.1.10 | 80     |
| Flask + SQLite    | `backend/` | Intranet  | 192.168.2.10 | 80     |

La base de datos es SQLite y va embebida dentro del contenedor Flask (sin
servidor aparte). Ninguno de los dos necesita variables de entorno.

## Ejecutar

```bash
# Web DMZ (en la MV de la DMZ)
cd landing && docker compose up -d

# Aplicación Flask (en la MV de la intranet)
cd backend && docker compose up -d --build
```

La web DMZ muestra asignatura, estudiante e IP (la toma de `location.hostname`).
La app Flask es un gestor de notas con SQLite; edita tu nombre en
`landing/index.html`.

Ver **`pfSense.md`** para la configuración completa de red (interfaces, DHCP,
DNS, NAT y firewall).
