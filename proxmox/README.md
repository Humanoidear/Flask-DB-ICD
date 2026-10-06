# Proxmox LXC deployment

Three Debian 12 LXC containers, each running one Docker Compose stack.

| CT  | Hostname        | Role                          | Ports      |
| --- | --------------- | ----------------------------- | ---------- |
| 200 | `datanotes-db`  | PostgreSQL 16 (SGBD)          | 5432       |
| 201 | `datanotes-app` | Flask API + React frontend    | 80         |
| 202 | `datanotes-web` | nginx static landing page     | 80         |

## Prerequisites

- A Proxmox VE host (root shell).
- A Debian 12 LXC template. If you do not have one:

  ```bash
  pveam update
  pveam available | grep debian-12
  pveam download local debian-12-standard_12.7-1_amd64.tar.zst
  ```

- The project directory present on the Proxmox host (this `proxmox/` folder's
  parent). Copy it with `scp -r` or `git clone` onto the host.
- Internet access from the containers (Docker install + image pulls).

## 1. Configure

Edit `config.env`: set the bridge/gateway/subnet to match your Proxmox network,
the three IPs you want, and **change `DB_PASSWORD` and `CT_PASSWORD`**.

## 2. Create the containers

```bash
cd proxmox
sudo ./create-cts.sh
```

This creates the three LXCs with `nesting=1,keyctl=1`, gives them static IPs,
starts them and installs Docker.

## 3. Deploy the stacks

```bash
sudo ./deploy.sh
```

This copies the project into `/opt/datanotes` inside each CT, writes the
`.env` files, builds the app image (Node build + Python) and starts everything.

When it finishes:

- Landing page: `http://<WEB_IP>/`
- Notes app:    `http://<APP_IP>/`
- Database:     `<DB_IP>:5432`

## Updating after a code change

Copy the project to the host again, then:

```bash
sudo ./deploy.sh                 # rebuilds and restarts everything
```

## Useful commands

```bash
pct exec 201 -- docker compose -f /opt/datanotes/backend/docker-compose.yml logs -f
pct exec 201 -- docker compose -f /opt/datanotes/backend/docker-compose.yml restart
pct exec 200 -- docker exec -it datanotes-db psql -U datanotes
```

## Notes and troubleshooting

- **Docker in LXC** needs `nesting=1` (and `keyctl=1` for some images). The
  create script sets both on unprivileged containers.
- **No internet / get.docker.com blocked** — install `docker.io` and
  `docker-compose-v2` from Debian repos instead:
  `apt-get install -y docker.io docker-compose-v2`.
- **Container has no network** — check `BRIDGE`/`GATEWAY` in `config.env` and
  that the bridge is the one your VMs use (`ip -br a` on the host).
- **Change the database password** by editing `config.env`, deleting the CT's
  `database/.env`, and re-running `deploy.sh` (or `docker compose down -v` on
  the DB CT to also wipe data).
- The database is exposed on the LAN. Restrict it with the Proxmox firewall or
  `pct set 200 --net0 ...,firewall=1` plus a rule allowing only the app CT.
