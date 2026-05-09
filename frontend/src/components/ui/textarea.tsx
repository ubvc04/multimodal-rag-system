import * as React from "react";

import { cn } from "./utils";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => (
	<textarea
		ref={ref}
		className={cn(
			"w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-ember",
			className,
		)}
		{...props}
	/>
));

Textarea.displayName = "Textarea";
