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

// Admin — SSO configuration (Backoffice → Configurações)
export interface SSOConfig {
  enabled: boolean;
  issuer: string;
  client_id: string;
  client_secret_set: boolean;
  staff_group: string;
  redirect_uri: string;
  updated_at: string | null;
  updated_by_email: string | null;
}

export interface SSOConfigUpdatePayload {
  enabled: boolean;
  issuer?: string;
  client_id?: string;
  client_secret?: string;
  staff_group?: string;
}

export interface SSOTestResult {
  reachable: boolean;
  message: string;
}

// Admin — conexão central do PaperMoon com o Keycloak que ELE administra via
// Admin REST API, pra provisionar realms/clients de clientes (Backoffice →
// Configurações). NÃO é o SSOConfig acima (aquilo é o SSO de STAFF — Keycloaks
// diferentes, só reaproveitam o mesmo padrão de tela/config).
export interface KeycloakConnectionConfig {
  enabled: boolean;
  api_url: string;
  admin_token_set: boolean;
  updated_at: string | null;
  updated_by_email: string | null;
}

export interface KeycloakConnectionUpdatePayload {
  enabled: boolean;
  api_url?: string;
  admin_token?: string;
}

// Client — guia de integração Keycloak e criação real de client OIDC
// (diferente do SSOConfig acima, que é o SSO de STAFF do próprio backoffice —
// isto aqui é o realm Keycloak que o PaperMoon provisiona pro cliente como
// produto, ver ServiceAccess.service_key === "keycloak")
export type KeycloakIntegrationLanguage =
  | "django"
  | "drf"
  | "nextjs"
  | "js"
  | "node"
  | "go"
  | "csharp";

export type KeycloakIntegrationUnavailableReason = "platform_not_configured" | "no_service_access";

export interface KeycloakIntegrationGuide {
  available: boolean;
  reason?: KeycloakIntegrationUnavailableReason | null;
  verified?: boolean;
  issuer?: string;
  authorization_endpoint?: string;
  token_endpoint?: string;
  userinfo_endpoint?: string;
  jwks_uri?: string;
  end_session_endpoint?: string;
  client_id_suggestion?: string;
  redirect_uri?: string;
  scopes?: string[];
  language?: KeycloakIntegrationLanguage;
  package?: string;
  install_command?: string;
  steps?: string[];
  code_snippet?: string;
}

// Client — integrações já criadas de verdade (client OIDC no Keycloak do cliente)
export interface KeycloakClientIntegration {
  id: string;
  client_id: string;
  realm: string;
  app_name: string;
  base_url: string;
  redirect_uri: string;
  language: KeycloakIntegrationLanguage;
  public_client: boolean;
  created_at: string;
}

export interface KeycloakIntegrationListResult {
  available: boolean;
  reason: KeycloakIntegrationUnavailableReason | null;
  integrations: KeycloakClientIntegration[];
}

export interface KeycloakIntegrationCreatePayload {
  language: KeycloakIntegrationLanguage;
  app_name?: string;
  base_url: string;
  redirect_path?: string;
}

export interface KeycloakIntegrationCreateResult {
  id: string;
  client_id: string;
  client_secret: string | null;
  public_client: boolean;
  verified: boolean;
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
  jwks_uri: string;
  end_session_endpoint: string;
  redirect_uri: string;
  scopes: string[];
  language: KeycloakIntegrationLanguage;
  package: string;
  install_command: string;
  steps: string[];
  code_snippet: string;
}

export interface KeycloakIntegrationSecretResult {
  client_secret: string;
}

// Admin — ferramenta de diagnóstico genérica (Backoffice → Integração
// Keycloak), sem vínculo com nenhum cliente/realm do PaperMoon
export interface KeycloakIssuerValidationResult {
  verified: boolean;
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
  jwks_uri: string;
  end_session_endpoint: string;
}

export interface KeycloakCodeSnippetPayload {
  language: KeycloakIntegrationLanguage;
  issuer: string;
  client_id: string;
  base_url: string;
  redirect_uri: string;
}

export interface KeycloakCodeSnippetResult {
  language: KeycloakIntegrationLanguage;
  public_client: boolean;
  package: string;
  install_command: string;
  steps: string[];
  code_snippet: string;
  verified: boolean;
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
  product_id: string;
  slug: string;
  product_name: string;
  is_active: boolean;
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
  product_id: string;
  slug: string;
  product_name: string;
  has_page: boolean;
  is_active: boolean;
  updated_at: string | null;
}

export type CmsPageAdminPayload = Omit<CmsPageAdmin, "product_id" | "slug" | "product_name" | "is_active" | "hero_image_url" | "images" | "updated_at">;

// Blog
export type BlogPostStatus = "draft" | "published";

export interface BlogPostListItem {
  slug: string;
  title: string;
  excerpt: string;
  cover_image_url: string | null;
  cover_image_alt: string;
  author_name: string;
  published_at: string | null;
}

export interface BlogPostDetail extends BlogPostListItem {
  body: string;
  meta_title: string;
  meta_description: string;
}

export interface BlogPostAdmin {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  body: string;
  cover_image_url: string | null;
  cover_image_alt: string;
  author: number;
  author_name: string;
  status: BlogPostStatus;
  published_at: string | null;
  meta_title: string;
  meta_description: string;
  created_at: string;
  updated_at: string;
}

export interface BlogPostAdminListItem {
  id: string;
  title: string;
  slug: string;
  status: BlogPostStatus;
  author_name: string;
  published_at: string | null;
  updated_at: string;
}

export type BlogPostAdminPayload = Partial<
  Pick<
    BlogPostAdmin,
    "title" | "slug" | "excerpt" | "body" | "cover_image_alt" | "status" | "meta_title" | "meta_description"
  >
>;
