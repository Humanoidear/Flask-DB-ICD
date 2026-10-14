# Práctica 5 — Configuración completa de pfSense (DMZ + Intranet)

Guía paso a paso partiendo **solo** de un pfSense recién instalado con acceso a
su interfaz web (`https://<IP_pfSense>/`, usuario `admin`, contraseña
`pfsense`).

## 0. Objetivo y plan de red

pfSense hace de router/firewall con dos segmentos:

- **DMZ** (`192.168.1.0/24`): un servidor web público (HTML).
- **Intranet corporativa** (`192.168.2.0/24`): aplicación Flask con su base de
  datos (SQLite, embebida en el propio contenedor Flask).

```
                    Internet (DISCA, DHCP)
                            │
                       [ pfSense ]  WAN (IP pública)
                        │        │
            DMZ ────────┘        └──────── INTRANET
      192.168.1.1/24                 192.168.2.1/24
            │                            │
      [web-dmz]                       [flask]
      192.168.1.10                  192.168.2.10
```

| Interfaz pfSense | Segmento | Red            | IP pfSense  | Rango DHCP            |
| ---------------- | -------- | -------------- | ----------- | --------------------- |
| WAN              | Internet | DHCP (DISCA)   | pública     | —                     |
| DMZ              | DMZ      | 192.168.1.0/24 | 192.168.1.1 | 192.168.1.100–200     |
| INTRANET         | Intranet | 192.168.2.0/24 | 192.168.2.1 | 192.168.2.100–200     |

Servidores (contenedores Docker):

| Servicio       | Hostname | IP            | Puerto | Carpeta    |
| -------------- | -------- | ------------- | ------ | ---------- |
| Web DMZ        | web-dmz  | 192.168.1.10  | 80     | `landing/` |
| Flask + SQLite | flask    | 192.168.2.10  | 80     | `backend/` |

> Sustituye estas IPs por los segmentos que vayas a comunicar al profesor.

---

## 1. Preparar la red en Proxmox

### 1.1 Crear dos bridges internos (DMZ e Intranet)

En la interfaz de Proxmox: **nodo → System → Network → Create → Linux Bridge**.

1. Nombre: `vmbr1`, puertos vacíos (sin *Bridge ports*). **Create**.
2. Nombre: `vmbr2`, puertos vacíos. **Create**.
3. Pulsa **Apply Configuration**.

`vmbr0` (que ya existe, con la tarjeta física) será la salida a Internet/DISCA.

### 1.2 Añadir NICs a la MV de pfSense

**pfSense VM → Hardware → Add → Network Device**:

| NIC  | Bridge | Modelo  | Uso      |
| ---- | ------ | ------- | -------- |
| net0 | vmbr0  | VirtIO  | WAN      |
| net1 | vmbr1  | VirtIO  | DMZ      |
| net2 | vmbr2  | VirtIO  | INTRANET |

Si pfSense ya tiene una NIC en `vmbr0` (WAN), añade solo `net1` y `net2`.

### 1.3 Crear las MV/CT de los servidores

Crea 2 máquinas Debian (o CT LXC con Docker) con su NIC en el bridge correcto:

| MV/CT   | Bridge | IP estática      |
| ------- | ------ | ---------------- |
| web-dmz | vmbr1  | 192.168.1.10/24  |
| flask   | vmbr2  | 192.168.2.10/24  |

Instala Docker en cada una (o usa la template `datanotes-*`):

```bash
curl -fsSL https://get.docker.com | sh
```

---

## 2. Configurar las interfaces en pfSense

### 2.1 Asignar interfaces

**Interfaces → Assignments**:

1. En *Available network ports* deben aparecer las 3 NICs.
2. Asegúrate de tener: `WAN`, `OPT1` y `OPT2`.
   - Si faltan, pulsa **Add** para añadir `OPT1` y `OPT2`.
3. Anota qué NIC es cada una (en Proxmox, *Hardware* de la VM, el orden net0→WAN,
   net1→DMZ, net2→INTRANET).

### 2.2 WAN (Internet)

**Interfaces → WAN**:

- *IPv4 Configuration Type*: **DHCP**.
- **Save → Apply Changes**.

Comprueba en **Status → Interfaces** que WAN obtiene una IP pública.

### 2.3 DMZ

**Interfaces → OPT1**:

- *Enable*: ✔
- *Description*: `DMZ`
- *IPv4 Configuration Type*: **Static IPv4**
- *IPv4 Address*: `192.168.1.1/24`
- **Save → Apply Changes**.

### 2.4 INTRANET

**Interfaces → OPT2**:

- *Enable*: ✔
- *Description*: `INTRANET`
- *IPv4 Configuration Type*: **Static IPv4**
- *IPv4 Address*: `192.168.2.1/24`
- **Save → Apply Changes**.

> A partir de aquí las interfaces aparecen como `DMZ` e `INTRANET` en los menús.

---

## 3. Configurar DHCP

**Services → DHCP Server**:

### Pestaña DMZ

- *Enable DHCP server on DMZ interface*: ✔
- *Range*: `192.168.1.100` – `192.168.1.200`
- **Save**.

### Pestaña INTRANET

- *Enable DHCP server on INTRANET interface*: ✔
- *Range*: `192.168.2.100` – `192.168.2.200`
- **Save**.

> Los dos servidores usan IP fija (fuera del rango DHCP) para que NAT y DNS
> sean estables.

---

## 4. Configurar DNS

**Services → DNS Resolver → General Settings**:

1. *Enable DNS Resolver*: ✔
2. Abajo, en **Host Overrides**, añade una entrada por servidor:

| Host    | Domain | IP            | Description |
| ------- | ------ | ------------- | ----------- |
| web-dmz | local  | 192.168.1.10  | Web DMZ     |
| flask   | local  | 192.168.2.10  | App Flask   |

3. **Save → Apply Changes**.

Los clientes DHCP recibirán pfSense como DNS y resolverán `web-dmz.local` y
`flask.local`.

---

## 5. Reglas de firewall

Las interfaces nuevas en pfSense deniegan todo por defecto; hay que permitir el
tráfico de salida (y aislar la DMZ).

### 5.1 DMZ

**Firewall → Rules → DMZ** (orden de arriba a abajo):

| Acción | Protocolo | Source      | Destination   | Descripción            |
| ------ | --------- | ----------- | ------------- | ---------------------- |
| Block  | any       | DMZ net     | INTRANET net  | Aisla DMZ de Intranet  |
| Pass   | any       | DMZ net     | any           | DMZ → Internet/DNS     |

### 5.2 INTRANET

**Firewall → Rules → INTRANET**:

| Acción | Protocolo | Source       | Destination | Descripción          |
| ------ | --------- | ------------ | ----------- | -------------------- |
| Pass   | any       | INTRANET net | any         | Intranet → Internet  |

*(Opcional)* Añade un `Block` de `INTRANET net → DMZ net` si quieres impedir
también el tráfico intranet → DMZ.

### 5.3 WAN

Las reglas de WAN se crean automáticamente al configurar el NAT (sección 6).
No añadas nada manualmente: WAN deniega todo lo entrante salvo los puertos que
abras con port-forward.

---

## 6. NAT (acceso desde Internet)

**Firewall → NAT → Port Forward → Add**:

### Regla 1 — Web DMZ

| Campo                      | Valor               |
| -------------------------- | ------------------- |
| Interface                  | WAN                 |
| Protocol                   | TCP                 |
| Destination                | WAN address         |
| Destination port range     | HTTP (80)           |
| Redirect target IP         | 192.168.1.10        |
| Redirect target port       | HTTP (80)           |
| Filter rule association    | Add associated filter rule |

### Regla 2 — Aplicación Flask

| Campo                      | Valor               |
| -------------------------- | ------------------- |
| Interface                  | WAN                 |
| Protocol                   | TCP                 |
| Destination                | WAN address         |
| Destination port range     | 8080 (other)        |
| Redirect target IP         | 192.168.2.10        |
| Redirect target port       | HTTP (80)           |
| Filter rule association    | Add associated filter rule |

**Save → Apply Changes**. Con esto quedan creadas las reglas de paso en
**Firewall → Rules → WAN** para los puertos 80 y 8080.

> Con el puerto 80 ya ocupado por la web DMZ, la app Flask se expone en el
> puerto **8080** del WAN.

---

## 7. Desplegar los contenedores (Docker)

Copia el proyecto a cada MV/CT (o usa `git clone`). Sin variables de entorno.

### 7.1 Web DMZ (`192.168.1.10`)

```bash
cd landing
docker compose up -d
```

### 7.2 Aplicación Flask (`192.168.2.10`)

```bash
cd backend
docker compose up -d --build
```

> La intranet necesita salir a Internet para que `docker compose` descargue la
> imagen base (por eso la regla de salida de la sección 5.2).

---

## 8. Validación

Desde una máquina con salida a Internet (o desde el propio WAN):

```bash
# Web DMZ
curl http://<IP_WAN>/                    # página con "Zona desmilitarizada"

# Aplicación Flask (puerto 8080 del WAN)
curl http://<IP_WAN>:8080/api/health     # {"status":"ok","database":"sqlite"}
curl http://<IP_WAN>:8080/               # página de notas "Intranet corporativa"
```

Dentro de la intranet (desde la MV de Flask):

```bash
ping web-dmz.local                 # resolución DNS
```

Verifica DHCP: arranca una MV adicional en cada segmento y comprueba que recibe
IP automáticamente del rango configurado.

---

## 9. Solución de problemas

- **WAN no obtiene IP pública**: revisa que la NIC de WAN esté en `vmbr0` (la
  que llega al DISCA) y que *IPv4 Configuration Type* sea DHCP.
- **Los servidores no navegan / no descargan imágenes**: falta la regla de
  salida (`Pass`) en la interfaz DMZ/INTRANET.
- **No se accede desde Internet**: confirma que en *Port Forward* tienes
  *Filter rule association = Add associated filter rule*, y que el servicio web
  está escuchando (`ss -tlnp` dentro de la MV).
- **La DMZ accede a la intranet**: revisa el orden de las reglas en
  **Firewall → Rules → DMZ** (el `Block` debe ir arriba del `Pass`).
- **DNS no resuelve**: asegúrate de que el DNS Resolver está habilitado y que
  los clientes usan pfSense como DNS (el DHCP lo hace automático).
- **El puerto 80/8080 ya está en uso en pfSense**: la propia GUI de pfSense usa
  80/443 en su interfaz; usa otro puerto WAN o una IP pública distinta.
