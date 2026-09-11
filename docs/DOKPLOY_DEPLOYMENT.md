# Dokploy Deployment Guide for Cholbe AI

This document provides step-by-step instructions for deploying this Django + Tailwind CSS application using **Dokploy**.

---

## Prerequisites

1. A VPS running Ubuntu (e.g., DigitalOcean, Hetzner, Linode, AWS) with at least 2GB of RAM.
2. Dokploy installed on your VPS. If not installed, run:
   ```bash
   curl -sSL https://dokploy.com/install.sh | sh
   ```
3. A domain name pointed to your VPS IP address (with `A` records for `yourdomain.com` and `*.yourdomain.com` if using subdomains).

---

## Step 1: Create a PostgreSQL Database in Dokploy

Django needs a PostgreSQL database in production. Let's set it up first inside the Dokploy panel:

1. Log into your **Dokploy Panel**.
2. Go to **Databases** -> **Create Database** -> Choose **PostgreSQL**.
3. Give it a name (e.g., `bikriai-db`).
4. Once created, click on the database and go to **Credentials**. Note the following fields (you will need them in Step 3):
   * **Host** (usually the internal container name or service name, e.g., `postgres`)
   * **Port** (default: `5432`)
   * **Database Name** (e.g., `postgres` or whatever you configured)
   * **Username** (e.g., `postgres` or `admin`)
   * **Password**

---

## Step 2: Create a New Application in Dokploy

1. Go to **Applications** -> Click **Create Application**.
2. Give it a name (e.g., `bikriai-app`).
3. Select **Git Provider** (GitHub, GitLab, or Self-hosted). Connect your repository:
   * **Repository**: `ssshiponu/sae`
   * **Branch**: `main` (or your deployment branch)
4. Under **Build Configuration**:
   * Change the build type from **Nixpacks** to **Dockerfile**.
   * Leave the Dockerfile path as `./Dockerfile` (or `Dockerfile`).
5. Under **Port Mapping**:
   * Expose port **`8000`** (which Gunicorn runs on inside the container).

---

## Step 3: Configure Environment Variables in Dokploy

In your application dashboard under **Environment Variables**, add the following keys. Make sure to toggle **Secret** for sensitive credentials.

| Environment Variable | Description / Recommended Value |
| :--- | :--- |
| `DEBUG` | `False` |
| `SECRET_KEY` | *A long, random, secure secret string* |
| `LOGGING_FILE` | `console` *(Routes Django logs to Dokploy dashboard)* |
| `SITE_DOMAIN` | `yourdomain.com` *(The domain you are mapping to the app)* |
| `ENCRYPTION_KEY` | *Your Fernet encryption key (e.g., `h3r5BPHvJ5FIH7AzmA59ZrLiJJXyifhkw_aot7SH0pc=`)* |
| **Database Variables** | |
| `DB_NAME` | *Database Name from Step 1* |
| `DB_USER` | *Username from Step 1* |
| `DB_PASSWORD` | *Password from Step 1* |
| `DB_HOST` | *Host/Service name from Step 1 (e.g., `postgres` or IP)* |
| `DB_PORT` | `5432` |
| **Email Variables** | |
| `ADMIN_EMAIL` | `bikriai24@gmail.com` |
| `MAIN_EMAIL` | `bikriai24@gmail.com` |
| `MAIN_EMAIL_HOST_PASSWORD` | *Your SMTP application password* |
| **AI Credentials** | |
| `OPENROUTER_API_KEY` | *Your OpenRouter API Key* |
| `GOOGLE_TAG_MANAGER_ID` | *Your GTM container ID (optional)* |
| **Facebook & WhatsApp APIs** | |
| `FACEBOOK_VERIFY_TOKEN` | *Your webhook verification token* |
| `FACEBOOK_APP_ID` | *Your Meta App ID* |
| `FACEBOOK_APP_SECRET` | *Your Meta App Secret* |
| `WHATSAPP_EMBEDDED_SIGNUP_CONFIG_ID` | *Your WhatsApp Embedded Signup configuration ID* |
| **Payment Gateways** | |
| `BKASH_USERNAME` | *Your bKash username* |
| `BKASH_PASSWORD` | *Your bKash password* |
| `BKASH_APP_KEY` | *Your bKash app key* |
| `BKASH_APP_SECRET` | *Your bKash app secret* |
| `MANUAL_PAYMENT_NUMBER` | *Your manual bKash/Nagad number* |

---

## Step 4: Configure Persistent Volumes (CRITICAL)

By default, Docker containers are ephemeral. When you redeploy, any files uploaded by users to the `media/` directory will be deleted. To prevent this, we must mount a persistent volume:

1. In the application settings in Dokploy, go to **Volumes**.
2. Click **Create Volume** or **Mount Volume**.
3. Fill in the fields:
   * **Host Path**: `/var/lib/dokploy/volumes/bikriai-media` (or any custom folder on the VPS host)
   * **Mount Path**: `/app/media` (this matches Django's `MEDIA_ROOT` in the container)
4. Click **Save**.

Now, all files uploaded to the media folder will persist across deployments.

---

## Step 5: Configure Domain and SSL (Traefik)

1. Go to the **Domains** tab of your Dokploy application.
2. Click **Add Domain**.
3. Input your domain name (e.g., `bikriai.expert` or `yourdomain.com`).
4. Enable **HTTPS / SSL** (Dokploy handles Let's Encrypt certificates automatically).
5. Specify the path routing if needed (usually defaults to `/` on port `8000`).

---

## Step 6: Deploy

1. Go to the **Deploy** tab or click the **Deploy** button in the top right.
2. Dokploy will:
   * Clone your Git repository.
   * Start the multi-stage build: compile Tailwind CSS v4 in Node.js, and then assemble the Python container.
   * Run the `entrypoint.sh` script, which applies database migrations (`python manage.py migrate`) and collects static files (`python manage.py collectstatic`).
   * Start Gunicorn and attach the Traefik proxy.
3. Watch the logs. Once complete, your site will be live and secure at `https://yourdomain.com`.

---

## Troubleshooting & Useful Info

* **Viewing Logs**: Click **Logs** in your Dokploy application to see the live console output.
* **Accessing the Console / Shell**: If you need to run Django commands (like creating a superuser), go to the **Console** tab in Dokploy and execute:
  ```bash
  python manage.py createsuperuser
  ```
