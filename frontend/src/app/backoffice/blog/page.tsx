"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import Link from "next/link";
import { toast } from "sonner";
import { Plus, Newspaper } from "lucide-react";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/compound/status-badge";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { ErrorState } from "@/components/compound/error-state";
import { Pagination } from "@/components/compound/pagination";
import { BlogPostFormModal, type BlogPostCreateData } from "@/components/backoffice/blog-post-form-modal";

export default function BackofficeBlogPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-blog-posts", statusFilter, page],
    queryFn: () => adminService.listBlogPosts({ status: statusFilter || undefined, page }),
    staleTime: 30_000,
  });

  const createMutation = useMutation({
    mutationFn: (payload: BlogPostCreateData) => adminService.createBlogPost(payload),
    onSuccess: (post) => {
      qc.invalidateQueries({ queryKey: ["admin-blog-posts"] });
      setCreateOpen(false);
      toast.success("Post criado como rascunho.");
      window.location.href = `/backoffice/blog/${post.id}`;
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao criar post.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const posts = data?.results ?? [];
  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Blog"
        description="Posts de melhores práticas, implementações e novidades sobre os serviços"
        actions={
          <Button size="sm" variant="primary" onClick={() => setCreateOpen(true)}>
            <Plus size={14} className="mr-1.5" />
            Novo post
          </Button>
        }
      />

      <div className="flex gap-3 items-center flex-wrap">
        <label className="sr-only" htmlFor="blog-status-filter">Filtrar por status</label>
        <select
          id="blog-status-filter"
          aria-label="Filtrar por status"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os status</option>
          <option value="draft">Rascunho</option>
          <option value="published">Publicado</option>
        </select>
        {data && (
          <p className="text-sm text-text-tertiary">
            {data.count} post{data.count !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : isError ? (
          <ErrorState className="py-12" title="Não foi possível carregar os posts" onRetry={() => refetch()} />
        ) : posts.length === 0 ? (
          <EmptyState
            icon={Newspaper}
            title="Nenhum post encontrado"
            description="Crie o primeiro post do blog."
            action={{ label: "Novo post", onClick: () => setCreateOpen(true), variant: "primary" }}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Título</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Autor</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Publicado em</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {posts.map((post) => (
                  <tr key={post.id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-5 py-3">
                      <Link
                        href={`/backoffice/blog/${post.id}`}
                        className="font-medium text-text-primary hover:text-brand-accent transition-colors"
                      >
                        {post.title}
                      </Link>
                      <p className="text-xs text-text-tertiary font-mono mt-0.5">{post.slug}</p>
                    </td>
                    <td className="px-5 py-3 text-text-secondary">{post.author_name}</td>
                    <td className="px-5 py-3"><StatusBadge status={post.status} /></td>
                    <td className="px-5 py-3 text-text-secondary">
                      {post.published_at ? new Date(post.published_at).toLocaleDateString("pt-BR") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Pagination
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
        count={data?.count}
        countLabel={(c) => `${c} post${c !== 1 ? "s" : ""}`}
      />

      {createOpen && (
        <BlogPostFormModal
          loading={createMutation.isPending}
          onSubmit={(payload) => createMutation.mutate(payload)}
          onCancel={() => setCreateOpen(false)}
        />
      )}
    </div>
  );
}
