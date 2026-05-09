import * as React from "react";

import { cn } from "./utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => (
	<input
		ref={ref}
		className={cn(
			"w-full rounded-xl border border-black/10 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-ember",
			className,
		)}
		{...props}
	/>
));

Input.displayName = "Input";
