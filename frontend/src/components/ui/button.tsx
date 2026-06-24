"use client";

import { cn } from "@/lib/utils";
import { Spinner } from "./spinner";
import { type ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "upsell" | "warning";
type ButtonSize = "xs" | "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))] font-semibold hover:bg-brand-accent/90 shadow-glow-accent active:scale-[0.98]",
  secondary:
    "bg-surface-3 text-text-primary border border-border-default hover:bg-surface-4 hover:border-border-focus active:scale-[0.98]",
  ghost:
    "bg-transparent text-text-secondary hover:bg-surface-3 hover:text-text-primary active:scale-[0.98]",
  danger:
    "bg-danger text-[rgb(var(--papermoon-moonlight-fixed-rgb))] font-semibold hover:bg-danger-dark active:scale-[0.98]",
  upsell:
    "bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))] font-semibold hover:bg-brand-accent/90 shadow-glow-accent active:scale-[0.98]",
  warning:
    "bg-warning text-[rgb(var(--papermoon-midnight-fixed-rgb))] font-semibold hover:bg-warning-dark active:scale-[0.98]",
};

const sizeClasses: Record<ButtonSize, string> = {
  xs: "px-2.5 py-1 text-xs gap-1 rounded-sm",
  sm: "px-3 py-1.5 text-sm gap-1.5 rounded",
  md: "px-4 py-2 text-sm gap-2 rounded-md",
  lg: "px-5 py-2.5 text-base gap-2 rounded-md",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "secondary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-150 cursor-pointer select-none",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {loading ? (
          <Spinner size={size === "lg" ? "sm" : "xs"} />
        ) : leftIcon ? (
          <span className="shrink-0">{leftIcon}</span>
        ) : null}
        {children}
        {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
