import type { Config } from "tailwindcss";

export default {
	content: ["./index.html", "./src/**/*.{ts,tsx}"],
	theme: {
		extend: {
			colors: {
				ink: "#111111",
				haze: "#f4f1ea",
				ember: "#f25f4c",
				moss: "#0f766e",
				sky: "#1f7a8c",
			},
			fontFamily: {
				display: ["\"Space Grotesk\"", "ui-sans-serif", "system-ui"],
				body: ["\"IBM Plex Sans\"", "ui-sans-serif", "system-ui"],
				mono: ["\"IBM Plex Mono\"", "ui-monospace", "SFMono-Regular"],
			},
			boxShadow: {
				glow: "0 0 30px rgba(242, 95, 76, 0.35)",
			},
			keyframes: {
				float: {
					"0%, 100%": { transform: "translateY(0px)" },
					"50%": { transform: "translateY(-6px)" },
				},
				fadeUp: {
					"0%": { opacity: "0", transform: "translateY(12px)" },
					"100%": { opacity: "1", transform: "translateY(0)" },
				},
				pulseCursor: {
					"0%, 100%": { opacity: "0.2" },
					"50%": { opacity: "1" },
				},
			},
			animation: {
				float: "float 6s ease-in-out infinite",
				fadeUp: "fadeUp 0.5s ease-out",
				pulseCursor: "pulseCursor 1s ease-in-out infinite",
			},
		},
	},
	plugins: [],
} satisfies Config;
