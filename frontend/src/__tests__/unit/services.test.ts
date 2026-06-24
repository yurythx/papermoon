import { describe, expect, it } from "vitest";
import { adminService, apiKeyService, authService, licenseService, productService } from "@/lib/services";

describe("authService", () => {
  it("login returns message on success", async () => {
    const result = await authService.login("owner@acme.com", "demo123");
    expect(result).toEqual({ message: "ok" });
  });

  it("me returns user profile", async () => {
    const result = await authService.me();
    expect(result.user.email).toBe("owner@acme.com");
    expect(result.customer?.company_name).toBe("Acme Ltda");
    expect(result.role).toBe("owner");
  });
});

describe("productService", () => {
  it("catalog returns list of active products", async () => {
    const products = await productService.catalog();
    expect(products).toHaveLength(1);
    expect(products[0].name).toBe("Atendimento WhatsApp");
    expect(products[0].pricings).toHaveLength(2);
  });

  it("each product has components", async () => {
    const products = await productService.catalog();
    expect(products[0].components[0].service_key).toBe("n8n");
  });
});

describe("licenseService", () => {
  it("list returns paginated licenses", async () => {
    const result = await licenseService.list();
    expect(result.count).toBe(1);
    expect(result.results[0].status).toBe("active");
    expect(result.results[0].days_remaining).toBe(90);
  });

  it("get returns a single license by id", async () => {
    const license = await licenseService.get("lic1");
    expect(license.key).toBe("lic-abc123");
    expect(license.services[0].service_key).toBe("n8n");
  });

  it("get throws on unknown id", async () => {
    await expect(licenseService.get("unknown-id")).rejects.toThrow();
  });
});

describe("apiKeyService", () => {
  it("list returns array of api keys", async () => {
    const keys = await apiKeyService.list();
    expect(keys).toHaveLength(2);
    expect(keys[0].key).toBe("test-key-abc123");
    expect(keys[0].is_active).toBe(true);
    expect(keys[1].is_active).toBe(false);
  });

  it("create returns the new key", async () => {
    const key = await apiKeyService.create();
    expect(key.id).toBe("key3");
    expect(key.key).toBe("new-key-generated");
    expect(key.is_active).toBe(true);
  });

  it("revoke resolves without value", async () => {
    const result = await apiKeyService.revoke("key1");
    expect(result).toBeUndefined();
  });
});

describe("adminService", () => {
  it("listCustomers returns paginated customers", async () => {
    const result = await adminService.listCustomers();
    expect(result.count).toBe(2);
    expect(result.results[0].company_name).toBe("Acme Ltda");
    expect(result.results[1].status).toBe("suspended");
  });

  it("getMetrics returns MRR and ARR", async () => {
    const metrics = await adminService.getMetrics();
    expect(metrics.mrr).toBe(5980.0);
    expect(metrics.arr).toBe(71760.0);
    expect(metrics.active_customers).toBe(12);
    expect(metrics.churned_customers).toBe(1);
    expect(metrics.monthly_revenue).toHaveLength(2);
  });

  it("getAPIUsage returns per-customer usage rows", async () => {
    const usage = await adminService.getAPIUsage();
    expect(usage).toHaveLength(2);
    expect(usage[0].company_name).toBe("Acme Ltda");
    expect(usage[0].usage_pct).toBe(75.0);
  });

  it("suspendCustomer returns updated customer", async () => {
    const customer = await adminService.suspendCustomer("c1");
    expect(customer.status).toBe("suspended");
  });

  it("reactivateCustomer returns updated customer", async () => {
    const customer = await adminService.reactivateCustomer("c2");
    expect(customer.status).toBe("active");
  });
});
