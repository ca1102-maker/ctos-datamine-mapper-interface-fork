#!/bin/bash

# 1. Enter the bound directory
cd /app

# 2. Configure npm to install global tools to a local folder
#    (This bypasses the read-only /usr/local error)
export NPM_CONFIG_PREFIX=/app/.npm-global
export PATH=/app/.npm-global/bin:$PATH

# 3. Install pnpm into that local folder
echo "Installing pnpm locally..."
npm install -g pnpm

# 4. Install project dependencies
echo "Installing dependencies..."
pnpm install

# 5. Start the server
echo "Starting Next.js on port 4000..."
export PORT=4000
pnpm run dev

