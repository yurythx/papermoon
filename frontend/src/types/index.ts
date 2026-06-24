// API envelope
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
}

export interface ApiError {
  code: string;
  message: string;
  details: string[];
}

// Auth — BFF stores tokens in httpOnly cookies, browser only receives a confirmation
export interface LoginResponse {
  message: string;
}

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  is_staff: boolean;
}

export interface MeResponse {
  user: AuthUser;
  customer: Customer | null;
  role: "owner" | "admin" | "member" | null;
}

// Customer (tenant)
export interface Customer {
  id: string;
  company_name: string;
  document: string;
  status: "active" | "suspended" | "cancelled";
  asaas_customer_id: string;
  created_at: string;
  updated_at: string;
}

// Subscription
export interface ServiceAccess {
  id: string;
  service_key: string;
  status: "provisioning" | "active" | "suspended" | "failed";
  external_id: string | null;
  service_url: string | null;
  error: string | null;
}

export interface CustomerQuota {
  max_api_calls: number | null;
  used_api_calls: number;
  reset_at: string | null;
}

export interface License {
  id: string;
  key: string;
  status: "active" | "expired" | "suspended";
  valid_from: string;
  valid_until: string;
  days_remaining: number;
  product_name: string;
  product_slug: string;
  subscription_id: string;
  subscription_status: string;
  billing_cycle: "monthly" | "annual" | "lifetime" | "one_time";
  amount: string;
  services: ServiceAccess[];
  created_at: string;
}

export interface Subscription {
  id: string;
  status: "trial" | "active" | "suspended" | "expired" | "grace_period" | "cancelled";
  starts_at: string;
  expires_at: string;
  created_at: string;
  customer_id?: string;
  customer_name?: string;
  product_id: string;
  product_name: string;
  product_slug: string;
  pricing_id: string;
  billing_cycle: string;
  amount: string;
  license: {
    id: string;
    key: string;
    status: string;
    valid_until: string;
    service_accesses: ServiceAccess[];
  } | null;
}

// Product catalog
export interface Pricing {
  id: string;
  billing_cycle: "monthly" | "annual" | "lifetime" | "one_time";
  amount: string;
  trial_days: number;
  is_active: boolean;
  max_api_calls?: number | null;
  max_users?: number | null;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  components: { id: string; service_key: string; config: Record<string, unknown> }[];
  pricings: Pricing[];
  created_at: string;
  updated_at: string;
}

// Invoice
export interface Invoice {
  id: string;
  invoice_type: "subscription" | "implementation" | "support";
  description: string;
  amount: string;
  status: "pending" | "paid" | "overdue" | "cancelled";
  due_date: string;
  asaas_id: string;
  payment_url: string | null;
  created_at: string;
  updated_at: string;
}

// Metrics
export interface FinancialMetrics {
  total_paid: number;
  total_pending: number;
  total_overdue: number;
}

// API Quota
export interface ApiQuota {
  used_api_calls: number;
  max_api_calls: number;
  reset_at: string | null;
  usage_pct: number;
  billing_cycle: string | null;
  plan_name?: string | null;
}

// Team
export interface TeamMember {
  id: string;
  email: string;
  username: string;
  role: "owner" | "admin" | "member";
  joined_at: string;
  is_you: boolean;
}

export interface Invitation {
  id: string;
  email: string;
  role: "owner" | "admin" | "member";
  status: "pending" | "accepted" | "revoked" | "expired";
  expires_at: string;
  created_at: string;
  accepted_at: string | null;
}

// Admin — Invoices
export interface AdminInvoice {
  id: string;
  customer_id: string;
  company_name: string;
  invoice_type: "subscription" | "implementation" | "support";
  billing_type: "BOLETO" | "PIX" | "CREDIT_CARD";
  description: string;
  amount: string;
  status: "pending" | "paid" | "overdue" | "cancelled";
  due_date: string;
  asaas_id: string;
  payment_url: string;
  created_at: string;
}

export interface AdminInvoiceList {
  count: number;
  num_pages: number;
  page: number;
  results: AdminInvoice[];
}

// Admin — Pending Registrations
export interface PendingRegistration {
  id: string;
  email: string;
  name: string;
  company_name: string;
  phone: string;
  registered_at: string;
}

// Admin — Customers
export interface AdminCustomer {
  id: string;
  company_name: string;
  document: string;
  status: "active" | "suspended" | "cancelled";
  asaas_customer_id: string;
  created_at: string;
  updated_at: string;
}

// Admin — Metrics
export interface MRRMetrics {
  mrr: number;
  arr: number;
  active_customers: number;
  new_customers: number;
  churned_customers: number;
  churn_rate: number;
  at_risk_count: number;
  revenue_by_plan: { plan: string; revenue: number; customer_count: number }[];
  monthly_revenue: { month: string; revenue: number }[];
}

export interface APIUsageRow {
  customer_id: string;
  company_name: string;
  used_api_calls: number;
  max_api_calls: number;
  usage_pct: number;
  reset_at: string;
}

// Admin — Audit Log
export interface AuditLogEntry {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user: string | null;
  ip_address: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

// API Key
export interface ApiKey {
  id: string;
  key: string;
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

// In-app notifications
export interface InAppNotification {
  id: string;
  event_type: string;
  subject: string;
  body: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface InAppNotificationList {
  count: number;
  unread_count: number;
  num_pages?: number;
  page?: number;
  results: InAppNotification[];
}

// Pagination
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// CMS — Admin editor types
export interface CmsResponsibility {
  side: "papermoon" | "client";
  text: string;
  order: number;
}

export interface CmsStep {
  number: string;
  title: string;
  description: string;
  order: number;
}

export interface CmsFeatureItem {
  text: string;
  order: number;
}

export interface CmsFeatureGroup {
  title: string;
  order: number;
  items: CmsFeatureItem[];
}

export interface CmsFAQ {
  question: string;
  answer: string;
  order: number;
}

export interface CmsImage {
  id: number;
  url: string;
  alt: string;
  caption: string;
  order: number;
}

export interface CmsPageAdmin {
  slug: string;
  product_name: string;
  hero_image_url: string | null;
  hero_image_alt: string;
  tagline: string;
  description: string;
  meta_title: string;
  meta_description: string;
  responsibilities: CmsResponsibility[];
  steps: CmsStep[];
  feature_groups: CmsFeatureGroup[];
  faqs: CmsFAQ[];
  images: CmsImage[];
  updated_at: string;
}

export interface CmsPageAdminListItem {
  slug: string;
  product_name: string;
  has_page: boolean;
  updated_at: string | null;
}

export type CmsPageAdminPayload = Omit<CmsPageAdmin, "slug" | "product_name" | "hero_image_url" | "images" | "updated_at">;
