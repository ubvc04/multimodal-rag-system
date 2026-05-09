import * as React from "react";

import { cn } from "./utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
	variant?: "neutral" | "success" | "warning" | "danger";
}

const variantStyles: Record<NonNullable<BadgeProps["variant"]>, string> = {
	neutral: "bg-black/10 text-ink",
	success: "bg-moss text-white",
	warning: "bg-amber-400 text-black",
	danger: "bg-ember text-white",
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
	({ className, variant = "neutral", ...props }, ref) => (
		<span
			ref={ref}
			className={cn(
				"inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold",
				variantStyles[variant],
				className,
			)}
			{...props}
		/>
	),
);

Badge.displayName = "Badge";
