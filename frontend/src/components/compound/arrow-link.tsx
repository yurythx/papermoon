import Link, { type LinkProps } from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

type CommonProps = Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, "href" | "className" | "children">;

interface ArrowLinkProps extends CommonProps {
  /** Sem `href`, renderiza um <span> — uso dentro de um card que já é o link
   * (o pai precisa ter `className="group"` pra herdar o hover). Com `href`,
   * o próprio ArrowLink vira o elemento clicável. */
  href?: string;
  children: React.ReactNode;
  size?: "xs" | "sm" | "md";
  external?: boolean;
  className?: string;
}

const sizeClasses: Record<NonNullable<ArrowLinkProps["size"]>, string> = {
  xs: "text-[11px] gap-1",
  sm: "text-xs gap-1",
  md: "text-sm gap-1.5",
};

const iconSizes: Record<NonNullable<ArrowLinkProps["size"]>, number> = { xs: 10, sm: 11, md: 13 };

export function ArrowLink({ href, children, size = "sm", external = false, className, ...rest }: ArrowLinkProps) {
  const classes = cn(
    "inline-flex items-center font-semibold text-brand-accent transition-colors",
    sizeClasses[size],
    href ? "hover:underline group" : "group-hover:underline",
    className
  );

  const content = (
    <>
      {children}
      <ArrowRight size={iconSizes[size]} className="shrink-0 transition-transform duration-150 group-hover:translate-x-0.5" />
    </>
  );

  if (!href) {
    return (
      <span className={classes} {...(rest as React.HTMLAttributes<HTMLSpanElement>)}>
        {content}
      </span>
    );
  }

  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={classes} {...rest}>
        {content}
      </a>
    );
  }

  return (
    <Link href={href} className={classes} {...(rest as Omit<LinkProps, "href">)}>
      {content}
    </Link>
  );
}
