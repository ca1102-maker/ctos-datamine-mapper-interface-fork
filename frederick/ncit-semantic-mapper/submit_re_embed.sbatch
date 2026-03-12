#!/bin/bash -l

# --- SLURM Configuration ---
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -t 48:00:00
#SBATCH -A cis220051
#SBATCH -p shared
#SBATCH --output=re_embed_%j.out

# --- Cleanup Function ---
cleanup() {
    echo "--- CLEANUP ---"
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "Shutting down Ollama server (PID: $OLLAMA_PID)..."
        kill $OLLAMA_PID
        wait $OLLAMA_PID 2>/dev/null
    fi
    if [ ! -z "$NEO4J_PID" ]; then
        echo "Shutting down Neo4j server (PID: $NEO4J_PID)..."
        kill $NEO4J_PID
        wait $NEO4J_PID 2>/dev/null
    fi
    echo "Cleanup complete."
}
trap 'cleanup' EXIT TERM INT

# --- 1. Setup Environment ---
echo "--- SETUP ---"
echo "Job running on node: $(hostname)"
echo "Loading TDM environment modules..."
module use /anvil/projects/tdm/opt/core
module load tdm python/seminar r/seminar

echo "Activating Python virtual environment..."
source venv/bin/activate
cd $SLURM_SUBMIT_DIR
echo "Working directory: $(pwd)"

# --- 2. Start Servers in the Background ---
echo "--- STARTING SERVERS ---"

# Start Neo4j Server and redirect its output to neo4j.log
echo "Starting Neo4j server in the background (logging to neo4j.log)..."
apptainer exec \
  --bind ~/neo4j_home/data:/var/lib/neo4j/data \
  --bind ~/neo4j_home/conf:/var/lib/neo4j/conf \
  --bind ~/neo4j_logs:/var/lib/neo4j/logs \
  --bind ~/neo4j_run:/var/lib/neo4j/run \
  ~/corporate/frederick-llm/data/neo4j_5.20.0.sif \
  /var/lib/neo4j/bin/neo4j console > neo4j.log 2>&1 &
NEO4J_PID=$!
echo "Neo4j server started with PID: $NEO4J_PID"

# Start Ollama Server and redirect its output to ollama.log
echo "Starting Ollama server in the background (logging to ollama.log)..."
/anvil/projects/tdm/bin/ollama serve > ollama.log 2>&1 &
OLLAMA_PID=$!
echo "Ollama server started with PID: $OLLAMA_PID"

# --- 3. Wait for Servers to be Ready ---
echo "--- WAITING FOR SERVERS ---"
echo "Waiting for Neo4j (port 7687) to be available..."
while ! ss -tulpn | grep -q ":7687"
do
  echo -n "."
  sleep 2
done
echo " Neo4j is ready!"

echo "Waiting for Ollama (port 11434) to be available..."
while ! ss -tulpn | grep -q ":11434"
do
  echo -n "."
  sleep 1
done
echo " Ollama is ready!"

# --- 4. Run the Python Re-embedding Script ---
# Use the '-u' flag for unbuffered output to see progress in real-time.
echo "--- RUNNING PYTHON SCRIPT ---"
python -u re_embed_database.py

# --- 5. Exit ---
echo "--- JOB SCRIPT FINISHED ---"