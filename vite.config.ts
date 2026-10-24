// Lovable's config already includes TanStack Start, React, Tailwind and Nitro.
// Only add the Vite dev-server proxy for our local FastAPI service.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    server: { entry: "server" },
  },
  vite: {
    server: {
      proxy: {
        "/api": "http://127.0.0.1:8000",
      },
    },
  },
});
