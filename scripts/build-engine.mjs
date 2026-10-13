import {build} from 'vite';
await build({configFile:false,build:{ssr:'src/adapters/server-cli.ts',outDir:'backend',emptyOutDir:false,minify:false,rollupOptions:{output:{entryFileNames:'engine.mjs'}}}});
