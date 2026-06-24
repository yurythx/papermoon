import { api, unwrap } from "./api";
import type {
  AdminCustomer,
  AdminInvoice,
  AdminInvoiceList,
  APIUsageRow,
  ApiKey,
  ApiQuota,
  AuditLogEntry,
  CmsImage,
  CmsPageAdmin,
  CmsPageAdminListItem,
  CmsPageAdminPayload,
  Customer,
  CustomerQuota,
  FinancialMetrics,
  InAppNotificationList,
  Invitation,
  Invoice,
  License,
  LoginResponse,
  MeResponse,
  MRRMetrics,
  PaginatedResponse,
  PendingRegistration,
  Pricing,
  Product,
  ServiceAccess,
  Subscription,
  TeamMember,
} from "@/types";

// Auth — calls BFF /api/auth/* which manages httpOnly cookies
export const authService = {
  login: (email: string, password: string) =>
    api
      .post<{ success: boolean; data: LoginResponse; error: null }>("/auth/login", { email, password })
      .then(unwrap),

  logout: () => api.post("/auth/logout"),

  me: () =>
    api.get<{ success: boolean; data: MeResponse; error: null }>("/auth/me").then(unwrap),

  passwordReset: (email: string) =>
    api
      .post<{ success: boolean; data: { message: string }; error: null }>("/auth/password-reset", { email })
      .then(unwrap),

  passwordResetConfirm: (uid: string, token: string, password: string) =>
    api
      .post<{ success: boolean; data: { message: string }; error: null }>("/auth/password-reset/confirm", {
        uid,
        token,
        password,
      })
      .then(unwrap),

  changePassword: (currentPassword: string, newPassword: string) =>
    api
      .post<{ success: boolean; data: { message: string }; error: null }>("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      })
      .then(unwrap),
};

export const invitationService = {
  accept: (token: string, password: string) =>
    api
      .post<{ success: boolean; data: { message: string; customer_id: string; role: string }; error: null }>(
        "/invitations/accept",
        { token, password }
      )
      .then(unwrap),
};

// Data — calls BFF /api/proxy/* which forwards to Django with cookie token
export const customerService = {
  getMe: () =>
    api.get<{ success: boolean; data: Customer; error: null }>("/proxy/client/me/").then(unwrap),

  updateMe: (data: Partial<Customer>) =>
    api.patch<{ success: boolean; data: Customer; error: null }>("/proxy/client/me/", data).then(unwrap),

  getMetrics: () =>
    api.get<{ success: boolean; data: FinancialMetrics; error: null }>("/proxy/client/metrics/").then(unwrap),

  getQuota: (): Promise<ApiQuota> =>
    api.get<{ success: boolean; data: ApiQuota; error: null }>("/proxy/client/quota/").then(unwrap),
};

export const invoiceService = {
  list: (params?: { status?: string; ordering?: string; page?: number }) =>
    api
      .get<{ success: boolean; data: PaginatedResponse<Invoice>; error: null }>("/proxy/client/invoices/", { params })
      .then(unwrap),

  exportCsv: async (params?: { status?: string }): Promise<void> => {
    const res = await api.get("/proxy/client/invoices/export/", {
      params,
      responseType: "blob",
    });
    const url = URL.createObjectURL(res.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "faturas.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
};

export const licenseService = {
  list: () =>
    api.get<{ success: boolean; data: PaginatedResponse<License>; error: null }>("/proxy/client/licenses/").then(unwrap),

  get: (id: string) =>
    api.get<{ success: boolean; data: License; error: null }>(`/proxy/client/licenses/${id}/`).then(unwrap),
};

export const productService = {
  catalog: (): Promise<Product[]> =>
    api.get<{ success: boolean; data: Product[]; error: null }>("/proxy/products/catalog/").then(unwrap),
};

export const teamService = {
  listMembers: (): Promise<TeamMember[]> =>
    api.get<{ success: boolean; data: TeamMember[]; error: null }>("/proxy/client/team/").then(unwrap),

  listInvitations: (): Promise<Invitation[]> =>
    api.get<{ success: boolean; data: Invitation[]; error: null }>("/proxy/client/invitations/").then(unwrap),

  sendInvitation: (email: string, role: string): Promise<Invitation> =>
    api
      .post<{ success: boolean; data: Invitation; error: null }>("/proxy/client/invitations/", { email, role })
      .then(unwrap),

  revokeInvitation: (id: string): Promise<void> =>
    api.delete(`/proxy/client/invitations/${id}`).then(() => undefined),

  resendInvitation: (id: string): Promise<Invitation> =>
    api
      .post<{ success: boolean; data: Invitation; error: null }>(`/proxy/client/invitations/${id}/resend`)
      .then(unwrap),

  changeMemberRole: (id: string, role: string): Promise<TeamMember> =>
    api
      .patch<{ success: boolean; data: TeamMember; error: null }>(`/proxy/client/team/${id}`, { role })
      .then(unwrap),

  removeMember: (id: string): Promise<void> =>
    api.delete(`/proxy/client/team/${id}`).then(() => undefined),
};

export type DailyUsagePoint = { date: string; calls: number };

export const apiKeyService = {
  list: (): Promise<ApiKey[]> =>
    api.get<{ success: boolean; data: ApiKey[]; error: null }>("/proxy/client/api-keys/").then(unwrap),

  create: (): Promise<ApiKey> =>
    api.post<{ success: boolean; data: ApiKey; error: null }>("/proxy/client/api-keys/").then(unwrap),

  revoke: (id: string): Promise<void> =>
    api.delete(`/proxy/client/api-keys/${id}/`).then(() => undefined),

  usageHistory: (days = 30): Promise<DailyUsagePoint[]> =>
    api
      .get<{ success: boolean; data: DailyUsagePoint[]; error: null }>(
        `/proxy/client/api-keys/usage/daily/?days=${days}`
      )
      .then(unwrap),
};

export const subscriptionService = {
  list: () =>
    api
      .get<{ success: boolean; data: PaginatedResponse<Subscription>; error: null }>("/proxy/client/subscriptions/")
      .then(unwrap),

  get: (id: string) =>
    api
      .get<{ success: boolean; data: Subscription; error: null }>(`/proxy/client/subscriptions/${id}/`)
      .then(unwrap),

  subscribe: (productId: string, pricingId: string): Promise<Subscription> =>
    api
      .post<{ success: boolean; data: Subscription; error: null }>("/proxy/client/subscriptions/", {
        product_id: productId,
        pricing_id: pricingId,
      })
      .then(unwrap),

  reactivate: (id: string): Promise<Subscription> =>
    api
      .post<{ success: boolean; data: Subscription; error: null }>(`/proxy/client/subscriptions/${id}/reactivate`)
      .then(unwrap),

  cancel: (id: string, reason?: string): Promise<Subscription> =>
    api
      .post<{ success: boolean; data: Subscription; error: null }>(`/proxy/client/subscriptions/${id}/cancel`, { reason })
      .then(unwrap),

  changePlan: (id: string, pricingId: string): Promise<Subscription> =>
    api
      .post<{ success: boolean; data: Subscription; error: null }>(`/proxy/client/subscriptions/${id}/change-plan`, { pricing_id: pricingId })
      .then(unwrap),

  changePlanPreview: (id: string, pricingId: string): Promise<{ proration_amount: string; has_proration: boolean }> =>
    api
      .get<{ success: boolean; data: { proration_amount: string; has_proration: boolean }; error: null }>(`/proxy/client/subscriptions/${id}/change-plan-preview`, { params: { pricing_id: pricingId } })
      .then(unwrap),
};

export const adminService = {
  listCustomers: (params?: { status?: string; search?: string; page?: number }): Promise<PaginatedResponse<AdminCustomer>> =>
    api
      .get<{ success: boolean; data: PaginatedResponse<AdminCustomer>; error: null }>("/proxy/admin/customers/", { params })
      .then(unwrap),

  getCustomer: (id: string): Promise<AdminCustomer> =>
    api
      .get<{ success: boolean; data: AdminCustomer; error: null }>(`/proxy/admin/customers/${id}/`)
      .then(unwrap),

  suspendCustomer: (id: string): Promise<AdminCustomer> =>
    api
      .post<{ success: boolean; data: AdminCustomer; error: null }>(`/proxy/admin/customers/${id}/suspend/`)
      .then(unwrap),

  reactivateCustomer: (id: string): Promise<AdminCustomer> =>
    api
      .post<{ success: boolean; data: AdminCustomer; error: null }>(`/proxy/admin/customers/${id}/reactivate/`)
      .then(unwrap),

  cancelCustomer: (id: string): Promise<AdminCustomer> =>
    api
      .post<{ success: boolean; data: AdminCustomer; error: null }>(`/proxy/admin/customers/${id}/cancel/`)
      .then(unwrap),

  getMetrics: (): Promise<MRRMetrics> =>
    api
      .get<{ success: boolean; data: MRRMetrics; error: null }>("/proxy/admin/metrics/")
      .then(unwrap),

  getMRRMetrics: (): Promise<MRRMetrics> =>
    api
      .get<{ success: boolean; data: MRRMetrics; error: null }>("/proxy/admin/billing/metrics/mrr/")
      .then(unwrap),

  getAPIUsage: (): Promise<APIUsageRow[]> =>
    api
      .get<{ success: boolean; data: APIUsageRow[]; error: null }>("/proxy/admin/billing/metrics/api-usage/")
      .then(unwrap),

  getAuditLogs: (params?: { resource_type?: string; action?: string; page?: number }): Promise<PaginatedResponse<AuditLogEntry>> =>
    api
      .get<{ success: boolean; data: PaginatedResponse<AuditLogEntry>; error: null }>("/proxy/admin/audit-logs/", { params })
      .then(unwrap),

  listSubscriptions: (params?: { status?: string; customer_id?: string; search?: string; page?: number }): Promise<PaginatedResponse<Subscription>> =>
    api
      .get<{ success: boolean; data: PaginatedResponse<Subscription>; error: null }>("/proxy/admin/subscriptions/", { params })
      .then(unwrap),

  suspendSubscription: (id: string): Promise<Subscription> =>
    api.post<{ success: boolean; data: Subscription; error: null }>(`/proxy/admin/subscriptions/${id}/suspend/`).then(unwrap),

  cancelSubscription: (id: string): Promise<Subscription> =>
    api.post<{ success: boolean; data: Subscription; error: null }>(`/proxy/admin/subscriptions/${id}/cancel/`).then(unwrap),

  softDeleteCustomer: (id: string): Promise<{ message: string }> =>
    api.delete<{ success: boolean; data: { message: string }; error: null }>(`/proxy/admin/customers/${id}/delete/`).then(unwrap),

  listInvoices: (params?: { status?: string; invoice_type?: string; customer_id?: string; page?: number }): Promise<AdminInvoiceList> =>
    api.get<{ success: boolean; data: AdminInvoiceList; error: null }>("/proxy/admin/billing/invoices/", { params }).then(unwrap),

  createInvoice: (data: {
    customer_id: string;
    invoice_type: string;
    amount: string;
    due_date: string;
    description?: string;
    billing_type?: string;
  }): Promise<AdminInvoice> =>
    api.post<{ success: boolean; data: AdminInvoice; error: null }>("/proxy/admin/billing/invoices/", data).then(unwrap),

  softDeleteInvoice: (id: string): Promise<{ message: string }> =>
    api.delete<{ success: boolean; data: { message: string }; error: null }>(`/proxy/admin/billing/invoices/${id}/`).then(unwrap),

  renewSubscription: (id: string): Promise<Subscription> =>
    api.post<{ success: boolean; data: Subscription; error: null }>(`/proxy/admin/subscriptions/${id}/renew/`).then(unwrap),

  listProducts: (): Promise<Product[]> =>
    api.get<{ success: boolean; data: Product[]; error: null }>("/proxy/admin/products/").then(unwrap),

  toggleProduct: (id: string, isActive: boolean): Promise<Product> =>
    api.patch<{ success: boolean; data: Product; error: null }>(`/proxy/admin/products/${id}`, { is_active: isActive }).then(unwrap),

  createCustomer: (data: { company_name: string; document: string }): Promise<AdminCustomer> =>
    api.post<{ success: boolean; data: AdminCustomer; error: null }>("/proxy/admin/customers/", data).then(unwrap),

  createProduct: (data: { name: string; slug: string; description: string; is_active: boolean }): Promise<Product> =>
    api.post<{ success: boolean; data: Product; error: null }>("/proxy/admin/products/", data).then(unwrap),

  updateProduct: (id: string, data: { name: string; slug: string; description: string; is_active: boolean }): Promise<Product> =>
    api.patch<{ success: boolean; data: Product; error: null }>(`/proxy/admin/products/${id}/`, data).then(unwrap),

  createPricing: (
    productId: string,
    data: { billing_cycle: string; amount: string; trial_days: number; max_api_calls: number; max_users: number; is_active: boolean }
  ): Promise<Pricing> =>
    api.post<{ success: boolean; data: Pricing; error: null }>(`/proxy/admin/products/${productId}/pricings/`, data).then(unwrap),

  updatePricing: (
    productId: string,
    pricingId: string,
    data: { amount: string; trial_days: number; max_api_calls: number; max_users: number; is_active: boolean }
  ): Promise<Pricing> =>
    api.patch<{ success: boolean; data: Pricing; error: null }>(`/proxy/admin/products/${productId}/pricings/${pricingId}/`, data).then(unwrap),

  getCustomerQuota: (customerId: string): Promise<CustomerQuota> =>
    api.get<{ success: boolean; data: CustomerQuota; error: null }>(`/proxy/admin/customers/${customerId}/quota/`).then(unwrap),

  updateCustomerQuota: (customerId: string, maxApiCalls: number): Promise<CustomerQuota> =>
    api.patch<{ success: boolean; data: CustomerQuota; error: null }>(`/proxy/admin/customers/${customerId}/quota/`, { max_api_calls: maxApiCalls }).then(unwrap),

  getHealthStatus: (): Promise<{ db: string; redis: string; celery: string }> =>
    api.get<{ success: boolean; data: { db: string; redis: string; celery: string }; error: null }>("/proxy/health/").then(unwrap),

  getSubscription: (id: string): Promise<Subscription> =>
    api.get<{ success: boolean; data: Subscription; error: null }>(`/proxy/admin/subscriptions/${id}/`).then(unwrap),

  listServiceAccesses: (subscriptionId: string): Promise<ServiceAccess[]> =>
    api.get<{ success: boolean; data: ServiceAccess[]; error: null }>(`/proxy/admin/subscriptions/${subscriptionId}/services/`).then(unwrap),

  reprovisionServiceAccess: (id: string): Promise<ServiceAccess> =>
    api.post<{ success: boolean; data: ServiceAccess; error: null }>(`/proxy/admin/service-accesses/${id}/reprovision/`).then(unwrap),

  patchServiceAccess: (id: string, data: { external_id?: string; config?: Record<string, unknown> }): Promise<ServiceAccess> =>
    api.patch<{ success: boolean; data: ServiceAccess; error: null }>(`/proxy/admin/service-accesses/${id}/`, data).then(unwrap),

  addServiceAccess: (subscriptionId: string, serviceKey: string): Promise<ServiceAccess> =>
    api
      .post<{ success: boolean; data: ServiceAccess; error: null }>(
        `/proxy/admin/subscriptions/${subscriptionId}/services/`,
        { service_key: serviceKey }
      )
      .then(unwrap),

  createSubscription: (data: {
    customer_id: string;
    product_id: string;
    pricing_id: string;
  }): Promise<Subscription> =>
    api
      .post<{ success: boolean; data: Subscription; error: null }>("/proxy/admin/subscriptions/", data)
      .then(unwrap),

  listPendingRegistrations: (): Promise<PendingRegistration[]> =>
    api
      .get<{ success: boolean; data: PendingRegistration[]; error: null }>("/proxy/auth/pending-registrations/")
      .then(unwrap),

  provisionUser: (userId: string, data: { company_name: string; document: string }): Promise<AdminCustomer> =>
    api
      .post<{ success: boolean; data: AdminCustomer; error: null }>(`/proxy/auth/pending-registrations/${userId}/provision/`, data)
      .then(unwrap),

  // CMS
  listCmsPages: (): Promise<CmsPageAdminListItem[]> =>
    api
      .get<{ success: boolean; data: CmsPageAdminListItem[]; error: null }>("/proxy/admin/cms/pages/")
      .then(unwrap),

  getCmsPage: (slug: string): Promise<CmsPageAdmin> =>
    api
      .get<{ success: boolean; data: CmsPageAdmin; error: null }>(`/proxy/admin/cms/pages/${slug}/`)
      .then(unwrap),

  updateCmsPage: (slug: string, data: CmsPageAdminPayload): Promise<CmsPageAdmin> =>
    api
      .patch<{ success: boolean; data: CmsPageAdmin; error: null }>(`/proxy/admin/cms/pages/${slug}/`, data)
      .then(unwrap),

  uploadCmsHero: (slug: string, file: File): Promise<{ hero_image_url: string | null }> => {
    const formData = new FormData();
    formData.append("hero_image", file);
    return api
      .post<{ success: boolean; data: { hero_image_url: string | null }; error: null }>(
        `/proxy/admin/cms/pages/${slug}/hero/`,
        formData
      )
      .then(unwrap);
  },

  deleteCmsHero: (slug: string): Promise<void> =>
    api.delete(`/proxy/admin/cms/pages/${slug}/hero/`).then(() => undefined),

  uploadCmsGalleryImage: (slug: string, file: File, alt?: string, caption?: string): Promise<CmsImage> => {
    const formData = new FormData();
    formData.append("image", file);
    if (alt) formData.append("alt", alt);
    if (caption) formData.append("caption", caption);
    return api
      .post<{ success: boolean; data: CmsImage; error: null }>(
        `/proxy/admin/cms/pages/${slug}/gallery/`,
        formData
      )
      .then(unwrap);
  },

  deleteCmsGalleryImage: (slug: string, pk: number): Promise<void> =>
    api.delete(`/proxy/admin/cms/pages/${slug}/gallery/${pk}/`).then(() => undefined),
};

export const notificationService = {
  list: (page?: number): Promise<InAppNotificationList> =>
    api
      .get<{ success: boolean; data: InAppNotificationList; error: null }>("/proxy/client/notifications/", {
        params: page ? { page } : undefined,
      })
      .then(unwrap),

  markRead: (id: string): Promise<void> =>
    api.post(`/proxy/client/notifications/${id}/read`).then(() => undefined),

  markAllRead: (): Promise<void> =>
    api.post("/proxy/client/notifications/read-all").then(() => undefined),
};
