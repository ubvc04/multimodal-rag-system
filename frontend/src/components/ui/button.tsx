import * as React from "react";

import { cn } from "./utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant?: "primary" | "secondary" | "ghost";
	size?: "sm" | "md" | "lg";
}

const baseStyles = "inline-flex items-center justify-center rounded-full font-semibold transition";

const variantStyles: Record<NonNullable<ButtonProps["variant"]>, string> = {
	primary: "bg-ink text-white hover:opacity-90",
	secondary: "border border-black/10 bg-white text-ink hover:bg-black/5",
	ghost: "text-ink hover:bg-black/5",
};

const sizeStyles: Record<NonNullable<ButtonProps["size"]>, string> = {
	sm: "px-3 py-1.5 text-xs",
	md: "px-4 py-2 text-sm",
	lg: "px-5 py-3 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
	({ className, variant = "primary", size = "md", type = "button", ...props }, ref) => {
		return (
			<button
				ref={ref}
				type={type}
				className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
				{...props}
			/>
		);
	},
);

Button.displayName = "Button";
