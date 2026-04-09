#!/usr/bin/env bash
# ============================================================================
# ollama_setup.sh — One-time Ollama setup for Anvil HPC (Purdue RCAC)
#
# Run this ONCE from your home directory on an Anvil compute node
# that has been allocated with at least 16 cores.
#
# Usage:
#   chmod +x ollama_setup.sh
#   ./ollama_setup.sh
#
# What it does:
#   1. Symlinks ~/.ollama → $SCRATCH/.ollama  (large model storage)
#   2. Starts ollama serve in the background
#   3. Pulls the LLM and embedding models you need
#   4. Creates thread-limited variants (64 threads) for Anvil
#   5. Verifies everything works with a test query
# ============================================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────
# Change these if you want different models or thread counts
LLM_BASE="qwen3-64"
LLM_THREADS=64
LLM_NAME="${LLM_BASE}-${LLM_THREADS}"       # e.g. qwen3-64

EMBED_BASE="nomic-embed-text"
EMBED_THREADS=64
EMBED_NAME="${EMBED_BASE}-${EMBED_THREADS}"  # e.g. nomic-embed-text-64

OLLAMA_BIN="/anvil/projects/tdm/bin/ollama"
# ────────────────────────────────────────────────────────────────────────

echo "========================================"
echo " Ollama One-Time Setup for Anvil"
echo "========================================"

# ── Step 1: Symlink .ollama to scratch ──────────────────────────────────
if [ -L "$HOME/.ollama" ]; then
    echo "[1/6] ~/.ollama symlink already exists → $(readlink $HOME/.ollama)"
elif [ -d "$HOME/.ollama" ]; then
    echo "[1/6] WARNING: ~/.ollama is a real directory. Moving to scratch..."
    mv "$HOME/.ollama" "$SCRATCH/.ollama"
    ln -s "$SCRATCH/.ollama" "$HOME/.ollama"
    echo "       Moved and symlinked."
else
    echo "[1/6] Creating symlink: ~/.ollama → \$SCRATCH/.ollama"
    mkdir -p "$SCRATCH/.ollama"
    ln -s "$SCRATCH/.ollama" "$HOME/.ollama"
fi

# ── Step 2: Start ollama serve ──────────────────────────────────────────
echo "[2/6] Starting ollama serve in background..."
# Kill any existing ollama serve for this user
pkill -u "$(whoami)" -f "ollama serve" 2>/dev/null || true
sleep 1

$OLLAMA_BIN serve &
OLLAMA_PID=$!
sleep 3

# Read the dynamically assigned host/port
if [ -f "/dev/shm/ollama.$(id -u)" ]; then
    OLLAMA_HOST=$(head -1 "/dev/shm/ollama.$(id -u)")
    export OLLAMA_HOST
    echo "       Ollama serving at: $OLLAMA_HOST"
else
    echo "ERROR: Could not find ollama host file at /dev/shm/ollama.$(id -u)"
    echo "       Make sure you're on a compute node with enough cores allocated."
    exit 1
fi

# ── Step 3: Pull base models ───────────────────────────────────────────
echo "[3/6] Pulling base LLM: $LLM_BASE ..."
$OLLAMA_BIN pull "$LLM_BASE"

echo "       Pulling embedding: $EMBED_BASE ..."
$OLLAMA_BIN pull "$EMBED_BASE"

# ── Step 4: Create thread-limited model variants ────────────────────────
echo "[4/6] Creating thread-limited LLM: $LLM_NAME (${LLM_THREADS} threads) ..."
cat > "$HOME/modelfile_llm" << EOF
FROM ${LLM_BASE}
PARAMETER num_thread ${LLM_THREADS}
EOF
$OLLAMA_BIN create "$LLM_NAME" -f "$HOME/modelfile_llm"

echo "       Creating thread-limited embedding: $EMBED_NAME (${EMBED_THREADS} threads) ..."
cat > "$HOME/modelfile_embed" << EOF
FROM ${EMBED_BASE}
PARAMETER num_thread ${EMBED_THREADS}
EOF
$OLLAMA_BIN create "$EMBED_NAME" -f "$HOME/modelfile_embed"

# Clean up modelfiles
rm -f "$HOME/modelfile_llm" "$HOME/modelfile_embed"

# ── Step 5: Verify ──────────────────────────────────────────────────────
echo "[5/6] Verifying with a test query..."
RESPONSE=$($OLLAMA_BIN run "$LLM_NAME" "Say 'hello' and nothing else." 2>&1 | head -5)
echo "       Model responded: $RESPONSE"

# ── Step 6: List installed models ───────────────────────────────────────
echo "[6/6] Installed models:"
$OLLAMA_BIN list

echo ""
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo ""
echo "Ollama is running (PID $OLLAMA_PID) at $OLLAMA_HOST"
echo ""
echo "Your models:"
echo "  LLM:       $LLM_NAME"
echo "  Embedding: $EMBED_NAME"
echo ""
echo "To use in Python:"
echo "  import os"
echo "  with open(f'/dev/shm/ollama.{os.getuid()}') as f:"
echo "      os.environ['OLLAMA_HOST'] = f.read().strip()"
echo "  from langchain_ollama import OllamaLLM, OllamaEmbeddings"
echo "  llm = OllamaLLM(model='$LLM_NAME')"
echo "  embed = OllamaEmbeddings(model='$EMBED_NAME')"
echo ""
echo "NOTE: ollama serve stops when this session ends."
echo "      Re-run 'ollama serve &' each time you start a new session."
echo "      You do NOT need to re-run this setup script — models persist."