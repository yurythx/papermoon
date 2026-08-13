from __future__ import annotations

from django.db import models


class FeatureFlag(models.Model):
    """Liga/desliga uma feature pra todo mundo (enabled_globally) ou só pra
    um conjunto de customers (enabled_customers) — beta fechado, rollout
    manual, kill-switch de algo novo. Sem rollout por porcentagem de
    propósito: "todo mundo" ou "esses customers específicos" cobre o caso
    de uso real hoje, e isso já era um item avaliativo do roadmap (Fase 5).

    M2M em vez de FK em Customer porque a relação é fundamentalmente N flags
    x N customers, não um registro por tenant — não faz sentido reaproveitar
    o padrão repository/interfaces dos apps de negócio (customers, billing)
    pra uma leitura simples como essa.
    """

    key = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Identificador estável usado no código (ex: new_dashboard_widget).",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    enabled_globally = models.BooleanField(
        default=False,
        help_text="Liga pra todo mundo — ignora a lista de customers abaixo.",
    )
    enabled_customers = models.ManyToManyField(
        "customers.Customer",
        blank=True,
        related_name="enabled_flags",
        help_text="Customers com a flag ligada individualmente (irrelevante se enabled_globally=True).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_flags"
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key
