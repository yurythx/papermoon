"""
Conteúdo estático do guia de integração Keycloak (client-facing).

Cada entrada de LANGUAGE_PACKS descreve uma stack: a lib recomendada, os
passos e um `code_template` com placeholders `__ALGO__` substituídos por
`apps.subscriptions.keycloak_guide.build_integration_guide()` via `.replace()`
simples — não `.format()`/f-string, de propósito: várias dessas linguagens
(JS, Go, C#) usam `{`/`}` pra sintaxe própria dentro do próprio snippet, e
`.format()` exigiria escapar toda chave literal (`{{`/`}}`), frágil e fácil
de esquecer. `.replace()` com placeholders `__ASSIM__` não colide com nada.

Placeholders disponíveis em todo `code_template`:
    __ISSUER__              URL do realm (ex: https://auth.papermoon.com/realms/tenant-abc123)
    __CLIENT_ID__            slug sugerido a partir do nome do app
    __CLIENT_SECRET__        secret real (client criado de verdade) ou o literal
                             histórico "COLE_AQUI_O_CLIENT_SECRET" (guia read-only)
    __REDIRECT_URI__         __BASE_URL__ + o redirect_path resolvido (ver keycloak_guide.py)
    __BASE_URL__             URL base informada pelo cliente
    __AUTH_ENDPOINT__        authorization_endpoint
    __TOKEN_ENDPOINT__       token_endpoint
    __USERINFO_ENDPOINT__    userinfo_endpoint
    __JWKS_URI__             jwks_uri
    __LOGOUT_ENDPOINT__      end_session_endpoint
    __SCOPES_SPACE__         scopes separados por espaço: "openid profile email"
    __SCOPES_GO__            scopes como literal Go: "openid", "profile", "email"
    __SCOPES_CSHARP__        scopes como linhas options.Scope.Add("...") do ASP.NET Core

Cada pacote também tem `public_client: bool` — só True para "js" (SPA sem
backend, sem onde guardar segredo). Determina o tipo de client criado de
verdade no Keycloak (ver apps.provisioning.keycloak.create_oidc_client):
público usa PKCE e não tem client_secret; confidencial usa client_secret.
"""

DEFAULT_SCOPES = ["openid", "profile", "email"]

LANGUAGE_PACKS: dict[str, dict] = {
    "django": {
        "label": "Django (monolito)",
        "package": "mozilla-django-oidc",
        "install_command": "pip install mozilla-django-oidc",
        "default_redirect_path": "/oidc/callback/",
        "public_client": False,
        "steps": [
            "Instale o pacote: pip install mozilla-django-oidc.",
            "Adicione 'mozilla_django_oidc' a INSTALLED_APPS e o backend de "
            "autenticação a AUTHENTICATION_BACKENDS (veja o snippet).",
            "Cole as variáveis OIDC_* no settings.py com os valores desta página.",
            "Inclua mozilla_django_oidc.urls no urls.py raiz do projeto.",
            "Peça pro time do PaperMoon cadastrar o client no seu realm com o "
            "Redirect URI mostrado acima — client confidencial (com secret), "
            "Standard Flow habilitado.",
            "Pronto: um link para /oidc/authenticate/ dispara o login; "
            "request.user funciona normalmente depois disso.",
        ],
        "code_template": """# settings.py
INSTALLED_APPS = [
    ...,
    "mozilla_django_oidc",
]

AUTHENTICATION_BACKENDS = (
    "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)

OIDC_RP_CLIENT_ID = "__CLIENT_ID__"
OIDC_RP_CLIENT_SECRET = "__CLIENT_SECRET__"  # gerado ao criar o client no Keycloak
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_OP_AUTHORIZATION_ENDPOINT = "__AUTH_ENDPOINT__"
OIDC_OP_TOKEN_ENDPOINT = "__TOKEN_ENDPOINT__"
OIDC_OP_USER_ENDPOINT = "__USERINFO_ENDPOINT__"
OIDC_OP_JWKS_ENDPOINT = "__JWKS_URI__"
OIDC_RP_SCOPES = "__SCOPES_SPACE__"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# urls.py (raiz do projeto)
from django.urls import include, path

urlpatterns = [
    ...,
    path("oidc/", include("mozilla_django_oidc.urls")),
]

# Redirect URI a cadastrar no Keycloak (caminho fixo do mozilla-django-oidc):
# __REDIRECT_URI__
""",
    },
    "drf": {
        "label": "Django REST Framework (API — validação de token via JWKS)",
        "package": "PyJWT",
        "install_command": 'pip install "PyJWT[crypto]"',
        "default_redirect_path": "/auth/callback",
        "public_client": False,
        "steps": [
            'Instale o PyJWT com suporte a criptografia: pip install "PyJWT[crypto]".',
            "Este padrão NÃO faz o fluxo de login (redirect pro Keycloak) — "
            "pressupõe que outro sistema seu (um frontend, um BFF em Next.js/etc.) "
            "já cuida disso e te entrega o token pronto. A API aqui só VALIDA.",
            "Copie a função validate_keycloak_token abaixo — ela busca a chave "
            "pública certa no JWKS do Keycloak (cacheada em memória pelo PyJWKClient) "
            "e confere assinatura, issuer, audience e expiração.",
            "Plugue KeycloakBearerAuthentication em DEFAULT_AUTHENTICATION_CLASSES "
            "(settings.py) ou só nas views que precisam.",
            "Ajuste a linha marcada pra resolver seu usuário real a partir de "
            "claims['email']/claims['sub'] (criar na hora, se sua regra permitir).",
        ],
        "code_template": """# keycloak_auth.py
import jwt
from jwt import PyJWKClient

ISSUER = "__ISSUER__"
AUDIENCE = "__CLIENT_ID__"

_jwks_client = PyJWKClient("__JWKS_URI__")


def validate_keycloak_token(token: str) -> dict:
    \"\"\"Valida um access_token/id_token emitido pelo Keycloak.

    Levanta jwt.PyJWTError (ou subclasse) se assinatura, issuer, audience ou
    expiração forem inválidos — trate isso como 401 na sua view/middleware.
    \"\"\"
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"require": ["exp", "iat", "aud", "iss", "sub"]},
    )


# authentication.py — plugue em DEFAULT_AUTHENTICATION_CLASSES da DRF
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class KeycloakBearerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        token = header.removeprefix("Bearer ")
        try:
            claims = validate_keycloak_token(token)
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed(f"Token inválido: {exc}") from exc
        return (claims["sub"], claims)  # TODO: resolver seu User real aqui
""",
    },
    "nextjs": {
        "label": "Next.js (BFF, NextAuth.js)",
        "package": "next-auth",
        "install_command": "npm install next-auth",
        "default_redirect_path": "/api/auth/callback/keycloak",
        "public_client": False,
        "steps": [
            "Instale o pacote: npm install next-auth.",
            "Crie o arquivo de rota do NextAuth (App Router: "
            "app/api/auth/[...nextauth]/route.ts; Pages Router: "
            "pages/api/auth/[...nextauth].ts) com o provider Keycloak abaixo.",
            "Guarde o client secret em variável de ambiente "
            "(KEYCLOAK_CLIENT_SECRET), nunca no código.",
            "Peça pro time do PaperMoon cadastrar o client no seu realm com o "
            "Redirect URI mostrado acima — esse caminho é fixo, o NextAuth "
            "sempre usa /api/auth/callback/<provider>.",
            "Use signIn('keycloak') / useSession() normalmente nas suas páginas.",
        ],
        "code_template": """// app/api/auth/[...nextauth]/route.ts (App Router)
// ou pages/api/auth/[...nextauth].ts (Pages Router)
import NextAuth from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

export const authOptions = {
  providers: [
    KeycloakProvider({
      clientId: "__CLIENT_ID__",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET!, // gerado ao criar o client
      issuer: "__ISSUER__",
      authorization: { params: { scope: "__SCOPES_SPACE__" } },
    }),
  ],
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };

// .env.local
// KEYCLOAK_CLIENT_SECRET=__CLIENT_SECRET__

// Redirect URI a cadastrar no Keycloak (caminho fixo do NextAuth):
// __REDIRECT_URI__
""",
    },
    "js": {
        "label": "JavaScript puro (SPA, sem backend)",
        "package": "oidc-client-ts",
        "install_command": "npm install oidc-client-ts",
        "default_redirect_path": "/callback",
        "public_client": True,
        "steps": [
            "Instale o pacote: npm install oidc-client-ts.",
            "Configure o UserManager com os valores desta página.",
            "IMPORTANTE: cadastre o client no Keycloak como PÚBLICO "
            "('Client authentication: Off') — um app 100% front-end não tem "
            "como guardar um client_secret em segredo. O fluxo usa "
            "Authorization Code + PKCE, que é seguro mesmo sem secret.",
            "Chame userManager.signinRedirect() no clique do botão de login.",
            "Na rota de callback (a URL cadastrada acima), chame "
            "userManager.signinRedirectCallback() pra completar o login.",
        ],
        "code_template": """import { UserManager } from "oidc-client-ts";

const userManager = new UserManager({
  authority: "__ISSUER__",
  client_id: "__CLIENT_ID__",
  redirect_uri: "__REDIRECT_URI__",
  response_type: "code", // Authorization Code + PKCE — sem client_secret
  scope: "__SCOPES_SPACE__",
});

// Dispara o login (redireciona o navegador pro Keycloak)
document.getElementById("login-btn")?.addEventListener("click", () => {
  userManager.signinRedirect();
});

// Na página de callback (__REDIRECT_URI__), processa o retorno:
userManager.signinRedirectCallback().then((user) => {
  console.log("Logado:", user.profile);
  window.location.href = "/";
});
""",
    },
    "node": {
        "label": "Node.js (Express)",
        "package": "express-openid-connect",
        "install_command": "npm install express-openid-connect",
        "default_redirect_path": "/callback",
        "public_client": False,
        "steps": [
            "Instale o pacote: npm install express-openid-connect.",
            "Plugue o middleware auth() com os valores desta página.",
            "Defina SESSION_SECRET (qualquer string aleatória longa) e "
            "KEYCLOAK_CLIENT_SECRET (gerado ao criar o client) como variáveis "
            "de ambiente.",
            "Peça pro time do PaperMoon cadastrar o client no seu realm com o "
            "Redirect URI mostrado acima — caminho fixo do middleware.",
            "Use req.oidc.isAuthenticated() / req.oidc.user em qualquer rota.",
        ],
        "code_template": """const express = require("express");
const { auth } = require("express-openid-connect");

const app = express();

app.use(
  auth({
    authRequired: false,
    auth0Logout: false, // não é Auth0 — usa OIDC genérico
    baseURL: "__BASE_URL__",
    clientID: "__CLIENT_ID__",
    clientSecret: process.env.KEYCLOAK_CLIENT_SECRET, // gerado ao criar o client
    issuerBaseURL: "__ISSUER__",
    secret: process.env.SESSION_SECRET, // string aleatória longa, só sua
    authorizationParams: { response_type: "code", scope: "__SCOPES_SPACE__" },
  })
);

app.get("/", (req, res) => {
  res.send(req.oidc.isAuthenticated() ? `Logado como ${req.oidc.user.email}` : "Não logado");
});

app.listen(3000);

// .env
// SESSION_SECRET=qualquer-string-aleatoria-longa
// KEYCLOAK_CLIENT_SECRET=__CLIENT_SECRET__

// Redirect URI a cadastrar no Keycloak (caminho fixo do middleware):
// __REDIRECT_URI__
""",
    },
    "go": {
        "label": "Go",
        "package": "github.com/coreos/go-oidc/v3 + golang.org/x/oauth2",
        "install_command": "go get github.com/coreos/go-oidc/v3/oidc golang.org/x/oauth2",
        "default_redirect_path": "/auth/callback",
        "public_client": False,
        "steps": [
            "Instale as dependências: go get github.com/coreos/go-oidc/v3/oidc "
            "golang.org/x/oauth2.",
            "oidc.NewProvider já busca o discovery document sozinho — não "
            "precisa colar os endpoints um por um.",
            "Peça pro time do PaperMoon cadastrar o client no seu realm com o "
            "Redirect URI mostrado acima.",
            "Troque 'state-aleatorio' por um valor gerado por request "
            "(crypto/rand) e guardado em sessão/cookie — o exemplo abaixo "
            "simplifica isso de propósito pra caber num snippet.",
        ],
        "code_template": """package main

import (
	"context"
	"log"
	"net/http"

	"github.com/coreos/go-oidc/v3/oidc"
	"golang.org/x/oauth2"
)

func main() {
	ctx := context.Background()

	provider, err := oidc.NewProvider(ctx, "__ISSUER__")
	if err != nil {
		log.Fatal(err)
	}

	oauth2Config := oauth2.Config{
		ClientID:     "__CLIENT_ID__",
		ClientSecret: "__CLIENT_SECRET__", // use variável de ambiente em produção
		RedirectURL:  "__REDIRECT_URI__",
		Endpoint:     provider.Endpoint(),
		Scopes:       []string{__SCOPES_GO__},
	}
	verifier := provider.Verifier(&oidc.Config{ClientID: "__CLIENT_ID__"})

	http.HandleFunc("/login", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, oauth2Config.AuthCodeURL("state-aleatorio"), http.StatusFound)
	})

	http.HandleFunc("__REDIRECT_PATH__", func(w http.ResponseWriter, r *http.Request) {
		token, err := oauth2Config.Exchange(ctx, r.URL.Query().Get("code"))
		if err != nil {
			http.Error(w, "troca de código falhou: "+err.Error(), http.StatusBadRequest)
			return
		}
		rawIDToken, ok := token.Extra("id_token").(string)
		if !ok {
			http.Error(w, "resposta sem id_token", http.StatusInternalServerError)
			return
		}
		idToken, err := verifier.Verify(ctx, rawIDToken)
		if err != nil {
			http.Error(w, "id_token inválido: "+err.Error(), http.StatusUnauthorized)
			return
		}
		var claims struct {
			Email string `json:"email"`
		}
		idToken.Claims(&claims)
		w.Write([]byte("Logado como " + claims.Email))
	})

	log.Fatal(http.ListenAndServe(":8080", nil))
}
""",
    },
    "csharp": {
        "label": "C# (.NET / ASP.NET Core)",
        "package": "Microsoft.AspNetCore.Authentication.OpenIdConnect",
        "install_command": "dotnet add package Microsoft.AspNetCore.Authentication.OpenIdConnect",
        "default_redirect_path": "/signin-oidc",
        "public_client": False,
        "steps": [
            "Instale o pacote (já vem embutido no SDK do ASP.NET Core na "
            "maioria dos casos — o comando abaixo garante a versão certa): "
            "dotnet add package Microsoft.AspNetCore.Authentication.OpenIdConnect.",
            "Configure o middleware em Program.cs com os valores desta página.",
            "Guarde o client secret em user-secrets/variável de ambiente "
            "(Keycloak:ClientSecret), nunca em appsettings.json versionado.",
            "Peça pro time do PaperMoon cadastrar o client no seu realm com o "
            "Redirect URI mostrado acima — /signin-oidc é o CallbackPath "
            "padrão do middleware.",
            "Proteja endpoints com [Authorize] normalmente.",
        ],
        "code_template": """// Program.cs
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.OpenIdConnect;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddAuthentication(options =>
{
    options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
})
.AddCookie()
.AddOpenIdConnect(options =>
{
    options.Authority = "__ISSUER__";
    options.ClientId = "__CLIENT_ID__";
    options.ClientSecret = builder.Configuration["Keycloak:ClientSecret"]; // gerado ao criar o client
    options.ResponseType = "code";
    options.CallbackPath = "__REDIRECT_PATH__"; // caminho fixo padrão do middleware
    options.SaveTokens = true;
    options.Scope.Clear();
__SCOPES_CSHARP__
});

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapGet("/", (HttpContext ctx) => ctx.User.Identity!.IsAuthenticated
    ? $"Logado como {ctx.User.Identity!.Name}"
    : "Não logado");

app.Run();

// user-secrets (dotnet user-secrets set Keycloak:ClientSecret "...") — NUNCA em
// appsettings.json versionado:
// { "Keycloak": { "ClientSecret": "__CLIENT_SECRET__" } }

// Redirect URI a cadastrar no Keycloak (caminho fixo do middleware):
// __REDIRECT_URI__
""",
    },
}
