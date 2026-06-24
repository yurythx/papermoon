import { http, HttpResponse } from "msw";

const ME_RESPONSE = {
  success: true,
  data: {
    user: { id: "u1", email: "owner@acme.com", username: "owner", is_staff: false },
    customer: {
      id: "c1",
      company_name: "Acme Ltda",
      document: "00.000.000/0001-00",
      status: "active",
      asaas_customer_id: "",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
    role: "owner",
  },
  error: null,
};

const CATALOG_RESPONSE = {
  success: true,
  data: [
    {
      id: "prod1",
      name: "Atendimento WhatsApp",
      slug: "atendimento-whatsapp",
      description: "Ideal para pequenas equipes",
      is_active: true,
      components: [{ id: "comp1", service_key: "n8n", config: {} }],
      pricings: [
        {
          id: "price1",
          billing_cycle: "monthly",
          amount: "199.00",
          trial_days: 14,
          is_active: true,
        },
        {
          id: "price2",
          billing_cycle: "annual",
          amount: "1990.00",
          trial_days: 0,
          is_active: true,
        },
      ],
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ],
  error: null,
};

const LICENSES_RESPONSE = {
  success: true,
  data: {
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: "lic1",
        key: "lic-abc123",
        status: "active",
        valid_from: "2024-01-01T00:00:00Z",
        valid_until: "2025-01-01T00:00:00Z",
        days_remaining: 90,
        product_name: "Atendimento WhatsApp",
        product_slug: "atendimento-whatsapp",
        subscription_id: "sub1",
        subscription_status: "active",
        billing_cycle: "monthly",
        amount: "199.00",
        services: [{ id: "sa1", service_key: "n8n", status: "active", external_id: "n8n-123", error: null }],
        created_at: "2024-01-01T00:00:00Z",
      },
    ],
  },
  error: null,
};

export const handlers = [
  // BFF auth
  http.post("/api/auth/login", () =>
    HttpResponse.json({ success: true, data: { message: "ok" }, error: null })
  ),

  http.post("/api/auth/password-reset", () =>
    HttpResponse.json({ success: true, data: { message: "Se o e-mail estiver cadastrado, você receberá um link em instantes." }, error: null })
  ),

  http.post("/api/auth/password-reset/confirm", () =>
    HttpResponse.json({ success: true, data: { message: "Senha redefinida com sucesso." }, error: null })
  ),

  http.post("/api/auth/logout", () =>
    HttpResponse.json({ success: true, data: { message: "ok" }, error: null })
  ),

  http.get("/api/auth/me", () => HttpResponse.json(ME_RESPONSE)),

  // BFF proxy → catalog (public, no auth needed in tests)
  http.get("/api/proxy/products/catalog/", () => HttpResponse.json(CATALOG_RESPONSE)),

  // BFF proxy → client data
  http.get("/api/proxy/client/me/", () =>
    HttpResponse.json({ success: true, data: ME_RESPONSE.data.customer, error: null })
  ),

  http.get("/api/proxy/client/licenses/", () => HttpResponse.json(LICENSES_RESPONSE)),

  http.get("/api/proxy/client/licenses/:id/", ({ params }) => {
    const license = LICENSES_RESPONSE.data.results.find((l) => l.id === params.id);
    if (!license) return HttpResponse.json({ success: false, data: null, error: { code: "not_found", message: "Not found", details: [] } }, { status: 404 });
    return HttpResponse.json({ success: true, data: license, error: null });
  }),

  http.get("/api/proxy/client/subscriptions/", () =>
    HttpResponse.json({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: "sub1",
            status: "active",
            starts_at: "2024-01-01T00:00:00Z",
            expires_at: "2024-12-31T00:00:00Z",
            created_at: "2024-01-01T00:00:00Z",
            product_name: "Atendimento WhatsApp",
            product_slug: "atendimento-whatsapp",
            billing_cycle: "monthly",
            amount: "199.00",
            license: {
              id: "lic1",
              key: "lic-abc123",
              status: "active",
              valid_until: "2024-12-31T00:00:00Z",
              service_accesses: [{ id: "sa1", service_key: "n8n", status: "active", external_id: "n8n-123", error: null }],
            },
          },
        ],
      },
      error: null,
    })
  ),

  http.post("/api/proxy/client/subscriptions/", () =>
    HttpResponse.json({
      success: true,
      data: { id: "sub2", status: "trial", product_name: "Atendimento WhatsApp", product_slug: "atendimento-whatsapp", billing_cycle: "monthly", amount: "199.00", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-12-31T00:00:00Z", created_at: "2024-01-01T00:00:00Z", license: null },
      error: null,
    }, { status: 201 })
  ),

  http.post("/api/proxy/client/subscriptions/:id/reactivate/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: {
        id: params.id,
        status: "active",
        product_name: "Atendimento WhatsApp",
        product_slug: "atendimento-whatsapp",
        billing_cycle: "monthly",
        amount: "199.00",
        starts_at: "2024-01-01T00:00:00Z",
        expires_at: "2024-12-31T00:00:00Z",
        created_at: "2024-01-01T00:00:00Z",
        license: null,
      },
      error: null,
    })
  ),

  http.post("/api/proxy/client/subscriptions/:id/cancel/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: {
        id: params.id,
        status: "cancelled",
        product_name: "Atendimento WhatsApp",
        product_slug: "atendimento-whatsapp",
        billing_cycle: "monthly",
        amount: "199.00",
        starts_at: "2024-01-01T00:00:00Z",
        expires_at: "2024-12-31T00:00:00Z",
        created_at: "2024-01-01T00:00:00Z",
        license: null,
      },
      error: null,
    })
  ),

  http.get("/api/proxy/client/quota/", () =>
    HttpResponse.json({
      success: true,
      data: {
        used_api_calls: 7500,
        max_api_calls: 10000,
        reset_at: "2024-07-01T00:00:00Z",
        usage_pct: 75.0,
      },
      error: null,
    })
  ),

  // BFF proxy → client api-keys
  http.get("/api/proxy/client/api-keys/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "key1", key: "test-key-abc123", is_active: true, created_at: "2024-01-01T00:00:00Z", revoked_at: null },
        { id: "key2", key: "revoked-key-xyz", is_active: false, created_at: "2024-01-01T00:00:00Z", revoked_at: "2024-06-01T00:00:00Z" },
      ],
      error: null,
    })
  ),

  http.post("/api/proxy/client/api-keys/", () =>
    HttpResponse.json({
      success: true,
      data: { id: "key3", key: "new-key-generated", is_active: true, created_at: "2024-06-10T00:00:00Z", revoked_at: null },
      error: null,
    }, { status: 201 })
  ),

  http.delete("/api/proxy/client/api-keys/:id/", () =>
    new HttpResponse(null, { status: 204 })
  ),

  // BFF proxy → admin
  http.get("/api/proxy/admin/customers/", () =>
    HttpResponse.json({
      success: true,
      data: {
        count: 2,
        next: null,
        previous: null,
        results: [
          { id: "c1", company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "active", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
          { id: "c2", company_name: "Mega Corp", document: "11.111.111/0001-11", status: "suspended", asaas_customer_id: "", created_at: "2024-02-01T00:00:00Z", updated_at: "2024-06-01T00:00:00Z" },
        ],
      },
      error: null,
    })
  ),

  http.get("/api/proxy/admin/customers/:id/", ({ params }) => {
    const customers = [
      { id: "c1", company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "active", asaas_customer_id: "asaas-c1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-01T00:00:00Z" },
      { id: "c2", company_name: "Mega Corp", document: "11.111.111/0001-11", status: "suspended", asaas_customer_id: "", created_at: "2024-02-01T00:00:00Z", updated_at: "2024-06-01T00:00:00Z" },
    ];
    const customer = customers.find((c) => c.id === params.id);
    if (!customer) return HttpResponse.json({ success: false, data: null, error: { code: "not_found", message: "Not found", details: [] } }, { status: 404 });
    return HttpResponse.json({ success: true, data: customer, error: null });
  }),

  http.post("/api/proxy/admin/customers/:id/suspend/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: { id: params.id, company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "suspended", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" },
      error: null,
    })
  ),

  http.post("/api/proxy/admin/customers/:id/reactivate/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: { id: params.id, company_name: "Mega Corp", document: "11.111.111/0001-11", status: "active", asaas_customer_id: "", created_at: "2024-02-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" },
      error: null,
    })
  ),

  http.post("/api/proxy/admin/customers/:id/cancel/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: { id: params.id, company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "cancelled", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" },
      error: null,
    })
  ),

  http.get("/api/proxy/admin/metrics/", () =>
    HttpResponse.json({
      success: true,
      data: {
        mrr: 5980.0,
        arr: 71760.0,
        active_customers: 12,
        new_customers: 3,
        churned_customers: 1,
        churn_rate: 7.7,
        at_risk_count: 2,
        revenue_by_plan: [
          { plan: "Atendimento WhatsApp", revenue: 3980.0, customer_count: 8 },
          { plan: "GLPI Helpdesk", revenue: 2000.0, customer_count: 4 },
        ],
        monthly_revenue: [
          { month: "2024-01", revenue: 4200 },
          { month: "2024-02", revenue: 5980 },
        ],
      },
      error: null,
    })
  ),

  http.get("/api/proxy/admin/billing/metrics/api-usage/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { customer_id: "c1", company_name: "Acme Ltda", used_api_calls: 7500, max_api_calls: 10000, usage_pct: 75.0, reset_at: "2024-07-01T00:00:00Z" },
        { customer_id: "c2", company_name: "Mega Corp", used_api_calls: 200, max_api_calls: 10000, usage_pct: 2.0, reset_at: "2024-07-01T00:00:00Z" },
      ],
      error: null,
    })
  ),

  http.get("/api/proxy/admin/audit-logs/", () =>
    HttpResponse.json({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          { id: "al1", action: "customer.created", resource_type: "Customer", resource_id: "c1", user: "admin@papermoon.com", ip_address: "127.0.0.1", metadata: {}, created_at: "2024-01-01T10:00:00Z" },
        ],
      },
      error: null,
    })
  ),

  // Admin — Invoices
  http.get("/api/proxy/admin/billing/invoices/", () =>
    HttpResponse.json({
      success: true,
      data: {
        count: 2,
        num_pages: 1,
        page: 1,
        results: [
          { id: "inv1", customer_id: "c1", company_name: "Acme Ltda", invoice_type: "subscription", billing_type: "BOLETO", description: "", amount: "199.00", status: "paid", due_date: "2024-06-01", asaas_id: "pay_abc", created_at: "2024-05-01T00:00:00Z" },
          { id: "inv2", customer_id: "c2", company_name: "Mega Corp", invoice_type: "support", billing_type: "PIX", description: "Chamado #1", amount: "399.00", status: "overdue", due_date: "2024-05-01", asaas_id: "pay_xyz", created_at: "2024-04-01T00:00:00Z" },
        ],
      },
      error: null,
    })
  ),

  http.delete("/api/proxy/admin/billing/invoices/:id/", () =>
    HttpResponse.json({ success: true, data: { message: "Fatura removida com sucesso." }, error: null })
  ),

  http.delete("/api/proxy/admin/customers/:id/delete/", () =>
    HttpResponse.json({ success: true, data: { message: "Customer removido com sucesso." }, error: null })
  ),

  // Client invoices
  http.get("/api/proxy/client/invoices/", ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get("status");
    const allInvoices = [
      { id: "i1", amount: "199.00", status: "paid", due_date: "2024-06-01", asaas_id: "pay_1", payment_url: null, created_at: "2024-05-01T00:00:00Z", updated_at: "2024-06-01T00:00:00Z" },
      { id: "i2", amount: "199.00", status: "pending", due_date: "2024-07-01", asaas_id: "pay_2", payment_url: "https://pay.asaas.com/i2", created_at: "2024-06-01T00:00:00Z", updated_at: "2024-06-01T00:00:00Z" },
      { id: "i3", amount: "199.00", status: "overdue", due_date: "2024-05-01", asaas_id: "pay_3", payment_url: null, created_at: "2024-04-01T00:00:00Z", updated_at: "2024-05-02T00:00:00Z" },
    ];
    const filtered = status ? allInvoices.filter((i) => i.status === status) : allInvoices;
    return HttpResponse.json({ success: true, data: { count: filtered.length, next: null, previous: null, results: filtered }, error: null });
  }),

  // Invoice CSV export
  http.get("/api/proxy/client/invoices/export/", () =>
    new HttpResponse("ID,Status,Valor (R$),Vencimento,Criado em,Asaas ID\ni1,paid,199.00,2024-06-01,2024-05-01,pay_1\n", {
      status: 200,
      headers: { "Content-Type": "text/csv", "Content-Disposition": "attachment; filename=\"faturas.csv\"" },
    })
  ),

  // Change password (BFF)
  http.post("/api/auth/change-password", () =>
    HttpResponse.json({ success: true, data: { message: "Senha alterada." }, error: null })
  ),

  // Update customer me
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  http.patch("/api/proxy/client/me/", ({ request: _req }) =>
    HttpResponse.json({ success: true, data: { id: "c1", company_name: "Nova Razão Ltda", document: "00.000.000/0001-00", status: "active", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" }, error: null })
  ),

  // Admin subscriptions
  http.get("/api/proxy/admin/subscriptions/", ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get("search") ?? "";
    const allResults = [
      { id: "sub1", status: "active", customer_id: "c1", customer_name: "Acme Ltda", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-12-31T00:00:00Z", created_at: "2024-01-01T00:00:00Z", product_name: "Atendimento WhatsApp", product_id: "prod1", product_slug: "atendimento-whatsapp", pricing_id: "price1", billing_cycle: "monthly", amount: "199.00", license: null },
      { id: "sub2", status: "suspended", customer_id: "c2", customer_name: "Beta Corp", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-06-30T00:00:00Z", created_at: "2024-01-01T00:00:00Z", product_name: "Atendimento WhatsApp", product_id: "prod1", product_slug: "atendimento-whatsapp", pricing_id: "price1", billing_cycle: "monthly", amount: "199.00", license: null },
    ];
    const results = search
      ? allResults.filter((r) => r.customer_name.toLowerCase().includes(search.toLowerCase()))
      : allResults;
    return HttpResponse.json({
      success: true,
      data: { count: results.length, next: null, previous: null, results },
      error: null,
    });
  }),

  http.post("/api/proxy/admin/subscriptions/", async ({ request }) => {
    const body = (await request.json()) as { customer_id: string; product_id: string; pricing_id: string };
    return HttpResponse.json(
      {
        success: true,
        data: {
          id: "sub-new",
          status: "trial",
          customer_id: body.customer_id,
          customer_name: "Acme Ltda",
          product_id: body.product_id,
          product_name: "Atendimento WhatsApp",
          product_slug: "atendimento-whatsapp",
          pricing_id: body.pricing_id,
          billing_cycle: "monthly",
          amount: "199.00",
          starts_at: "2024-06-01T00:00:00Z",
          expires_at: "2024-07-01T00:00:00Z",
          created_at: "2024-06-01T00:00:00Z",
          license: null,
        },
        error: null,
      },
      { status: 201 }
    );
  }),

  http.post("/api/proxy/admin/subscriptions/:id/suspend/", ({ params }) =>
    HttpResponse.json({ success: true, data: { id: params.id, status: "suspended", product_name: "Atendimento WhatsApp", product_slug: "atendimento-whatsapp", billing_cycle: "monthly", amount: "199.00", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-12-31T00:00:00Z", created_at: "2024-01-01T00:00:00Z", license: null }, error: null })
  ),

  http.post("/api/proxy/admin/subscriptions/:id/cancel/", ({ params }) =>
    HttpResponse.json({ success: true, data: { id: params.id, status: "cancelled", product_name: "Atendimento WhatsApp", product_slug: "atendimento-whatsapp", billing_cycle: "monthly", amount: "199.00", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-12-31T00:00:00Z", created_at: "2024-01-01T00:00:00Z", license: null }, error: null })
  ),

  http.post("/api/proxy/admin/subscriptions/:id/renew/", ({ params }) =>
    HttpResponse.json({ success: true, data: { id: params.id, status: "active", product_name: "Atendimento WhatsApp", product_slug: "atendimento-whatsapp", billing_cycle: "monthly", amount: "199.00", starts_at: "2024-01-01T00:00:00Z", expires_at: "2025-01-01T00:00:00Z", created_at: "2024-01-01T00:00:00Z", license: null }, error: null })
  ),

  // Admin subscription detail
  http.get("/api/proxy/admin/subscriptions/:id/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: { id: params.id, status: "active", customer_id: "c1", customer_name: "Acme Ltda", starts_at: "2024-01-01T00:00:00Z", expires_at: "2024-12-31T00:00:00Z", created_at: "2024-01-01T00:00:00Z", product_name: "Atendimento WhatsApp", product_slug: "atendimento-whatsapp", product_id: "prod1", pricing_id: "price1", billing_cycle: "monthly", amount: "199.00", license: null },
      error: null,
    })
  ),

  // Admin service accesses
  http.get("/api/proxy/admin/subscriptions/:id/services/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "sa1", service_key: "chatwoot", status: "active", external_id: "inbox-42", service_url: "https://chatwoot.papermoon.com", error: null },
        { id: "sa2", service_key: "n8n", status: "failed", external_id: null, service_url: null, error: "ConnectionError: max retries exceeded" },
      ],
      error: null,
    })
  ),

  http.post("/api/proxy/admin/service-accesses/:id/reprovision/", ({ params }) =>
    HttpResponse.json({
      success: true,
      data: { id: params.id, service_key: "n8n", status: "provisioning", external_id: null, service_url: null, error: null },
      error: null,
    })
  ),

  http.patch("/api/proxy/admin/service-accesses/:id/", async ({ params, request }) => {
    const body = (await request.json()) as { external_id?: string };
    return HttpResponse.json({
      success: true,
      data: {
        id: params.id,
        service_key: "chatwoot",
        status: "active",
        external_id: body.external_id ?? null,
        service_url: "https://chatwoot.papermoon.com",
        error: null,
      },
      error: null,
    });
  }),

  http.post("/api/proxy/admin/subscriptions/:id/services/", async ({ request }) => {
    const body = (await request.json()) as { service_key: string };
    return HttpResponse.json(
      {
        success: true,
        data: {
          id: "sa-new",
          service_key: body.service_key ?? "glpi",
          status: "provisioning",
          external_id: null,
          service_url: null,
          error: null,
        },
        error: null,
      },
      { status: 201 }
    );
  }),

  // Admin customer quota
  http.get("/api/proxy/admin/customers/:id/quota/", () =>
    HttpResponse.json({
      success: true,
      data: { max_api_calls: 10000, used_api_calls: 3200, reset_at: "2024-07-01T00:00:00Z" },
      error: null,
    })
  ),

  http.patch("/api/proxy/admin/customers/:id/quota/", () =>
    HttpResponse.json({
      success: true,
      data: { max_api_calls: 20000, used_api_calls: 3200, reset_at: "2024-07-01T00:00:00Z" },
      error: null,
    })
  ),

  // Platform health
  http.get("/api/proxy/health/", () =>
    HttpResponse.json({
      success: true,
      data: { db: "ok", redis: "ok", celery: "ok" },
      error: null,
    })
  ),

  // Admin products
  http.get("/api/proxy/admin/products/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "prod1", name: "Atendimento WhatsApp", slug: "atendimento-whatsapp", description: "Plano básico", is_active: true, components: [{ id: "comp1", service_key: "n8n", config: {} }], pricings: [{ id: "price1", billing_cycle: "monthly", amount: "199.00", trial_days: 7, is_active: true }], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
        { id: "prod2", name: "GLPI Helpdesk", slug: "pro", description: "Plano avançado", is_active: false, components: [], pricings: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
      ],
      error: null,
    })
  ),

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  http.patch("/api/proxy/admin/products/:id/", ({ params, request: _req }) =>
    HttpResponse.json({ success: true, data: { id: params.id, name: "Atendimento WhatsApp", slug: "atendimento-whatsapp", description: "Plano básico", is_active: false, components: [], pricings: [], created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" }, error: null })
  ),

  // Client financial metrics
  http.get("/api/proxy/client/metrics/", () =>
    HttpResponse.json({
      success: true,
      data: { total_paid: 1200.0, total_pending: 199.0, total_overdue: 399.0 },
      error: null,
    })
  ),

  // In-app notifications
  http.get("/api/proxy/client/notifications/", ({ request }) => {
    const url = new URL(request.url);
    const page = url.searchParams.get("page");
    if (page) {
      return HttpResponse.json({
        success: true,
        data: {
          count: 2,
          unread_count: 1,
          num_pages: 1,
          page: 1,
          results: [
            { id: "notif1", event_type: "payment.processed", subject: "Pagamento confirmado", body: "Fatura de R$ 199.00 paga.", is_read: false, created_at: "2024-06-01T10:00:00Z", read_at: null },
            { id: "notif2", event_type: "subscription.renewed", subject: "Assinatura renovada", body: "Sua assinatura foi renovada.", is_read: true, created_at: "2024-05-01T10:00:00Z", read_at: "2024-05-02T10:00:00Z" },
          ],
        },
        error: null,
      });
    }
    return HttpResponse.json({
      success: true,
      data: {
        count: 2,
        unread_count: 1,
        results: [
          { id: "notif1", event_type: "payment.processed", subject: "Pagamento confirmado", body: "Fatura de R$ 199.00 paga.", is_read: false, created_at: "2024-06-01T10:00:00Z", read_at: null },
          { id: "notif2", event_type: "subscription.renewed", subject: "Assinatura renovada", body: "Sua assinatura foi renovada.", is_read: true, created_at: "2024-05-01T10:00:00Z", read_at: "2024-05-02T10:00:00Z" },
        ],
      },
      error: null,
    });
  }),

  http.post("/api/proxy/client/notifications/:id/read/", () =>
    HttpResponse.json({ success: true, data: { message: "Notificação marcada como lida." }, error: null })
  ),

  http.post("/api/proxy/client/notifications/read-all/", () =>
    HttpResponse.json({ success: true, data: { message: "2 notificações marcadas como lidas." }, error: null })
  ),

  // Team & invitations
  http.get("/api/proxy/client/team/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "prof1", email: "owner@acme.com", username: "owner", role: "owner", joined_at: "2024-01-01T00:00:00Z", is_you: true },
        { id: "prof2", email: "member@acme.com", username: "member", role: "member", joined_at: "2024-03-01T00:00:00Z", is_you: false },
      ],
      error: null,
    })
  ),

  http.get("/api/proxy/client/invitations/", () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "inv1", email: "novo@empresa.com", role: "member", status: "pending", expires_at: "2099-01-01T00:00:00Z", created_at: "2024-06-01T00:00:00Z", accepted_at: null },
        { id: "inv2", email: "antigo@empresa.com", role: "admin", status: "accepted", expires_at: "2024-01-10T00:00:00Z", created_at: "2024-01-01T00:00:00Z", accepted_at: "2024-01-05T00:00:00Z" },
      ],
      error: null,
    })
  ),

  http.post("/api/proxy/client/invitations/", () =>
    HttpResponse.json({
      success: true,
      data: { id: "inv3", email: "convidado@empresa.com", role: "member", status: "pending", expires_at: "2099-01-01T00:00:00Z", created_at: "2024-06-10T00:00:00Z", accepted_at: null },
      error: null,
    }, { status: 201 })
  ),

  http.delete("/api/proxy/client/invitations/:id/", () =>
    new HttpResponse(null, { status: 204 })
  ),
];
