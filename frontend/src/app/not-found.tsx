"use client";

import Link from "next/link";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0 px-6">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Logo */}
        <div className="flex justify-center">
          <div className="flex items-center gap-2.5">
            <PaperMoonMark idSuffix="404" size={32} />
            <span className="text-lg font-bold text-text-primary">PaperMoon</span>
          </div>
        </div>

        {/* 404 display */}
        <div className="relative">
          <p className="text-[120px] font-black leading-none bg-gradient-to-br from-brand-accent/30 to-text-secondary/20 bg-clip-text text-transparent select-none">
            404
          </p>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-48 h-48 bg-brand-accent/12 blur-3xl rounded-full" />
          </div>
        </div>

        {/* Message */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-text-primary">Página não encontrada</h1>
          <p className="text-sm text-text-secondary leading-relaxed">
            O endereço que você acessou não existe ou foi movido.
            Verifique a URL ou volte ao início.
          </p>
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/dashboard">
            <Button variant="primary" size="md">
              <Home size={14} className="mr-1.5" />
              Ir para o dashboard
            </Button>
          </Link>
          <Button variant="secondary" size="md" onClick={() => window.history.back()}>
            <ArrowLeft size={14} className="mr-1.5" />
            Voltar
          </Button>
        </div>

        <p className="text-xs text-text-tertiary">
          Se o problema persistir,{" "}
          <a href="mailto:suporte@papermoon.com.br" className="underline hover:text-text-secondary transition-colors">
            entre em contato com o suporte
          </a>
          .
        </p>
      </div>
    </div>
  );
}
