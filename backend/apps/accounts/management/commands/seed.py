"""
Management command: python manage.py seed

Creates a complete demo dataset for development and manual QA:
  - 1 superuser (admin)
  - 5 customers with team members and varied statuses
  - Product catalog with monthly subscriptions and one-time implementation services
  - Subscriptions + licenses + service accesses per customer
  - 6 months of invoice history per customer
  - API keys + license quotas (apenas para clientes de assinatura mensal)
  - In-app notifications per customer
  - Audit log entries

Usage:
  docker compose exec django-api python manage.py seed
  docker compose exec django-api python manage.py seed --flush   # wipe & reseed
"""

import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed the database with demo data for development"
    frontend_url = getattr(settings, "FRONTEND_URL", "https://app.papermoon.com.br").rstrip("/")

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        with transaction.atomic():
            admin = self._create_admin()
            products = self._create_products()
            customers = self._create_customers(products)
            self._create_invoice_history(customers, products)
            self._create_daily_usage(customers)
            self._create_notifications(customers)
            self._create_audit_entries(customers, admin)
            self._create_invitations(customers, admin)
            self._create_outbox_events(customers)
            pending_users = self._create_pending_registrations()
            self._create_cms_pages()

        self.stdout.write(self.style.SUCCESS("\n✓ Seed concluído com sucesso!\n"))
        self._print_summary(admin, customers, pending_users)

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    def _flush(self):
        from apps.audit.models import AuditLog
        from apps.billing.models import Invoice
        from apps.cms.models import ServicePage
        from apps.customers.models import Customer, CustomerProfile, Invitation
        from apps.licensing.models import ApiKey, DailyApiUsage, LicenseQuota
        from apps.notifications.models import Notification
        from apps.products.models import Pricing, Product, ServiceComponent
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        self.stdout.write("  Limpando dados existentes...")
        for model in [
            AuditLog,
            Notification,
            OutboxEvent,
            ServiceAccess,
            License,
            Subscription,
            ApiKey,
            DailyApiUsage,
            LicenseQuota,
            Invoice,
            Invitation,
            CustomerProfile,
            Customer,
            ServicePage,
            Pricing,
            ServiceComponent,
            Product,
        ]:
            model.objects.all().delete()

    # ------------------------------------------------------------------
    # Admin
    # ------------------------------------------------------------------

    def _create_admin(self):
        from apps.accounts.models import CustomUser

        user, created = CustomUser.objects.get_or_create(
            email="admin@papermoon.com",
            defaults={
                "username": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write("  ✓ Admin criado: admin@papermoon.com / admin123")
        else:
            self.stdout.write("  · Admin já existe: admin@papermoon.com")
        return user

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    def _create_products(self):
        from apps.products.models import Pricing, Product, ServiceComponent

        catalog = [
            {
                "name": "WhatsApp via API Meta",
                "slug": "whatsapp-api",
                "description": (
                    "API oficial da Meta + Chatwoot multiagente + n8n automação — "
                    "instalados e configurados na sua VPS. Número verificado, zero risco de ban."
                ),
                "services": ["meta_whatsapp", "chatwoot", "n8n"],
                "pricings": [
                    {
                        "billing_cycle": "monthly",
                        "amount": "499.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "WhatsApp via Evolution API",
                "slug": "whatsapp-evolution",
                "description": (
                    "Evolution API self-hosted + Chatwoot multiagente + n8n automação — "
                    "múltiplas instâncias WhatsApp na sua VPS, sem custo por mensagem."
                ),
                "services": ["evolution_api", "chatwoot", "n8n"],
                "pricings": [
                    {
                        "billing_cycle": "monthly",
                        "amount": "299.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Chatwoot",
                "slug": "chatwoot",
                "description": (
                    "Central de atendimento omnichannel open-source auto-hospedada — "
                    "WhatsApp, e-mail e web chat em uma única interface, na sua VPS."
                ),
                "services": ["chatwoot"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "n8n — Automação de Fluxos",
                "slug": "n8n",
                "description": (
                    "n8n self-hosted com 400+ integrações nativas — fluxos de automação "
                    "personalizados entregues prontos, rodando na sua infraestrutura."
                ),
                "services": ["n8n"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Evolution API",
                "slug": "evolution-api",
                "description": (
                    "Evolution API self-hosted — gateway WhatsApp multi-instância com webhooks "
                    "granulares, integração nativa com n8n e Chatwoot, rodando na sua VPS."
                ),
                "services": ["evolution_api"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "GLPI Helpdesk",
                "slug": "glpi",
                "description": (
                    "Implantação completa de GLPI com parametrização ITIL 4 — categorias, SLAs, "
                    "filas de atendimento, integrações e treinamento da equipe."
                ),
                "services": ["glpi"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Zabbix Monitoramento",
                "slug": "zabbix",
                "description": (
                    "Implantação de Zabbix com hosts, triggers, alertas e dashboards — "
                    "alinhado à gestão de disponibilidade e capacidade (ITIL 4)."
                ),
                "services": ["zabbix"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2000.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Proxmox VE",
                "slug": "proxmox",
                "description": (
                    "Implantação completa de Proxmox VE com virtualização, clustering, "
                    "storage ZFS/Ceph e treinamento da equipe de infra."
                ),
                "services": ["proxmox"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "TrueNAS",
                "slug": "truenas",
                "description": (
                    "Implantação de NAS open-source TrueNAS com ZFS, replicação, "
                    "snapshots agendados e compartilhamento NFS/SMB na sua rede local."
                ),
                "services": ["truenas"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Nextcloud",
                "slug": "nextcloud",
                "description": (
                    "Implantação de nuvem privada Nextcloud com apps, colaboração em tempo real, "
                    "SSL e configuração de backup automatizado."
                ),
                "services": ["nextcloud"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1800.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "AAPanel",
                "slug": "aapanel",
                "description": (
                    "Implantação de painel de hospedagem AAPanel com stack LEMP ou LAMP, "
                    "SSL automático e gerenciamento de múltiplos sites."
                ),
                "services": ["aapanel"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "RustDesk Self-Hosted",
                "slug": "rustdesk",
                "description": (
                    "Implantação do RustDesk Server (hbbs + hbbr) via Docker na sua VPS — "
                    "acesso remoto criptografado ponta a ponta sem custo por dispositivo. "
                    "Inclui SSL, chaves criptográficas e build de cliente customizado."
                ),
                "services": ["rustdesk"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Windows Server",
                "slug": "windows-server",
                "description": (
                    "Implantação e configuração de Windows Server com Active Directory, "
                    "servidor de arquivos NTFS, GPOs, DNS, DHCP e integração com Microsoft 365."
                ),
                "services": ["windows-server"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "3500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Samba — Servidor de Arquivos",
                "slug": "samba",
                "description": (
                    "Implantação de servidor de arquivos Samba em Linux com compartilhamentos "
                    "SMB/CIFS, permissões POSIX + ACL, autenticação AD e backup incremental."
                ),
                "services": ["samba"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1800.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Redes Corporativas",
                "slug": "redes",
                "description": (
                    "Projeto, implantação e configuração de rede corporativa — "
                    "switching, roteamento, VLANs, firewall e VPN para a sua empresa."
                ),
                "services": [],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Cabeamento Estruturado",
                "slug": "cabeamento",
                "description": (
                    "Instalação certificada de cabeamento Cat5e, Cat6 e fibra óptica — "
                    "projeto, execução e certificação conforme normas ABNT."
                ),
                "services": [],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2000.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Manutenção de Servidores",
                "slug": "manutencao",
                "description": (
                    "Diagnóstico, limpeza, manutenção preventiva e corretiva de servidores "
                    "físicos — substituição de componentes e relatório técnico."
                ),
                "services": [],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Backup Corporativo",
                "slug": "backup",
                "description": (
                    "Implementação de política de backup e recuperação de desastres (DRP) — "
                    "backup local + offsite com retenção, testes periódicos e documentação."
                ),
                "services": [],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1800.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Plone CMS",
                "slug": "plone",
                "description": (
                    "Implantação de portal corporativo e intranet com Plone 6 — "
                    "gestão documental, workflow de publicação, controle de acesso por papel "
                    "e integração com LDAP/Active Directory."
                ),
                "services": ["plone"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "3500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Keycloak — IAM e SSO",
                "slug": "keycloak",
                "description": (
                    "Implantação de Identity and Access Management com Keycloak — "
                    "SSO, MFA, OAuth2/OIDC, SAML 2.0 e integração com Active Directory "
                    "para todas as aplicações da empresa."
                ),
                "services": ["keycloak"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "3000.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Tailscale",
                "slug": "tailscale",
                "description": (
                    "Implantação de rede privada mesh com Tailscale — acesso remoto seguro, "
                    "ACLs por identidade, subnet routers e integração com SSO sem expor "
                    "serviços na internet."
                ),
                "services": ["tailscale"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Twenty CRM",
                "slug": "twenty-crm",
                "description": (
                    "Implantação de CRM open-source Twenty self-hosted — pipeline de vendas, "
                    "gestão de contatos e empresas, integração de e-mail e webhooks. "
                    "Alternativa ao Salesforce/HubSpot sem custo por usuário."
                ),
                "services": ["twenty_crm"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "2500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "Papermark",
                "slug": "papermark",
                "description": (
                    "Implantação de plataforma self-hosted de compartilhamento de documentos "
                    "Papermark — links rastreáveis, analytics por página e proteção por e-mail. "
                    "Alternativa ao DocSend com dados no servidor do cliente."
                ),
                "services": ["papermark"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1500.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
            {
                "name": "CrowdSec",
                "slug": "crowdsec",
                "description": (
                    "Implantação do CrowdSec em toda a infraestrutura Linux — detecção "
                    "comportamental de ataques, bouncers Nginx/iptables e acesso à blocklist "
                    "colaborativa global de IPs maliciosos."
                ),
                "services": ["crowdsec"],
                "pricings": [
                    {
                        "billing_cycle": "one_time",
                        "amount": "1200.00",
                        "max_api_calls": 0,
                        "max_users": 0,
                    },
                ],
            },
        ]

        products = {}
        for item in catalog:
            product, created = Product.objects.get_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "description": item.get("description", "")},
            )
            existing_services = set(product.components.values_list("service_key", flat=True))
            for svc in item["services"]:
                if svc not in existing_services:
                    ServiceComponent.objects.create(product=product, service_key=svc)

            existing_cycles = set(product.pricings.values_list("billing_cycle", flat=True))
            for p in item["pricings"]:
                if p["billing_cycle"] not in existing_cycles:
                    Pricing.objects.create(product=product, **p)

            if created:
                self.stdout.write(f"  ✓ Produto criado: {product.name}")
            else:
                self.stdout.write(f"  · Produto já existe: {product.name}")
            products[item["slug"]] = product

        return products

    # ------------------------------------------------------------------
    # Customers + subscriptions + API keys
    # ------------------------------------------------------------------

    def _create_customers(self, products):
        from apps.accounts.models import CustomUser
        from apps.customers.models import Customer, CustomerProfile
        from apps.licensing.models import ApiKey, LicenseQuota
        from apps.products.models import Pricing
        from apps.subscriptions.models import License, ServiceAccess, Subscription

        demos = [
            {
                "company": "Acme Ltda",
                "document": "11.222.333/0001-81",
                "email": "owner@acme.com",
                "members": [
                    {"email": "dev@acme.com", "username": "dev_acme", "role": "admin"},
                ],
                "product_slug": "whatsapp-api",
                "billing_cycle": "monthly",
                "status": "active",
            },
            {
                "company": "Globo Corp",
                "document": "44.555.666/0001-72",
                "email": "owner@globo.com",
                "members": [
                    {"email": "ti@globo.com", "username": "ti_globo", "role": "admin"},
                    {"email": "suporte@globo.com", "username": "suporte_globo", "role": "member"},
                ],
                "product_slug": "whatsapp-evolution",
                "billing_cycle": "monthly",
                "status": "active",
            },
            {
                "company": "Mega Tech",
                "document": "77.888.999/0001-63",
                "email": "owner@mega.com",
                "members": [],
                "product_slug": "whatsapp-api",
                "billing_cycle": "monthly",
                "status": "suspended",
            },
            {
                "company": "TechFlow Solutions",
                "document": "22.333.444/0001-52",
                "email": "owner@techflow.com",
                "members": [
                    {"email": "ops@techflow.com", "username": "ops_techflow", "role": "member"},
                ],
                "product_slug": "glpi",
                "billing_cycle": "one_time",
                "status": "active",
            },
            {
                "company": "StartupXYZ",
                "document": "33.444.555/0001-43",
                "email": "owner@startupxyz.com",
                "members": [],
                "product_slug": "proxmox",
                "billing_cycle": "one_time",
                "status": "cancelled",
            },
        ]

        created_customers = []
        for demo in demos:
            customer, c_new = Customer.objects.get_or_create(
                document=demo["document"],
                defaults={
                    "company_name": demo["company"],
                    "status": demo["status"],
                },
            )

            username = demo["email"].replace("@", "_").replace(".", "_")
            user, u_new = CustomUser.objects.get_or_create(
                email=demo["email"],
                defaults={"username": username},
            )
            if u_new:
                user.set_password("demo1234")
                user.save()

            CustomerProfile.objects.get_or_create(
                user=user,
                customer=customer,
                defaults={"role": "owner"},
            )

            # Team members
            for m in demo.get("members", []):
                member_user, mu_new = CustomUser.objects.get_or_create(
                    email=m["email"],
                    defaults={"username": m["username"]},
                )
                if mu_new:
                    member_user.set_password("demo1234")
                    member_user.save()
                CustomerProfile.objects.get_or_create(
                    user=member_user,
                    customer=customer,
                    defaults={"role": m["role"]},
                )

            # Subscription + License
            product = products[demo["product_slug"]]
            pricing = Pricing.objects.filter(
                product=product, billing_cycle=demo["billing_cycle"]
            ).first()

            sub_status = (
                Subscription.Status.ACTIVE
                if demo["status"] == "active"
                else Subscription.Status.SUSPENDED
                if demo["status"] == "suspended"
                else Subscription.Status.CANCELLED
            )

            sub, s_new = Subscription.objects.get_or_create(
                customer=customer,
                product=product,
                defaults={
                    "pricing": pricing,
                    "status": sub_status,
                    "starts_at": timezone.now() - datetime.timedelta(days=180),
                    "expires_at": timezone.now() + datetime.timedelta(days=15),
                },
            )

            if s_new:
                lic_status = (
                    License.Status.ACTIVE
                    if demo["status"] == "active"
                    else License.Status.SUSPENDED
                    if demo["status"] == "suspended"
                    else License.Status.REVOKED
                )
                lic = License.objects.create(
                    subscription=sub,
                    customer=customer,
                    key=License.generate_key(),
                    status=lic_status,
                    valid_from=sub.starts_at,
                    valid_until=sub.expires_at,
                )
                from apps.products.models import ServiceComponent

                svc_status = (
                    ServiceAccess.Status.ACTIVE
                    if demo["status"] == "active"
                    else ServiceAccess.Status.SUSPENDED
                )
                for comp in ServiceComponent.objects.filter(product=product):
                    ServiceAccess.objects.create(
                        license=lic,
                        service_key=comp.service_key,
                        status=svc_status,
                        external_id=f"{self.frontend_url}/{comp.service_key}/{customer.id.hex[:8]}",
                    )

            # API Key + Quota — apenas para serviços de assinatura mensal
            is_recurring = pricing and pricing.billing_cycle in ("monthly", "annual")
            if is_recurring and not ApiKey.objects.filter(customer=customer).exists():
                ApiKey.objects.create(customer=customer)
                LicenseQuota.objects.create(
                    customer=customer,
                    max_api_calls=10000,
                    used_api_calls=0,
                    reset_at=timezone.now() + datetime.timedelta(days=30),
                )

            action = "criado" if c_new else "já existe"
            member_count = len(demo.get("members", []))
            self.stdout.write(
                f"  ✓ Customer {action}: {customer.company_name} "
                f"({demo['status']}, {member_count + 1} usuário{'s' if member_count else ''}) "
                f"— {demo['email']} / demo1234"
            )
            created_customers.append(customer)

        return created_customers

    # ------------------------------------------------------------------
    # Invoice history (6 months paid + current state)
    # ------------------------------------------------------------------

    def _create_invoice_history(self, customers, products):
        from apps.billing.models import Invoice
        from apps.subscriptions.models import Subscription

        today = datetime.date.today()

        for customer in customers:
            sub = Subscription.objects.filter(customer=customer).first()
            if not sub or not sub.pricing:
                continue
            amount = sub.pricing.amount

            # 6 months of paid history
            for i in range(1, 7):
                due = today - datetime.timedelta(days=30 * i)
                Invoice.objects.get_or_create(
                    customer=customer,
                    due_date=due,
                    status="paid",
                    defaults={"amount": amount, "subscription": sub},
                )

            # Current state based on customer status
            if customer.status == "active":
                # Pending: upcoming invoice
                Invoice.objects.get_or_create(
                    customer=customer,
                    due_date=today + datetime.timedelta(days=10),
                    status="pending",
                    defaults={"amount": amount, "subscription": sub},
                )
            elif customer.status == "suspended":
                # Overdue: invoice that triggered suspension
                Invoice.objects.get_or_create(
                    customer=customer,
                    due_date=today - datetime.timedelta(days=12),
                    status="overdue",
                    defaults={"amount": amount, "subscription": sub},
                )

        self.stdout.write("  ✓ Histórico de faturas criado (6 meses por customer)")

    # ------------------------------------------------------------------
    # Daily API usage (30-day history for chart demo)
    # ------------------------------------------------------------------

    def _create_daily_usage(self, customers):
        from apps.licensing.models import DailyApiUsage, LicenseQuota

        today = datetime.date.today()

        # Deterministic weekday weights: Mon-Fri peak, Sat-Sun low
        weekday_weights = [1.3, 1.2, 1.1, 1.2, 1.3, 0.4, 0.3]

        # Gera uso diário realista para clientes com quota (assinatura mensal)
        baseline_calls = 5000  # calls mensais simuladas para demonstração
        for customer in customers:
            quota = LicenseQuota.objects.filter(customer=customer).first()
            if not quota:
                continue

            days = 30
            dates = [today - datetime.timedelta(days=days - 1 - i) for i in range(days)]
            weights = [weekday_weights[d.weekday()] for d in dates]
            weight_sum = sum(weights)

            for i, d in enumerate(dates):
                calls = int(baseline_calls * weights[i] / weight_sum)
                DailyApiUsage.objects.update_or_create(
                    customer=customer,
                    date=d,
                    defaults={"calls_count": calls},
                )

        self.stdout.write("  ✓ Histórico diário de uso de API criado (30 dias por customer)")

    # ------------------------------------------------------------------
    # In-app notifications
    # ------------------------------------------------------------------

    def _create_notifications(self, customers):
        from apps.notifications.models import Notification

        templates = [
            {
                "event_type": "customer.created",
                "subject": "Bem-vindo à PaperMoon!",
                "body": "Sua conta foi criada com sucesso. Acesse o painel para configurar seus serviços.",
                "status": Notification.Status.SENT,
            },
            {
                "event_type": "payment.processed",
                "subject": "Pagamento confirmado",
                "body": "Sua fatura foi paga com sucesso. O serviço continua ativo.",
                "status": Notification.Status.SENT,
            },
            {
                "event_type": "billing.cycle",
                "subject": "Nova fatura disponível",
                "body": "Uma nova fatura foi gerada para este mês. Vencimento em 10 dias.",
                "status": Notification.Status.PENDING,
            },
        ]

        for customer in customers:
            if customer.status == "cancelled":
                continue  # cancelled customers have no active notifications
            for t in templates:
                Notification.objects.get_or_create(
                    event_type=t["event_type"],
                    channel=Notification.Channel.IN_APP,
                    recipient=str(customer.id),
                    defaults={
                        "subject": t["subject"],
                        "body": t["body"],
                        "status": t["status"],
                    },
                )

        self.stdout.write("  ✓ Notificações in-app criadas")

    # ------------------------------------------------------------------
    # Audit log entries
    # ------------------------------------------------------------------

    def _create_audit_entries(self, customers, admin):
        from apps.audit.models import AuditLog

        for customer in customers:
            AuditLog.objects.get_or_create(
                action="create",
                resource_type="customer",
                resource_id=str(customer.id),
                defaults={
                    "user": admin,
                    "changes": {
                        "company_name": customer.company_name,
                        "status": customer.status,
                    },
                },
            )
            if customer.status == "suspended":
                AuditLog.objects.get_or_create(
                    action="suspend",
                    resource_type="customer",
                    resource_id=str(customer.id),
                    defaults={
                        "user": admin,
                        "changes": {"status": {"from": "active", "to": "suspended"}},
                    },
                )
            elif customer.status == "cancelled":
                AuditLog.objects.get_or_create(
                    action="cancel",
                    resource_type="customer",
                    resource_id=str(customer.id),
                    defaults={
                        "user": admin,
                        "changes": {"status": {"from": "active", "to": "cancelled"}},
                    },
                )

        self.stdout.write("  ✓ Entradas de audit log criadas")

    # ------------------------------------------------------------------
    # Invitations (D1 — pending invites for manual testing of accept flow)
    # ------------------------------------------------------------------

    def _create_invitations(self, customers, admin):
        import secrets

        from apps.customers.models import CustomerProfile, Invitation

        pending_invites = [
            ("newdev@acme.com", "admin"),
            ("analyst@globo.com", "member"),
            ("junior@techflow.com", "member"),
        ]

        active_customers = [c for c in customers if c.status == "active"]
        for i, customer in enumerate(active_customers):
            if i >= len(pending_invites):
                break
            email, role = pending_invites[i]

            # owner of this customer
            owner_profile = (
                CustomerProfile.objects.filter(customer=customer, role="owner")
                .select_related("user")
                .first()
            )
            invited_by = owner_profile.user if owner_profile else admin

            Invitation.objects.get_or_create(
                customer=customer,
                email=email,
                defaults={
                    "invited_by": invited_by,
                    "role": role,
                    "token": secrets.token_urlsafe(48),
                    "status": "pending",
                    "expires_at": timezone.now() + datetime.timedelta(days=7),
                },
            )

        self.stdout.write(
            f"  ✓ Convites pendentes criados: {min(len(pending_invites), len(active_customers))}"
        )

    # ------------------------------------------------------------------
    # OutboxEvents (D2 — sample events for retry logic testing)
    # ------------------------------------------------------------------

    def _create_outbox_events(self, customers):
        from shared.models import OutboxEvent

        # Already-processed event (normal, cleaned by cleanup task)
        active = [c for c in customers if c.status == "active"]
        if active:
            OutboxEvent.objects.get_or_create(
                event_type="payment.processed",
                processed=True,
                defaults={
                    "payload": {"customer_id": str(active[0].id), "amount": "199.00"},
                    "processed_at": timezone.now() - datetime.timedelta(hours=2),
                    "retry_count": 0,
                },
            )

        # Failed event (retry_count=5, permanently failed — shows up in logs)
        if len(active) >= 2:
            OutboxEvent.objects.get_or_create(
                event_type="subscription.expiring_soon",
                processed=False,
                defaults={
                    "payload": {"customer_id": str(active[1].id), "days_remaining": 7},
                    "retry_count": 5,
                    "last_error": "ConnectionError: max retries exceeded calling Chatwoot",
                    "failed_at": timezone.now() - datetime.timedelta(hours=1),
                },
            )

        # Pending event (not yet processed — shows Celery consumer picking it up)
        if customers:
            OutboxEvent.objects.get_or_create(
                event_type="quota.warning",
                processed=False,
                defaults={
                    "payload": {
                        "customer_id": str(
                            customers[3].id if len(customers) > 3 else customers[0].id
                        ),
                        "pct": 85,
                    },
                    "retry_count": 0,
                },
            )

        self.stdout.write("  ✓ OutboxEvents de demonstração criados (processed, failed, pending)")

    # ------------------------------------------------------------------
    # Pending registrations (users without CustomerProfile)
    # ------------------------------------------------------------------

    def _create_pending_registrations(self):
        from apps.accounts.models import CustomUser
        from shared.models import OutboxEvent

        pending = [
            {
                "first_name": "Pedro",
                "last_name": "Carvalho",
                "email": "pedro.carvalho@startupx.com.br",
                "company_name": "Startup X Tecnologia",
                "phone": "(11) 98765-4321",
            },
            {
                "first_name": "Fernanda",
                "last_name": "Martins",
                "email": "fernanda@logisticapro.com.br",
                "company_name": "Logística Pro Ltda",
                "phone": "(21) 97654-3210",
            },
            {
                "first_name": "Rodrigo",
                "last_name": "Alves",
                "email": "rodrigo@construtora-delta.com",
                "company_name": "Construtora Delta",
                "phone": "",
            },
        ]

        users = []
        for p in pending:
            user, created = CustomUser.objects.get_or_create(
                email=p["email"],
                defaults={
                    "username": p["email"],
                    "first_name": p["first_name"],
                    "last_name": p["last_name"],
                    "phone": p["phone"],
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()
                OutboxEvent.objects.create(
                    event_type="user.registered",
                    payload={
                        "user_id": str(user.id),
                        "email": user.email,
                        "name": f"{p['first_name']} {p['last_name']}",
                        "company_name": p["company_name"],
                        "phone": p["phone"],
                    },
                )
                users.append((user, p["company_name"]))

        if users:
            self.stdout.write(f"  ✓ {len(users)} cadastros pendentes criados (sem CustomerProfile)")
        else:
            self.stdout.write("  · Cadastros pendentes já existem")

        return users

    # ------------------------------------------------------------------
    # CMS Pages
    # ------------------------------------------------------------------

    def _create_cms_pages(self):
        from apps.cms.models import (
            ServiceFAQ,
            ServiceFeatureGroup,
            ServiceFeatureItem,
            ServicePage,
            ServiceResponsibility,
            ServiceStep,
        )
        from apps.products.models import Product

        pages_data = [
            {
                "slug": "whatsapp-api",
                "tagline": "WhatsApp oficial direto nos seus fluxos",
                "description": (
                    "Conecte sua operação ao WhatsApp Business API via Meta de forma nativa, "
                    "sem intermediários. Escale atendimento, automações e notificações com "
                    "qualidade enterprise e SLA garantido."
                ),
                "steps": [
                    (
                        "01",
                        "Homologação",
                        "Verificamos CNPJ, domínio e número junto à Meta. Essa etapa depende da análise e da documentação aprovada pela plataforma.",
                    ),
                    (
                        "02",
                        "Configuração do WABA",
                        "Criamos o WhatsApp Business Account e vinculamos o número escolhido.",
                    ),
                    (
                        "03",
                        "Integração n8n",
                        "Montamos os fluxos de entrada e saída no seu ambiente n8n.",
                    ),
                    (
                        "04",
                        "Testes & go-live",
                        "Executamos bateria de testes e ativamos a produção com monitoramento.",
                    ),
                ],
                "faqs": [
                    (
                        "Posso usar meu número atual?",
                        "Sim, desde que ainda não esteja ativo em outro WABA. O processo exige migração prévia.",
                    ),
                    (
                        "Qual o custo por mensagem?",
                        "A Meta cobra por conversa iniciada (24 h). Os valores variam por categoria e região — fornecemos a tabela atualizada no onboarding.",
                    ),
                    (
                        "Preciso de CNPJ?",
                        "Sim. A verificação de negócio da Meta exige CNPJ ativo e com atividade coerente ao uso.",
                    ),
                    (
                        "Posso ter múltiplos números?",
                        "Sim, cada número exige um número de telefone separado no WABA.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Mensageria",
                        [
                            "Templates HSM",
                            "Mensagens de sessão",
                            "Mídia e documentos",
                            "Reações e emojis",
                        ],
                    ),
                    (
                        "Automação",
                        [
                            "Webhooks em tempo real",
                            "Integração n8n nativa",
                            "Filas e roteamento",
                            "Chatbot com IA",
                        ],
                    ),
                    (
                        "Gestão",
                        [
                            "Painel de métricas",
                            "Relatório de entregas",
                            "Gestão de templates",
                            "Multi-agente",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Processo de verificação junto à Meta",
                    "Configuração do WABA e número",
                    "Integração com n8n e Chatwoot",
                    "Monitoramento pós-implantação",
                ],
                "client_does": [
                    "Fornecer CNPJ e documentos da empresa",
                    "Indicar o número a ser ativado",
                    "Aprovar templates de mensagem",
                ],
            },
            {
                "slug": "whatsapp-evolution",
                "tagline": "WhatsApp multi-sessão sem burocracia",
                "description": (
                    "Solução baseada em Evolution API para equipes que precisam de múltiplas "
                    "sessões WhatsApp Web sem a complexidade de homologação Meta. "
                    "Ideal para operações internas, testes e equipes de médio porte."
                ),
                "steps": [
                    (
                        "01",
                        "Provisionamento",
                        "Subimos o servidor Evolution API no ambiente do cliente com SSL e domínio.",
                    ),
                    (
                        "02",
                        "Sessões & QR Code",
                        "Configuramos as sessões e conectamos os números via QR Code.",
                    ),
                    (
                        "03",
                        "Webhooks",
                        "Integramos os eventos de mensagem com n8n, Chatwoot ou sistema próprio.",
                    ),
                    (
                        "04",
                        "Monitoramento",
                        "Configuramos alertas de reconexão automática e painel de status.",
                    ),
                ],
                "faqs": [
                    (
                        "Qual a diferença para a API Meta?",
                        "A Evolution API usa WhatsApp Web (não é oficial). É mais simples de ativar, mas não tem suporte a templates HSM.",
                    ),
                    (
                        "Posso usar múltiplos números?",
                        "Sim, cada sessão é um número independente — sem limite técnico.",
                    ),
                    (
                        "É estável para produção?",
                        "Sim, com reconexão automática configurada e monitoramento Zabbix.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Mensageria",
                        [
                            "Texto, mídia e documentos",
                            "Grupos e listas",
                            "Mensagens em massa",
                            "Webhooks de eventos",
                        ],
                    ),
                    (
                        "Integração",
                        ["n8n nativo", "Chatwoot pronto", "API REST documentada", "SDK TypeScript"],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do servidor",
                    "Configuração de sessões e webhooks",
                    "Integração com ferramentas do cliente",
                    "Suporte e manutenção mensal",
                ],
                "client_does": [
                    "Fornecer acesso ao servidor ou cloud",
                    "Disponibilizar os números de WhatsApp",
                    "Escanear o QR Code de ativação",
                ],
            },
            {
                "slug": "glpi",
                "tagline": "Help desk completo sem custo de licença",
                "description": (
                    "Implantamos e configuramos o GLPI — sistema open source de gestão de chamados "
                    "e ativos de TI — no seu ambiente, com SLA, base de conhecimento e "
                    "integrações com WhatsApp e e-mail."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do GLPI no servidor do cliente com banco de dados dedicado.",
                    ),
                    (
                        "02",
                        "Configuração",
                        "Categorias, SLA, filas de atendimento, grupos e e-mails configurados.",
                    ),
                    (
                        "03",
                        "Integração",
                        "Conectamos WhatsApp e e-mail para abertura automática de chamados.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Sessão de treinamento com a equipe de atendimento e TI.",
                    ),
                ],
                "faqs": [
                    (
                        "GLPI é gratuito?",
                        "Sim, é open source sob licença GPL. A PaperMoon cobra pela implantação e suporte.",
                    ),
                    (
                        "Posso migrar chamados do sistema atual?",
                        "Sim, importamos via CSV ou API dependendo do sistema de origem.",
                    ),
                    ("Tem app mobile?", "Sim, o GLPI possui app oficial para iOS e Android."),
                    (
                        "Suporta múltiplas entidades?",
                        "Sim, o GLPI suporta hierarquia de entidades — ideal para grupos empresariais.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Atendimento",
                        [
                            "Abertura por WhatsApp/e-mail/portal",
                            "SLA com escalonamento",
                            "Respostas automáticas",
                            "Pesquisa de satisfação",
                        ],
                    ),
                    (
                        "TI",
                        [
                            "Inventário de ativos",
                            "Gestão de contratos",
                            "Base de conhecimento",
                            "Relatórios e dashboards",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração completa",
                    "Integração com canais de comunicação",
                    "Treinamento da equipe",
                    "Suporte pós-implantação",
                ],
                "client_does": [
                    "Fornecer servidor ou acesso à cloud",
                    "Definir categorias e SLA desejados",
                    "Participar do treinamento",
                ],
            },
            {
                "slug": "zabbix",
                "tagline": "Monitoramento de infraestrutura em tempo real",
                "description": (
                    "Implantamos o Zabbix para monitorar servidores, redes, serviços e "
                    "aplicações com alertas inteligentes por WhatsApp, e-mail ou Telegram. "
                    "Saiba de problemas antes que seus usuários percebam."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do Zabbix Server no ambiente indicado com PostgreSQL otimizado.",
                    ),
                    (
                        "02",
                        "Agentes",
                        "Instalação dos agentes Zabbix em todos os hosts a monitorar.",
                    ),
                    (
                        "03",
                        "Templates",
                        "Aplicamos templates oficiais e personalizados por tipo de serviço.",
                    ),
                    (
                        "04",
                        "Alertas",
                        "Configuramos triggers, ações e notificações por WhatsApp e e-mail.",
                    ),
                ],
                "faqs": [
                    (
                        "Zabbix é gratuito?",
                        "Sim, a versão community é open source. A PaperMoon cobra pela implantação e suporte.",
                    ),
                    (
                        "Quantos hosts posso monitorar?",
                        "Não há limite técnico. Dimensionamos o servidor conforme o volume.",
                    ),
                    (
                        "Tem dashboard web?",
                        "Sim, o Zabbix possui dashboards totalmente configuráveis.",
                    ),
                    (
                        "Posso monitorar serviços cloud?",
                        "Sim, suportamos AWS, Azure, GCP e serviços via API.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Monitoramento",
                        [
                            "CPU, memória e disco",
                            "Rede e latência",
                            "Serviços e processos",
                            "URLs e certificados SSL",
                        ],
                    ),
                    (
                        "Alertas",
                        [
                            "WhatsApp e e-mail",
                            "Telegram e Slack",
                            "Escalonamento por horário",
                            "Supressão de falsos positivos",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Zabbix",
                    "Implantação de agentes nos hosts",
                    "Configuração de templates e triggers",
                    "Treinamento da equipe de TI",
                ],
                "client_does": [
                    "Fornecer acesso SSH aos servidores",
                    "Indicar os serviços críticos a monitorar",
                    "Definir contatos para alertas",
                ],
            },
            {
                "slug": "proxmox",
                "tagline": "Virtualização enterprise open source",
                "description": (
                    "Implantamos o Proxmox VE para consolidar sua infraestrutura em um "
                    "ambiente de virtualização de alta disponibilidade, com backup automático "
                    "e gerenciamento centralizado via interface web."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Instalação do Proxmox VE no hardware dedicado com configuração de rede.",
                    ),
                    (
                        "02",
                        "Armazenamento",
                        "Configuração de pools de armazenamento ZFS/Ceph conforme a necessidade.",
                    ),
                    (
                        "03",
                        "Migração",
                        "Migração das VMs e containers existentes para o novo ambiente.",
                    ),
                    (
                        "04",
                        "Backup",
                        "Configuração de backup automático para armazenamento local ou nuvem.",
                    ),
                ],
                "faqs": [
                    (
                        "Proxmox é gratuito?",
                        "Sim, a versão community é gratuita. Suporte oficial Proxmox é opcional.",
                    ),
                    ("Suporta alta disponibilidade?", "Sim, com cluster Proxmox e múltiplos nós."),
                    (
                        "Posso virtualizar Windows?",
                        "Sim, Proxmox suporta VMs Windows e Linux com aceleração de hardware.",
                    ),
                    (
                        "Tem painel web?",
                        "Sim, gerenciamento completo via interface web com suporte a noVNC.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Virtualização",
                        [
                            "KVM para VMs completas",
                            "LXC para containers",
                            "Templates e snapshots",
                            "Live migration",
                        ],
                    ),
                    (
                        "Storage",
                        [
                            "ZFS com checksum",
                            "Ceph distribuído",
                            "NFS e iSCSI",
                            "Backup incremental",
                        ],
                    ),
                    (
                        "Rede",
                        [
                            "Bridges e VLANs",
                            "SDN (Software Defined Networking)",
                            "Firewall integrado",
                            "IPv6 nativo",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Proxmox",
                    "Configuração de storage e rede",
                    "Migração de VMs existentes",
                    "Configuração de backup automático",
                ],
                "client_does": [
                    "Fornecer o hardware ou servidores bare-metal",
                    "Indicar os sistemas a migrar",
                    "Definir política de backup desejada",
                ],
            },
            # ── Chatwoot ────────────────────────────────────────────────
            {
                "slug": "chatwoot",
                "tagline": "Central de atendimento multicanal self-hosted",
                "description": (
                    "Implantamos o Chatwoot na sua VPS: inbox unificado para WhatsApp, e-mail, "
                    "chat ao vivo e Telegram, com múltiplos agentes, labels, SLAs e "
                    "relatórios de desempenho — tudo sem custo por agente."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do Chatwoot via Docker na VPS com SSL e domínio próprio.",
                    ),
                    (
                        "02",
                        "Canais",
                        "Integração dos canais: WhatsApp (via API Meta ou Evolution), e-mail e chat ao vivo.",
                    ),
                    (
                        "03",
                        "Equipe",
                        "Criação de agentes, caixas de entrada, labels e horários de atendimento.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe no painel e entrega de documentação operacional.",
                    ),
                ],
                "faqs": [
                    (
                        "Quantos agentes posso ter?",
                        "Ilimitado — não há cobrança por agente no Chatwoot self-hosted.",
                    ),
                    (
                        "Suporta WhatsApp?",
                        "Sim, via API oficial Meta ou Evolution API (WhatsApp não oficial).",
                    ),
                    (
                        "Tem relatórios?",
                        "Sim — tempo de resposta, volume por canal, produtividade por agente e CSAT.",
                    ),
                    (
                        "Funciona com chatbot?",
                        "Sim, via integração com n8n ou webhooks para automação de respostas.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Canais",
                        [
                            "WhatsApp Business API",
                            "E-mail IMAP/SMTP",
                            "Chat ao vivo (widget)",
                            "Telegram",
                        ],
                    ),
                    (
                        "Gestão",
                        [
                            "Múltiplos agentes e equipes",
                            "Labels e prioridades",
                            "SLA por canal",
                            "Horário de atendimento",
                        ],
                    ),
                    (
                        "Relatórios",
                        [
                            "CSAT por conversa",
                            "Tempo médio de resposta",
                            "Volume por canal",
                            "Produtividade por agente",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do Chatwoot via Docker com SSL e domínio",
                    "Configuração de todos os canais solicitados",
                    "Criação inicial de agentes e caixas de entrada",
                    "Treinamento da equipe e documentação",
                ],
                "client_does": [
                    "Fornecer VPS com Ubuntu 22.04 (mínimo 2 vCPU, 4 GB RAM)",
                    "Definir canais a integrar e agentes da equipe",
                    "Gerenciar usuários e conversas após a entrega",
                ],
            },
            # ── n8n ─────────────────────────────────────────────────────
            {
                "slug": "n8n",
                "tagline": "Automação de processos sem código na sua VPS",
                "description": (
                    "Implantamos e configuramos o n8n self-hosted para automatizar "
                    "processos entre sistemas: CRM, WhatsApp, e-mail, APIs e bancos de dados — "
                    "sem custo por execução e com seus dados no seu servidor."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do n8n via Docker com SSL, domínio e autenticação configurados.",
                    ),
                    (
                        "02",
                        "Credenciais",
                        "Configuração das credenciais dos sistemas a integrar (WhatsApp, CRM, ERP, APIs).",
                    ),
                    (
                        "03",
                        "Workflows",
                        "Criação dos primeiros workflows conforme os processos mapeados.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe para criar e manter automações e entrega de documentação.",
                    ),
                ],
                "faqs": [
                    (
                        "n8n é gratuito?",
                        "A versão self-hosted é open-source e gratuita. Você paga apenas o servidor.",
                    ),
                    (
                        "Precisa saber programar?",
                        "Não. A maioria dos workflows é construída visualmente. JavaScript é opcional para lógica avançada.",
                    ),
                    (
                        "Quantas execuções posso ter?",
                        "Ilimitadas — sem restrição por execução no self-hosted.",
                    ),
                    (
                        "Integra com WhatsApp?",
                        "Sim, via nós nativos para Evolution API, Chatwoot e API Meta.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Integrações",
                        [
                            "400+ conectores nativos",
                            "HTTP Request para qualquer API REST",
                            "Webhook de entrada e saída",
                            "Schedule (cron)",
                        ],
                    ),
                    (
                        "Lógica",
                        [
                            "Condicionais e loops",
                            "Transformação de dados JSON",
                            "Código JavaScript customizado",
                            "Sub-workflows reutilizáveis",
                        ],
                    ),
                    (
                        "Operação",
                        [
                            "Interface web para monitoramento",
                            "Histórico de execuções",
                            "Retry automático em falhas",
                            "Alertas por e-mail",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do n8n self-hosted com SSL e autenticação",
                    "Configuração das credenciais dos sistemas a integrar",
                    "Criação dos primeiros workflows do cliente",
                    "Treinamento da equipe e documentação",
                ],
                "client_does": [
                    "Fornecer VPS com Ubuntu 22.04 (mínimo 1 vCPU, 2 GB RAM)",
                    "Mapear os processos e integrações desejados",
                    "Fornecer credenciais dos sistemas a integrar",
                ],
            },
            # ── Evolution API ─────────────────────────────────────────────
            {
                "slug": "evolution-api",
                "tagline": "Gateway WhatsApp self-hosted com múltiplas instâncias e webhooks",
                "description": (
                    "Implantamos a Evolution API na sua VPS: múltiplas instâncias WhatsApp, "
                    "webhooks granulares por evento e integração nativa com n8n e Chatwoot — "
                    "stack completo de atendimento auto-hospedado."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy da Evolution API com banco de dados, Redis e painel de administração.",
                    ),
                    (
                        "02",
                        "Instâncias",
                        "Criação das instâncias WhatsApp, scan do QR Code e configuração de reconexão automática.",
                    ),
                    (
                        "03",
                        "Integrações",
                        "Integração com n8n para automação e com Chatwoot para atendimento humano.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe no gerenciamento de instâncias, webhooks e fluxos.",
                    ),
                ],
                "faqs": [
                    (
                        "É oficial da Meta?",
                        "Não — usa o protocolo WhatsApp Web. Mais ágil, sem aprovação da Meta, com risco de bloqueio em uso intenso.",
                    ),
                    (
                        "Posso ter vários números?",
                        "Sim. A Evolution API suporta múltiplas instâncias no mesmo servidor — cada uma com seu número independente.",
                    ),
                    (
                        "Integra com Chatwoot?",
                        "Sim. A PaperMoon configura a integração completa: mensagens chegam no Chatwoot para atendimento multiagente.",
                    ),
                    (
                        "É cobrado por mensagem?",
                        "Não. A PaperMoon cobra pelo projeto de implantação — sem custo por mensagem ou por instância.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Instâncias",
                        [
                            "Múltiplas instâncias WhatsApp no mesmo servidor",
                            "Reconexão automática em caso de queda",
                            "Envio de texto, mídia, documentos e áudio",
                            "Painel de administração web",
                        ],
                    ),
                    (
                        "Automação",
                        [
                            "Webhooks granulares por tipo de evento",
                            "Integração nativa com n8n",
                            "TypeBot para bots conversacionais",
                            "RabbitMQ para filas de alta disponibilidade",
                        ],
                    ),
                    (
                        "Atendimento",
                        [
                            "Integração com Chatwoot para handoff humano",
                            "API REST documentada com Swagger",
                            "Logs de mensagens enviadas e recebidas",
                            "Controle de sessões por API Key",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação da Evolution API com Docker na sua VPS",
                    "Configuração das instâncias e reconexão automática",
                    "Integração com n8n para automação de fluxos",
                    "Integração com Chatwoot para atendimento multiagente",
                    "Treinamento da equipe e documentação",
                ],
                "client_does": [
                    "Fornecer VPS com Ubuntu 22.04 (mínimo 1 vCPU, 2 GB RAM)",
                    "Fornecer os números de WhatsApp a conectar",
                    "Respeitar os limites de volume para evitar bloqueio",
                ],
            },
            # ── TrueNAS ─────────────────────────────────────────────────
            {
                "slug": "truenas",
                "tagline": "NAS open-source com ZFS, snapshots e compartilhamento seguro",
                "description": (
                    "Implantamos o TrueNAS Scale ou Core na sua infraestrutura: storage "
                    "centralizado com ZFS, replicação automática, snapshots agendados e "
                    "compartilhamento via NFS, SMB e iSCSI."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Instalação do TrueNAS no servidor dedicado e configuração de pools ZFS.",
                    ),
                    (
                        "02",
                        "Storage",
                        "Criação de datasets, permissões e quotas por departamento ou usuário.",
                    ),
                    (
                        "03",
                        "Compartilhamento",
                        "Configuração de shares NFS/SMB e acesso de máquinas Windows/Linux.",
                    ),
                    (
                        "04",
                        "Backup",
                        "Configuração de replicação para site secundário ou cloud S3.",
                    ),
                ],
                "faqs": [
                    (
                        "TrueNAS é gratuito?",
                        "Sim — TrueNAS Core e Scale são open-source e gratuitos. Suporte enterprise é opcional.",
                    ),
                    (
                        "Qual a diferença entre Core e Scale?",
                        "Core usa FreeBSD (mais maduro). Scale usa Linux com suporte a containers Docker e clustering.",
                    ),
                    (
                        "Suporta máquinas virtuais?",
                        "TrueNAS Scale suporta VMs via KVM e aplicações containerizadas via Kubernetes.",
                    ),
                    (
                        "Como funciona o backup?",
                        "TrueNAS suporta replicação ZFS para outro NAS ou para S3 (Backblaze, AWS, MinIO).",
                    ),
                ],
                "feature_groups": [
                    (
                        "Storage",
                        [
                            "ZFS com proteção contra bit-rot",
                            "Snapshots agendados com retenção",
                            "Compressão e deduplicação",
                            "RAID-Z1/Z2/Z3",
                        ],
                    ),
                    (
                        "Compartilhamento",
                        [
                            "SMB/CIFS para Windows",
                            "NFS para Linux/macOS",
                            "iSCSI para VMs e bare-metal",
                            "FTP/SFTP",
                        ],
                    ),
                    (
                        "Resiliência",
                        [
                            "Replicação ZFS para site remoto",
                            "Alertas de disco via S.M.A.R.T.",
                            "Hot spare automático",
                            "Scrub semanal de integridade",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do TrueNAS no hardware dedicado",
                    "Configuração de pools ZFS, datasets e permissões",
                    "Configuração de shares NFS/SMB e replicação",
                    "Treinamento e documentação operacional",
                ],
                "client_does": [
                    "Fornecer o servidor/hardware com discos adequados",
                    "Definir estrutura de pastas e permissões por equipe",
                    "Gerenciar usuários e snapshots após a entrega",
                ],
            },
            # ── Nextcloud ───────────────────────────────────────────────
            {
                "slug": "nextcloud",
                "tagline": "Nuvem privada corporativa — arquivos, calendário e colaboração",
                "description": (
                    "Implantamos o Nextcloud na sua VPS: armazenamento de arquivos, "
                    "calendário, contatos, edição colaborativa de documentos e videochamadas — "
                    "tudo na sua infraestrutura, sem custo por usuário."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do Nextcloud via Docker com SSL, domínio e banco PostgreSQL.",
                    ),
                    (
                        "02",
                        "Apps",
                        "Instalação e configuração dos apps essenciais: Collabora Online, Calendar, Contacts, Talk.",
                    ),
                    (
                        "03",
                        "Usuários",
                        "Criação de usuários e grupos, ou integração com LDAP/Active Directory.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação para uso do cliente desktop/mobile e entrega de documentação.",
                    ),
                ],
                "faqs": [
                    (
                        "Nextcloud é gratuito?",
                        "Sim — a versão community é open-source e gratuita. Nextcloud Enterprise tem suporte pago opcional.",
                    ),
                    (
                        "Funciona como Google Drive?",
                        "Sim — sincronização de arquivos via cliente desktop e mobile, com edição colaborativa de documentos Office.",
                    ),
                    (
                        "Integra com Active Directory?",
                        "Sim, via LDAP. Usuários do AD acessam o Nextcloud com as mesmas credenciais de domínio.",
                    ),
                    (
                        "Tem aplicativo mobile?",
                        "Sim — apps oficiais para iOS e Android com sincronização automática de fotos.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Arquivos",
                        [
                            "Sincronização desktop (Windows/Mac/Linux)",
                            "App mobile (iOS/Android)",
                            "Compartilhamento com link externo",
                            "Versão de arquivos com histórico",
                        ],
                    ),
                    (
                        "Colaboração",
                        [
                            "Edição de documentos Office (Collabora Online)",
                            "Calendário e contatos compartilhados",
                            "Videochamada integrada (Talk)",
                            "Quadro Kanban (Deck)",
                        ],
                    ),
                    (
                        "Segurança",
                        [
                            "Criptografia de arquivos em repouso",
                            "2FA com TOTP",
                            "Auditoria de acessos",
                            "Scansão de antivírus (ClamAV)",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do Nextcloud com SSL e domínio próprio",
                    "Configuração de apps essenciais e integrações",
                    "Integração LDAP/AD se necessário",
                    "Treinamento dos usuários e documentação",
                ],
                "client_does": [
                    "Fornecer VPS com Ubuntu 22.04 (mínimo 2 vCPU, 4 GB RAM, storage para arquivos)",
                    "Definir grupos de usuários e política de compartilhamento",
                    "Gerenciar usuários e storage após a entrega",
                ],
            },
            # ── AAPanel ─────────────────────────────────────────────────
            {
                "slug": "aapanel",
                "tagline": "Painel web para hospedagem de sites na sua VPS",
                "description": (
                    "Implantamos o AAPanel (aaPanel) na sua VPS: hospedagem de múltiplos sites "
                    "com Nginx, PHP multi-versão, MySQL/PostgreSQL, SSL automático via Let's "
                    "Encrypt e backups agendados — sem custo de licença."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Instalação do AAPanel com stack LEMP (Nginx + PHP + MySQL) ou LAMP.",
                    ),
                    (
                        "02",
                        "Sites",
                        "Criação dos sites, configuração de domínios, SSL e versão de PHP por site.",
                    ),
                    (
                        "03",
                        "Banco de dados",
                        "Criação de bancos MySQL/PostgreSQL e usuários de acesso por site.",
                    ),
                    (
                        "04",
                        "Backup",
                        "Configuração de backup automático local e/ou para armazenamento externo.",
                    ),
                ],
                "faqs": [
                    (
                        "AAPanel é gratuito?",
                        "Sim — a versão community é gratuita. Há plugins pagos opcionais para otimização e segurança.",
                    ),
                    (
                        "Posso hospedar WordPress?",
                        "Sim — AAPanel tem instalador 1-click para WordPress, com PHP, MySQL e SSL configurados automaticamente.",
                    ),
                    (
                        "Suporta múltiplos sites?",
                        "Sim — você pode hospedar quantos sites quiser, com domínios, SSL e PHP independentes por site.",
                    ),
                    (
                        "Tem FTP?",
                        "Sim — AAPanel inclui servidor FTP (Pure-FTPd) com usuários individuais por site.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Hospedagem",
                        [
                            "Nginx ou Apache com configuração por site",
                            "PHP 7.4 a 8.3 com troca por site",
                            "SSL automático via Let's Encrypt",
                            "Domínios e subdomínios ilimitados",
                        ],
                    ),
                    (
                        "Banco de dados",
                        [
                            "MySQL 5.7/8.0 e MariaDB",
                            "PostgreSQL",
                            "phpMyAdmin integrado",
                            "Backup agendado por banco",
                        ],
                    ),
                    (
                        "Gestão",
                        [
                            "Gerenciador de arquivos web",
                            "Monitor de recursos em tempo real",
                            "Log de acesso e erro por site",
                            "Cron jobs via interface web",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do AAPanel com stack LEMP ou LAMP",
                    "Configuração dos sites, domínios e SSL",
                    "Configuração de backup automático",
                    "Treinamento e documentação",
                ],
                "client_does": [
                    "Fornecer VPS com Ubuntu 22.04 (mínimo 1 vCPU, 2 GB RAM)",
                    "Fornecer domínios com DNS apontando para o servidor",
                    "Gerenciar sites e usuários FTP após a entrega",
                ],
            },
            # ── RustDesk ────────────────────────────────────────────────
            {
                "slug": "rustdesk",
                "tagline": "Acesso remoto self-hosted — alternativa ao TeamViewer sem custo",
                "description": (
                    "Implantamos o RustDesk Server na sua VPS: acesso remoto criptografado "
                    "ponta a ponta para toda a equipe de TI, sem custo por dispositivo, "
                    "sem dados em servidores de terceiros."
                ),
                "steps": [
                    (
                        "01",
                        "Servidor",
                        "Instalação do hbbs e hbbr via Docker com chaves criptográficas próprias.",
                    ),
                    (
                        "02",
                        "SSL e domínio",
                        "Configuração de HTTPS e domínio para o servidor relay.",
                    ),
                    (
                        "03",
                        "Clientes",
                        "Build ou configuração do cliente RustDesk com servidor pré-configurado.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe de TI e documentação de operação.",
                    ),
                ],
                "faqs": [
                    (
                        "RustDesk é gratuito?",
                        "O servidor open-source é gratuito. RustDesk Server Pro (com painel web) tem licença paga opcional.",
                    ),
                    (
                        "É seguro?",
                        "Sim — criptografia ponta a ponta com Curve25519 + AES-256-GCM. A chave privada fica só na sua VPS.",
                    ),
                    (
                        "Funciona em mobile?",
                        "Sim — apps iOS e Android para controle remoto e visualização de tela.",
                    ),
                    (
                        "Posso ter acesso não supervisionado?",
                        "Sim — configure uma senha permanente por dispositivo para acesso sem aprovação do usuário.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Conectividade",
                        [
                            "Acesso remoto via relay próprio",
                            "P2P direto quando na mesma rede",
                            "Sem limite de dispositivos",
                            "Multi-monitor",
                        ],
                    ),
                    (
                        "Segurança",
                        [
                            "Criptografia E2E Curve25519 + AES-256",
                            "Chave privada na sua VPS",
                            "Acesso supervisionado e não supervisionado",
                            "Log de sessões",
                        ],
                    ),
                    (
                        "Compatibilidade",
                        [
                            "Windows 7+",
                            "macOS 10.14+",
                            "Linux (Ubuntu, Debian, CentOS)",
                            "iOS e Android",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do servidor RustDesk via Docker",
                    "Configuração de SSL e domínio próprio",
                    "Build de cliente customizado com servidor pré-configurado",
                    "Treinamento e documentação",
                ],
                "client_does": [
                    "Fornecer VPS (mínimo 1 vCPU, 1 GB RAM) com portas 21115 a 21119 abertas",
                    "Distribuir o cliente RustDesk para os computadores da equipe",
                    "Gerenciar senhas de acesso por dispositivo",
                ],
            },
            # ── Windows Server ───────────────────────────────────────────
            {
                "slug": "windows-server",
                "tagline": "Active Directory, GPOs e servidor de arquivos Microsoft",
                "description": (
                    "Implantamos e gerenciamos o Windows Server: Active Directory com estrutura "
                    "de UOs e GPOs, servidor de arquivos NTFS, DNS, DHCP e integração com "
                    "Microsoft 365 / Entra ID."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Instalação do Windows Server 2019/2022 e promoção do Domain Controller.",
                    ),
                    (
                        "02",
                        "Active Directory",
                        "Estrutura de UOs, grupos de segurança, delegação e políticas de senha.",
                    ),
                    (
                        "03",
                        "GPOs e File Server",
                        "Políticas de grupo, mapeamento de drives, servidor de arquivos NTFS e quotas.",
                    ),
                    (
                        "04",
                        "Integração M365",
                        "Configuração do Entra Connect para SSO com Microsoft 365.",
                    ),
                ],
                "faqs": [
                    (
                        "Preciso comprar licença?",
                        "Sim — licença Windows Server é responsabilidade do cliente (SPLA, OEM ou retail).",
                    ),
                    (
                        "Suporta Microsoft 365?",
                        "Sim — configuramos Entra Connect para sincronização com M365/Entra ID.",
                    ),
                    (
                        "E se o servidor cair?",
                        "Recomendamos dois Domain Controllers para HA. Com dois DCs, autenticação continua mesmo com um fora.",
                    ),
                    (
                        "Posso ter acesso remoto?",
                        "Sim — RDS (Remote Desktop Services) ou VPN site-to-site conforme a necessidade.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Identidade",
                        [
                            "Active Directory Domain Services",
                            "Grupos de segurança e UOs",
                            "GPOs por departamento",
                            "Entra Connect para M365",
                        ],
                    ),
                    (
                        "Servidor de arquivos",
                        [
                            "Compartilhamentos NTFS por grupo",
                            "Quotas de disco por usuário",
                            "Shadow Copies (versões anteriores)",
                            "Auditoria de acessos",
                        ],
                    ),
                    (
                        "Rede",
                        [
                            "DNS interno e resolução de nomes",
                            "DHCP com reservas por MAC",
                            "WSUS para patches centralizados",
                            "Integração com VPN",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Windows Server",
                    "Promoção do Domain Controller e AD DS",
                    "Configuração de GPOs, servidor de arquivos e backup",
                    "Integração com Microsoft 365 e treinamento",
                ],
                "client_does": [
                    "Fornecer licença Windows Server e CALs necessárias",
                    "Definir estrutura de UOs, grupos e permissões",
                    "Gerenciar criação e desativação de contas de usuário",
                ],
            },
            # ── Samba ───────────────────────────────────────────────────
            {
                "slug": "samba",
                "tagline": "Servidor de arquivos Linux com SMB/CIFS nativo para Windows",
                "description": (
                    "Implantamos o Samba em Linux: compartilhamento de arquivos via SMB/CIFS "
                    "compatível nativamente com Windows, macOS e Linux — sem custo de licença "
                    "de sistema operacional, com permissões POSIX + ACL e integração com AD."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Instalação do Samba em Linux com configuração inicial de shares.",
                    ),
                    (
                        "02",
                        "Permissões",
                        "Configuração de ACLs POSIX por usuário e grupo, quotas e auditoria.",
                    ),
                    (
                        "03",
                        "Autenticação",
                        "Integração com Active Directory ou usuários locais Samba.",
                    ),
                    (
                        "04",
                        "Backup",
                        "Configuração de backup via Rsync para site secundário ou NAS.",
                    ),
                ],
                "faqs": [
                    (
                        "Windows acessa sem instalar nada?",
                        "Sim — Samba fala SMB/CIFS nativo. O usuário mapeia o drive de rede sem software adicional.",
                    ),
                    (
                        "Integra com Active Directory?",
                        "Sim — Samba como domain member sincroniza usuários e grupos do AD Windows.",
                    ),
                    (
                        "Qual a diferença para Windows File Server?",
                        "Funcionalidade similar, mas sem custo de licença de SO. Ideal para empresas que já têm Linux ou querem economizar em licenças.",
                    ),
                    (
                        "Suporta quotas?",
                        "Sim — quotas de disco por usuário ou share com alertas automáticos quando o limite é atingido.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Compartilhamento",
                        [
                            "SMB/CIFS nativo para Windows",
                            "NFS para Linux/macOS",
                            "Múltiplos shares por departamento",
                            "Criptografia SMB3",
                        ],
                    ),
                    (
                        "Controle de acesso",
                        [
                            "Permissões POSIX + ACL estendidas",
                            "Integração LDAP/AD",
                            "Quotas por usuário ou share",
                            "Auditoria de acesso a arquivos",
                        ],
                    ),
                    (
                        "Resiliência",
                        [
                            "Backup via Rsync agendado",
                            "Monitoramento de capacidade via Zabbix",
                            "Snapshots via LVM ou Btrfs",
                            "Alta disponibilidade com Pacemaker/Corosync",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do Samba em servidor Linux",
                    "Configuração de shares, permissões e autenticação",
                    "Integração com Active Directory se necessário",
                    "Backup e documentação operacional",
                ],
                "client_does": [
                    "Fornecer servidor Linux (Ubuntu 22.04 LTS recomendado)",
                    "Definir estrutura de shares e permissões por equipe",
                    "Gerenciar usuários e quotas após a entrega",
                ],
            },
            # ── Redes Corporativas ───────────────────────────────────────
            {
                "slug": "redes",
                "tagline": "Projeto e implantação de rede corporativa com VLAN e firewall",
                "description": (
                    "Projetamos e implantamos a rede corporativa da sua empresa: switching "
                    "gerenciável, VLANs por departamento, roteamento, firewall e VPN — "
                    "desde o cabeamento até a configuração dos equipamentos ativos."
                ),
                "steps": [
                    (
                        "01",
                        "Levantamento",
                        "Mapeamento da planta física, número de usuários, demandas por departamento e equipamentos existentes.",
                    ),
                    (
                        "02",
                        "Projeto",
                        "Diagrama lógico com VLANs, endereçamento IP, política de firewall e topologia de rede.",
                    ),
                    (
                        "03",
                        "Implantação",
                        "Configuração de switches, roteador, firewall e access points conforme o projeto.",
                    ),
                    (
                        "04",
                        "Testes e entrega",
                        "Certificação da conectividade, teste de segmentação e entrega da documentação da rede.",
                    ),
                ],
                "faqs": [
                    (
                        "Por que usar VLANs?",
                        "VLANs segmentam a rede por departamento — financeiro, operação, convidados — isolando o tráfego e aumentando a segurança.",
                    ),
                    (
                        "Quais equipamentos são suportados?",
                        "Trabalhamos com Cisco, MikroTik, Ubiquiti, Intelbras e outros. A marca é definida conforme o orçamento e escala.",
                    ),
                    (
                        "Inclui Wi-Fi?",
                        "Sim — podemos projetar e implantar a rede Wi-Fi corporativa com SSIDs por VLAN e cobertura de todo o espaço físico.",
                    ),
                    (
                        "Tem monitoramento?",
                        "Sim — integramos com Zabbix para monitoramento de disponibilidade e desempenho dos equipamentos de rede.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Switching e roteamento",
                        [
                            "Switches gerenciáveis com 802.1Q (VLAN)",
                            "Roteamento inter-VLAN",
                            "Spanning Tree Protocol (STP)",
                            "Link aggregation (LACP)",
                        ],
                    ),
                    (
                        "Segurança",
                        [
                            "Firewall stateful com regras por VLAN",
                            "VPN site-to-site (IPsec/OpenVPN)",
                            "Port security e 802.1X",
                            "IDS/IPS integrado",
                        ],
                    ),
                    (
                        "Wi-Fi",
                        [
                            "Access points dual-band (2.4/5 GHz)",
                            "SSIDs por VLAN (funcionários, convidados)",
                            "Controle de acesso por MAC",
                            "Heatmap de cobertura",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Levantamento de requisitos e projeto da rede",
                    "Configuração de switches, roteador e firewall",
                    "Implantação de Wi-Fi e VPN",
                    "Documentação e treinamento da equipe de TI",
                ],
                "client_does": [
                    "Fornecer acesso físico ao ambiente para instalação",
                    "Definir segmentação por departamento e políticas de acesso",
                    "Adquirir os equipamentos indicados pela PaperMoon",
                ],
            },
            # ── Cabeamento ──────────────────────────────────────────────
            {
                "slug": "cabeamento",
                "tagline": "Cabeamento estruturado Cat6 e fibra conforme ABNT NBR 14565",
                "description": (
                    "Instalamos cabeamento estruturado Cat5e, Cat6 e Cat6A para dados, "
                    "e fibra óptica monomodo e multimodo para backbone — projeto, execução, "
                    "certificação e organização de rack conforme normas ABNT."
                ),
                "steps": [
                    (
                        "01",
                        "Projeto",
                        "Levantamento da planta, posições de pontos de rede, trajeto de eletrocalha e especificação de materiais.",
                    ),
                    (
                        "02",
                        "Instalação",
                        "Passagem de cabos, terminação em patch panels e tomadas, organização de rack.",
                    ),
                    (
                        "03",
                        "Certificação",
                        "Teste e certificação de todos os links com equipamento profissional (Fluke ou Softing).",
                    ),
                    (
                        "04",
                        "Documentação",
                        "Planta atualizada, etiquetagem dos pontos e relatório de certificação.",
                    ),
                ],
                "faqs": [
                    (
                        "Cat6 ou Cat6A?",
                        "Cat6 atende até 10 Gbps em até 55m. Cat6A atende 10 Gbps até 100m. Para novos projetos, recomendamos Cat6A.",
                    ),
                    (
                        "Fibra óptica é necessária?",
                        "Para backbone (entre andares ou prédios) e distâncias acima de 100m, fibra é obrigatória para garantir desempenho.",
                    ),
                    (
                        "Emite laudo de certificação?",
                        "Sim — cada link é certificado e gera relatório com comprimento, perda e atenuação. Entregamos o relatório completo.",
                    ),
                    (
                        "Como o cronograma é definido?",
                        "O cronograma depende do número de pontos, da infraestrutura existente e das janelas de execução disponíveis. A PaperMoon detalha esse planejamento antes do início do serviço.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Cabeamento de dados",
                        [
                            "Cat5e, Cat6 e Cat6A certificados",
                            "Fibra óptica monomodo e multimodo",
                            "Terminação em patch panel e keystones",
                            "Etiquetagem ABNT NBR 14565",
                        ],
                    ),
                    (
                        "Infraestrutura",
                        [
                            "Eletrocalhas e canaletas organizadas",
                            "Rack fechado ou aberto com patch panel 1U/2U",
                            "Gerenciamento de cabos com velcro e patch cords coloridos",
                            "Aterramento do rack",
                        ],
                    ),
                    (
                        "Certificação",
                        [
                            "Teste de todos os links com equipamento calibrado",
                            "Relatório de certificação por ponto",
                            "Verificação de mapa de pinos (wiring map)",
                            "Garantia de conformidade com normas",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Projeto e execução do cabeamento estruturado",
                    "Terminação em patch panel e organização de rack",
                    "Certificação de todos os links",
                    "Documentação completa e etiquetagem",
                ],
                "client_does": [
                    "Fornecer acesso físico ao ambiente durante a instalação",
                    "Aprovar o projeto antes da execução",
                    "Adquirir materiais se não incluídos no contrato",
                ],
            },
            # ── Manutenção ──────────────────────────────────────────────
            {
                "slug": "manutencao",
                "tagline": "Manutenção preventiva e corretiva de servidores e workstations",
                "description": (
                    "Realizamos manutenção preventiva e corretiva em servidores físicos e "
                    "workstations: diagnóstico completo, limpeza, substituição de componentes, "
                    "upgrade de hardware e relatório técnico com recomendações."
                ),
                "steps": [
                    (
                        "01",
                        "Diagnóstico",
                        "Análise de hardware: temperatura, S.M.A.R.T. dos discos, memória, fontes e logs de eventos.",
                    ),
                    (
                        "02",
                        "Limpeza",
                        "Limpeza interna com ar comprimido, troca de pasta térmica e verificação de cabos.",
                    ),
                    (
                        "03",
                        "Substituição",
                        "Substituição dos componentes com defeito ou desgastados por peças homologadas.",
                    ),
                    (
                        "04",
                        "Relatório",
                        "Entrega de relatório técnico com diagnóstico, ações realizadas e recomendações futuras.",
                    ),
                ],
                "faqs": [
                    (
                        "Com que frequência fazer manutenção preventiva?",
                        "Recomendamos manutenção preventiva semestral para servidores em produção e anual para workstations.",
                    ),
                    (
                        "Fazem upgrade de hardware?",
                        "Sim — RAM, SSD/HDD, placas de rede e fontes. Realizamos análise de compatibilidade antes da compra.",
                    ),
                    (
                        "Atendem in loco?",
                        "Sim — o serviço é realizado presencialmente no ambiente do cliente.",
                    ),
                    (
                        "O servidor precisa ser desligado?",
                        "Para limpeza e substituição de componentes não hot-swap, sim. Agendamos com antecedência para minimizar o impacto.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Diagnóstico",
                        [
                            "Análise S.M.A.R.T. de discos",
                            "Teste de memória (MemTest86)",
                            "Temperatura e voltagem de componentes",
                            "Logs de eventos do sistema",
                        ],
                    ),
                    (
                        "Manutenção",
                        [
                            "Limpeza interna com ar comprimido",
                            "Troca de pasta térmica processador/GPU",
                            "Verificação e reaperto de conectores",
                            "Substituição de baterias de BIOS/CMOS",
                        ],
                    ),
                    (
                        "Upgrade",
                        [
                            "Expansão de memória RAM",
                            "Substituição de HDD por SSD NVMe",
                            "Adição de placa de rede ou RAID controller",
                            "Upgrade de fonte de alimentação",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Diagnóstico completo de hardware",
                    "Manutenção preventiva e corretiva",
                    "Substituição e upgrade de componentes",
                    "Relatório técnico com recomendações",
                ],
                "client_does": [
                    "Agendar janela de manutenção com antecedência",
                    "Garantir backup dos dados antes da manutenção",
                    "Fornecer acesso físico ao equipamento",
                ],
            },
            # ── Backup Corporativo ───────────────────────────────────────
            {
                "slug": "backup",
                "tagline": "Política de backup e recuperação de desastres para sua empresa",
                "description": (
                    "Implementamos política de backup 3-2-1: 3 cópias, 2 mídias diferentes, "
                    "1 offsite — com testes periódicos de restauração, documentação do DRP "
                    "e alertas automáticos de falha."
                ),
                "steps": [
                    (
                        "01",
                        "Mapeamento",
                        "Identificação dos dados críticos, sistemas a proteger, RTO e RPO desejados.",
                    ),
                    (
                        "02",
                        "Implantação",
                        "Configuração das ferramentas de backup (Veeam, Restic, Proxmox Backup Server ou Rsync).",
                    ),
                    (
                        "03",
                        "Testes",
                        "Simulação de restauração para validar a integridade e o tempo de recuperação.",
                    ),
                    (
                        "04",
                        "Documentação",
                        "Entrega do DRP documentado com procedimentos de restauração passo a passo.",
                    ),
                ],
                "faqs": [
                    (
                        "O que é a regra 3-2-1?",
                        "3 cópias dos dados, em 2 tipos de mídia diferentes (ex: disco local + nuvem), com 1 cópia offsite (fora do local físico).",
                    ),
                    (
                        "Qual ferramenta é usada?",
                        "Depende do ambiente: Veeam para Windows/VMware, Proxmox Backup Server para VMs Proxmox, Restic ou Rsync para Linux em geral.",
                    ),
                    (
                        "Com que frequência é feito o backup?",
                        "Configuramos de acordo com o RPO desejado — pode ser contínuo, por hora, diário ou semanal por tipo de dado.",
                    ),
                    (
                        "Como sei que o backup funcionou?",
                        "Configuramos alertas por e-mail ou Telegram para sucesso e falha. Realizamos testes de restauração periódicos.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Estratégia",
                        [
                            "Política 3-2-1 (local + offsite)",
                            "RTO e RPO definidos por sistema",
                            "Retenção configurável por dado",
                            "Versionamento de backups",
                        ],
                    ),
                    (
                        "Ferramentas",
                        [
                            "Proxmox Backup Server para VMs",
                            "Restic para servidores Linux",
                            "Veeam para ambientes Windows/VMware",
                            "Rsync para dados de arquivos",
                        ],
                    ),
                    (
                        "Monitoramento",
                        [
                            "Alertas de falha por e-mail ou Telegram",
                            "Relatório mensal de execução",
                            "Testes de restauração agendados",
                            "Dashboard de status dos jobs",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Mapeamento dos dados críticos e definição do DRP",
                    "Implantação e configuração das ferramentas de backup",
                    "Testes de restauração e validação",
                    "Documentação do DRP e treinamento",
                ],
                "client_does": [
                    "Definir RTO e RPO aceitáveis por sistema",
                    "Fornecer destino offsite (S3, NAS externo ou cloud)",
                    "Revisar e aprovar o DRP antes da assinatura",
                ],
            },
            # ── Plone ───────────────────────────────────────────────────
            {
                "slug": "plone",
                "tagline": "Portal corporativo e intranet com controle total dos seus dados",
                "description": (
                    "Implantamos o Plone 6 na sua infraestrutura: portal corporativo ou intranet "
                    "com gestão documental, workflow de publicação, controle de acesso granular "
                    "por papel e integração com LDAP/Active Directory."
                ),
                "steps": [
                    (
                        "01",
                        "Arquitetura",
                        "Mapeamento de tipos de conteúdo, hierarquia de seções, papéis e fluxo de aprovação.",
                    ),
                    (
                        "02",
                        "Instalação",
                        "Deploy do Plone 6 com PostgreSQL, proxy Nginx e SSL. O ambiente é preparado conforme a arquitetura de conteúdo e as integrações definidas para o projeto.",
                    ),
                    (
                        "03",
                        "Tema e conteúdo",
                        "Aplicação do tema com identidade visual da empresa e configuração dos tipos de conteúdo.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe editorial e entrega de documentação de operação.",
                    ),
                ],
                "faqs": [
                    (
                        "Para que serve o Plone?",
                        "Intranet corporativa, portal de documentos, base de conhecimento e sites institucionais com controle de acesso rigoroso.",
                    ),
                    (
                        "Plone é difícil de usar?",
                        "O painel editorial é intuitivo para publicar conteúdo. A PaperMoon treina a equipe e entrega documentação operacional.",
                    ),
                    (
                        "Integra com Active Directory?",
                        "Sim — autenticação federada via LDAP com sincronização de usuários e grupos do AD.",
                    ),
                    (
                        "Qual o custo de licença?",
                        "Zero — Plone é open-source. O cliente paga apenas o servidor.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Conteúdo",
                        [
                            "Versionamento com histórico e rollback",
                            "Workflow de publicação customizável",
                            "Agendamento de publicação e expiração",
                            "Editor rich-text e suporte a Markdown",
                        ],
                    ),
                    (
                        "Acesso",
                        [
                            "Papéis granulares por seção",
                            "Integração LDAP/AD",
                            "SSO via SAML ou OAuth2",
                            "Auditoria de alterações",
                        ],
                    ),
                    (
                        "Infraestrutura",
                        [
                            "100% self-hosted",
                            "Backup automático do ZODB",
                            "Cache Varnish para alta performance",
                            "Docker Compose para deploys reproduzíveis",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Plone 6",
                    "Tema com identidade visual da empresa",
                    "Integração LDAP/AD e configuração de workflows",
                    "Treinamento e documentação operacional",
                ],
                "client_does": [
                    "Definir estrutura de seções e tipos de conteúdo",
                    "Fornecer identidade visual (cores, logo, tipografia)",
                    "Gerenciar conteúdo e usuários após a entrega",
                ],
            },
            # ── Keycloak ────────────────────────────────────────────────
            {
                "slug": "keycloak",
                "tagline": "Login único para todos os sistemas com segurança enterprise",
                "description": (
                    "Centralizamos a autenticação de todas as aplicações em um Keycloak "
                    "self-hosted: SSO, MFA, OAuth2/OIDC, SAML 2.0 e integração com Active "
                    "Directory — sem dependência de provedores externos."
                ),
                "steps": [
                    (
                        "01",
                        "Mapeamento",
                        "Levantamento das aplicações a integrar, grupos de usuário e políticas de acesso.",
                    ),
                    (
                        "02",
                        "Instalação",
                        "Deploy do Keycloak com PostgreSQL, proxy Nginx, SSL e integração LDAP/AD.",
                    ),
                    (
                        "03",
                        "Integração",
                        "Configuração de cada aplicação como cliente OAuth2/OIDC ou SAML no Keycloak.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe de TI na gestão de usuários e documentação operacional.",
                    ),
                ],
                "faqs": [
                    (
                        "Quais aplicações integram?",
                        "Qualquer app com OAuth2, OIDC ou SAML: Nextcloud, GLPI, Zabbix, N8N, Grafana, WordPress e outras.",
                    ),
                    (
                        "Keycloak é difícil de manter?",
                        "Operações do dia a dia (usuários, senhas, bloqueios) são simples no console web. A PaperMoon treina a equipe.",
                    ),
                    (
                        "Posso manter o AD e usar Keycloak?",
                        "Sim — o AD continua sendo fonte de identidade para estações Windows. Keycloak centraliza o SSO das apps web.",
                    ),
                    (
                        "Qual o custo de licença?",
                        "Zero — Keycloak é open-source. O cliente paga apenas o servidor.",
                    ),
                ],
                "feature_groups": [
                    (
                        "SSO",
                        [
                            "Login único para todas as apps integradas",
                            "Single Logout em todas as apps",
                            "OAuth2, OIDC e SAML 2.0",
                            "Social login (Google, Microsoft, GitHub)",
                        ],
                    ),
                    (
                        "Segurança",
                        [
                            "MFA com TOTP (Google Authenticator)",
                            "Política de senha e bloqueio de conta",
                            "Detecção de força bruta",
                            "Auditoria de login completa",
                        ],
                    ),
                    (
                        "Identidade",
                        [
                            "Sincronização com LDAP/AD",
                            "Self-service de senha",
                            "Convite por e-mail",
                            "Grupos e papéis automáticos por regras LDAP",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Keycloak",
                    "Integração LDAP/AD e configuração de MFA",
                    "Integração de todas as aplicações solicitadas",
                    "Treinamento da equipe de TI e documentação",
                ],
                "client_does": [
                    "Mapear as aplicações a integrar com SSO",
                    "Definir políticas de senha e MFA por grupo",
                    "Gerenciar usuários e grupos no Keycloak após entrega",
                ],
            },
            # ── Tailscale ────────────────────────────────────────────────
            {
                "slug": "tailscale",
                "tagline": "Rede privada mesh com acesso remoto seguro e sem abrir portas",
                "description": (
                    "Implantamos o Tailscale para conectar notebooks, servidores e filiais "
                    "em uma rede privada WireGuard com autenticação por identidade, ACLs "
                    "granulares e acesso remoto simples de operar."
                ),
                "steps": [
                    (
                        "01",
                        "Mapeamento",
                        "Levantamento dos usuários, dispositivos, servidores e redes locais que participarão da tailnet.",
                    ),
                    (
                        "02",
                        "Implantação",
                        "Instalação do Tailscale nos dispositivos necessários e conexão com o provedor de identidade da empresa.",
                    ),
                    (
                        "03",
                        "Políticas",
                        "Definição de ACLs, tags, grupos e publicação de sub-redes via subnet routers.",
                    ),
                    (
                        "04",
                        "Validação",
                        "Teste do acesso remoto em produção, documentação operacional e treinamento da equipe.",
                    ),
                ],
                "faqs": [
                    (
                        "Precisa abrir portas no firewall?",
                        "Na maioria dos cenários, não. O Tailscale usa NAT traversal e, quando necessário, relays DERP sem expor seus serviços diretamente na internet.",
                    ),
                    (
                        "Substitui VPN tradicional?",
                        "Em muitos casos, sim. Ele entrega acesso remoto privado com muito menos complexidade operacional que OpenVPN ou IPsec.",
                    ),
                    (
                        "Consigo acessar uma rede inteira sem instalar em todos os equipamentos?",
                        "Sim — com subnet routers, publicamos redes locais inteiras dentro da tailnet para dispositivos autorizados.",
                    ),
                    (
                        "Funciona com SSO corporativo?",
                        "Sim. O Tailscale integra com Google, Microsoft e outros provedores para centralizar autenticação e revogação de acesso.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Acesso remoto",
                        [
                            "Rede privada mesh entre notebooks, servidores e clouds",
                            "Baseado em WireGuard com alta performance",
                            "Sem expor RDP, SSH ou painéis na internet",
                            "Clientes para Windows, macOS, Linux, iOS e Android",
                        ],
                    ),
                    (
                        "Governança",
                        [
                            "ACLs por usuário, grupo, tag e serviço",
                            "Integração com SSO corporativo",
                            "Revogação central de acesso",
                            "Visibilidade dos dispositivos conectados",
                        ],
                    ),
                    (
                        "Redes",
                        [
                            "Subnet routers para redes locais",
                            "Exit nodes para saída controlada",
                            "Conexão segura entre matriz, filial e home office",
                            "Compartilhamento controlado com terceiros",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Desenho da topologia da tailnet",
                    "Instalação do Tailscale nos dispositivos e servidores",
                    "Configuração de SSO, ACLs, tags e subnet routers",
                    "Documentação operacional e treinamento da equipe",
                ],
                "client_does": [
                    "Definir usuários, dispositivos e redes autorizadas",
                    "Aprovar políticas de acesso entre times e fornecedores",
                    "Fornecer acesso administrativo aos equipamentos a integrar",
                ],
            },
            # ── Twenty CRM ──────────────────────────────────────────────
            {
                "slug": "twenty-crm",
                "tagline": "CRM open-source self-hosted — alternativa ao Salesforce",
                "description": (
                    "Implantamos o Twenty CRM na sua infraestrutura: pipeline de vendas, "
                    "gestão de contatos e empresas, integração de e-mail e webhooks para "
                    "automação — sem custo por usuário e com seus dados no seu servidor."
                ),
                "steps": [
                    (
                        "01",
                        "Mapeamento",
                        "Levantamento das etapas do pipeline, campos customizados e fluxo de atividades.",
                    ),
                    (
                        "02",
                        "Instalação",
                        "Deploy do Twenty via Docker Compose com PostgreSQL, Redis e SSL.",
                    ),
                    (
                        "03",
                        "Customização",
                        "Configuração de pipelines, campos e migração de dados do CRM anterior.",
                    ),
                    (
                        "04",
                        "Treinamento",
                        "Capacitação da equipe comercial e documentação operacional.",
                    ),
                ],
                "faqs": [
                    (
                        "Para que tamanho de empresa?",
                        "Ideal para startups e PMEs de até ~200 pessoas saindo de planilhas ou querendo substituir HubSpot/Pipedrive.",
                    ),
                    (
                        "Posso migrar do HubSpot ou Pipedrive?",
                        "Sim — a PaperMoon cuida da migração via CSV ou API como parte da entrega.",
                    ),
                    (
                        "Tem app mobile?",
                        "Interface web responsiva funciona bem em mobile. App nativo iOS/Android está no roadmap do projeto.",
                    ),
                    (
                        "Qual o custo de licença?",
                        "Zero — Twenty é open-source (AGPL). O cliente paga apenas o servidor.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Pipeline",
                        [
                            "Kanban de deals com drag-and-drop",
                            "Pipelines customizáveis por equipe",
                            "Campos personalizados por objeto",
                            "Filtros e visões salvas",
                        ],
                    ),
                    (
                        "Comunicação",
                        [
                            "Sincronização bidirecional de e-mails",
                            "Log de chamadas e reuniões",
                            "Notas com menção de membros",
                            "Timeline completa por contato",
                        ],
                    ),
                    (
                        "Integração",
                        [
                            "API GraphQL nativa",
                            "Importação via CSV de qualquer CRM",
                            "Webhooks para N8N ou Zapier",
                            "100% self-hosted",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Twenty CRM",
                    "Customização de campos e pipelines",
                    "Migração de dados do CRM anterior",
                    "Treinamento da equipe comercial",
                ],
                "client_does": [
                    "Definir etapas do pipeline e campos customizados",
                    "Fornecer exportação do CRM atual para migração",
                    "Gerenciar usuários e pipelines após a entrega",
                ],
            },
            # ── Papermark ───────────────────────────────────────────────
            {
                "slug": "papermark",
                "tagline": "Compartilhe propostas com rastreamento total — alternativa ao DocSend",
                "description": (
                    "Implantamos o Papermark self-hosted: envie documentos com link rastreável "
                    "e saiba quem abriu, por quanto tempo leu cada página e o que gerou mais "
                    "interesse — dados que ficam no seu servidor."
                ),
                "steps": [
                    (
                        "01",
                        "Instalação",
                        "Deploy do Papermark via Docker Compose com PostgreSQL e storage configurados.",
                    ),
                    (
                        "02",
                        "Storage",
                        "Configuração do armazenamento: S3 compatível (MinIO ou AWS) ou volume local.",
                    ),
                    (
                        "03",
                        "Domínio e e-mail",
                        "Configuração de domínio customizado para os links e e-mail transacional para notificações.",
                    ),
                    ("04", "Treinamento", "Capacitação da equipe e documentação de operação."),
                ],
                "faqs": [
                    (
                        "Diferença do DocSend?",
                        "DocSend é SaaS pago com dados nos servidores deles. Papermark self-hosted é open-source, sem licença, com documentos no seu servidor.",
                    ),
                    (
                        "Que formatos suporta?",
                        "PDF (com analytics por página), DOCX, PPTX e imagens. PDF é recomendado para melhores analytics.",
                    ),
                    (
                        "O destinatário precisa criar conta?",
                        "Não — abre o link diretamente no browser. Você pode pedir o e-mail dele antes de liberar o acesso.",
                    ),
                    (
                        "Qual o custo de licença?",
                        "Zero — Papermark é open-source. O cliente paga apenas servidor e storage.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Compartilhamento",
                        [
                            "Links únicos por destinatário",
                            "Proteção por e-mail verificado ou senha",
                            "Expiração por data ou número de views",
                            "Suporte a PDF, DOCX, PPTX",
                        ],
                    ),
                    (
                        "Analytics",
                        [
                            "Tempo de leitura por página",
                            "Total de views por link",
                            "Notificação em tempo real na abertura",
                            "Histórico de sessões por destinatário",
                        ],
                    ),
                    (
                        "Privacidade",
                        [
                            "100% self-hosted",
                            "Domínio customizado nos links",
                            "Sem limite de documentos ou views",
                            "Logs de acesso para auditoria",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação e configuração do Papermark",
                    "Configuração de storage, domínio e e-mail",
                    "Treinamento da equipe e documentação",
                ],
                "client_does": [
                    "Definir domínio customizado para os links",
                    "Fornecer credenciais de e-mail transacional",
                    "Gerenciar upload de documentos após a entrega",
                ],
            },
            # ── CrowdSec ────────────────────────────────────────────────
            {
                "slug": "crowdsec",
                "tagline": "Proteção automática contra ataques com inteligência colaborativa global",
                "description": (
                    "Implantamos o CrowdSec em toda a infraestrutura Linux: detecção "
                    "comportamental de ataques em tempo real, bloqueio automático via bouncers "
                    "e acesso à blocklist colaborativa de milhões de sensores globais."
                ),
                "steps": [
                    (
                        "01",
                        "Auditoria",
                        "Mapeamento dos servidores, serviços expostos e fontes de log disponíveis.",
                    ),
                    (
                        "02",
                        "Instalação",
                        "Instalação do agente e cenários de detecção em cada servidor.",
                    ),
                    (
                        "03",
                        "Bouncers",
                        "Configuração de bouncers: iptables, Nginx/Traefik ou Cloudflare.",
                    ),
                    (
                        "04",
                        "Dashboard",
                        "Configuração de métricas e alertas. Treinamento e documentação.",
                    ),
                ],
                "faqs": [
                    (
                        "Diferença do Fail2ban?",
                        "CrowdSec adiciona detecção comportamental mais sofisticada e inteligência coletiva global. IPs de atacantes já chegam bloqueados antes do primeiro ataque.",
                    ),
                    (
                        "Envia dados da minha rede?",
                        "Apenas IPs atacantes detectados (não conteúdo ou logs). Compartilhamento pode ser desativado.",
                    ),
                    (
                        "Substitui o firewall?",
                        "Não — é complementar. Firewall bloqueia portas; CrowdSec bloqueia IPs dinamicamente por comportamento.",
                    ),
                    (
                        "Funciona com Nginx e Traefik?",
                        "Sim — bouncers nativos para Nginx, Traefik, Caddy, Apache e Cloudflare.",
                    ),
                ],
                "feature_groups": [
                    (
                        "Detecção",
                        [
                            "Brute-force SSH, RDP e painéis web",
                            "Scan de portas e fingerprinting",
                            "Exploração de CVEs em tempo real",
                            "Flood HTTP (DDoS camada 7)",
                        ],
                    ),
                    (
                        "Bloqueio",
                        [
                            "Bloqueio via iptables/nftables",
                            "Bouncer Nginx/Traefik (retorno 403)",
                            "Integração Cloudflare",
                            "Decisões com tempo configurável",
                        ],
                    ),
                    (
                        "Inteligência",
                        [
                            "Blocklist colaborativa global (milhões de IPs)",
                            "Reputação de IP em tempo real",
                            "Listas de Tor, VPNs e hosting abusivo",
                            "API REST para consulta programática",
                        ],
                    ),
                ],
                "papermoon_does": [
                    "Instalação do agente em todos os servidores",
                    "Configuração de cenários e bouncers",
                    "Dashboard de métricas e alertas",
                    "Treinamento e documentação operacional",
                ],
                "client_does": [
                    "Fornecer acesso SSH aos servidores",
                    "Definir política de bloqueio e whitelist de IPs internos",
                    "Aprovar integração com a rede colaborativa CrowdSec",
                ],
            },
        ]

        created = 0
        for page_data in pages_data:
            try:
                product = Product.objects.get(slug=page_data["slug"])
            except Product.DoesNotExist:
                self.stdout.write(f"  · Produto '{page_data['slug']}' não encontrado — pulando CMS")
                continue

            page, _ = ServicePage.objects.get_or_create(product=product)
            page.tagline = page_data["tagline"]
            page.description = page_data["description"]
            page.save()

            # Steps
            ServiceStep.objects.filter(page=page).delete()
            for i, (num, title, desc) in enumerate(page_data["steps"], 1):
                ServiceStep.objects.create(
                    page=page, number=num, title=title, description=desc, order=i
                )

            # FAQs
            ServiceFAQ.objects.filter(page=page).delete()
            for i, (question, answer) in enumerate(page_data["faqs"], 1):
                ServiceFAQ.objects.create(page=page, question=question, answer=answer, order=i)

            # Feature groups
            ServiceFeatureGroup.objects.filter(page=page).delete()
            for gi, (group_title, items) in enumerate(page_data["feature_groups"], 1):
                group = ServiceFeatureGroup.objects.create(page=page, title=group_title, order=gi)
                for ii, item_text in enumerate(items, 1):
                    ServiceFeatureItem.objects.create(group=group, text=item_text, order=ii)

            # Responsibilities
            ServiceResponsibility.objects.filter(page=page).delete()
            for i, text in enumerate(page_data["papermoon_does"], 1):
                ServiceResponsibility.objects.create(page=page, side="papermoon", text=text, order=i)
            for i, text in enumerate(page_data["client_does"], 1):
                ServiceResponsibility.objects.create(page=page, side="client", text=text, order=i)

            created += 1

        if created:
            self.stdout.write(f"  ✓ {created} páginas CMS populadas")
        else:
            self.stdout.write("  · Páginas CMS já existem")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self, admin, customers, pending_users=None):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  CREDENCIAIS DE ACESSO (DESENVOLVIMENTO)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  {'Admin':<22} admin@papermoon.com  /  admin123")
        for c in customers:
            profile = c.profiles.select_related("user").filter(role="owner").first()
            if profile:
                self.stdout.write(
                    f"  {c.company_name[:22]:<22} {profile.user.email}  /  demo1234  [{c.status}]"
                )
        if pending_users:
            self.stdout.write("  — Pendentes (sem provisionar) —")
            for user, company in pending_users:
                self.stdout.write(f"  {company[:22]:<22} {user.email}  /  demo1234  [pending]")
        self.stdout.write("=" * 60)
        self.stdout.write("  API:    http://localhost:8000/api/v1/")
        self.stdout.write("  Docs:   http://localhost:8000/api/docs/")
        self.stdout.write("  Admin:  http://localhost:8000/admin/")
        self.stdout.write("  Front:  http://localhost:3000/")
        self.stdout.write("=" * 60 + "\n")
