import { cn } from "@/lib/utils";
import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, leftElement, rightElement, className, ...props }, ref) => {
    if (leftElement || rightElement) {
      return (
        <div className="relative flex items-center">
          {leftElement && (
            <span className="absolute left-3 text-text-tertiary pointer-events-none">
              {leftElement}
            </span>
          )}
          <input
            ref={ref}
            className={cn(
              "w-full bg-surface-2 border border-border-default rounded-md py-2 text-sm text-text-primary",
              "placeholder:text-text-tertiary",
              "focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus",
              "transition-colors duration-150",
              error && "border-danger focus:border-danger focus:ring-danger",
              leftElement ? "pl-9" : "pl-3",
              rightElement ? "pr-9" : "pr-3",
              className
            )}
            {...props}
          />
          {rightElement && (
            <span className="absolute right-3 text-text-tertiary">
              {rightElement}
            </span>
          )}
        </div>
      );
    }

    return (
      <input
        ref={ref}
        className={cn(
          "w-full bg-surface-2 border border-border-default rounded-md px-3 py-2 text-sm text-text-primary",
          "placeholder:text-text-tertiary",
          "focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus",
          "transition-colors duration-150",
          error && "border-danger focus:border-danger focus:ring-danger",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
