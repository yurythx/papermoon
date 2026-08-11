"use client";

import { PageHeader } from "@/components/compound/page-header";
import { KeycloakIntegrationManager } from "@/components/keycloak/keycloak-integration-manager";
import { integrationService } from "@/lib/services";

export default function KeycloakIntegrationPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Integração SSO (Keycloak)"
        description="Crie um client OIDC de verdade — ou só gere um guia com as URLs e o código pra conectar seu sistema"
      />
      <KeycloakIntegrationManager
        queryKeyPrefix={["keycloak-integrations"]}
        services={{
          listIntegrations: integrationService.listKeycloakIntegrations,
          createIntegration: integrationService.createKeycloakIntegration,
          getGuide: integrationService.getKeycloakGuide,
          getSecret: integrationService.getKeycloakIntegrationSecret,
        }}
      />
    </div>
  );
}
