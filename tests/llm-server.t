The physical model list exposes one shared agent model plus assistant and quality models.

  $ NO_COLOR=1 "$TESTDIR/../llm-server" list
  agent backend=vllm-mlx port=5413 model=mlx-community/Qwen3.6-35B-A3B-4bit
  assistant backend=vllm-mlx port=5413 model=mlx-community/gemma-4-26B-A4B-it-qat-4bit
  quality backend=vllm-mlx port=5413 model=mlx-community/Qwen3.8-27B-4bit

The agent launch uses one 64K-capable server with conservative cache memory and request-selectable thinking.

  $ mkdir "$CRAMTMP/bin"
  $ cat >"$CRAMTMP/bin/lsof" <<'EOF'
  > #!/bin/sh
  > exit 1
  > EOF
  $ chmod +x "$CRAMTMP/bin/lsof"
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/dry-state" -n start agent 2>&1
  + mkdir -p *dry-state (glob)
  + touch *dry-state/agent.log (glob)
  + vllm-mlx serve mlx-community/Qwen3.6-35B-A3B-4bit --served-model-name mlx-community/Qwen3.6-35B-A3B-4bit --host 127.0.0.1 --port 5413 --max-kv-size 65536 --cache-memory-mb 2048 --max-num-seqs 1 --default-chat-template-kwargs \{\"enable_thinking\":false\} --enable-auto-tool-choice --tool-call-parser qwen --reasoning-parser qwen3

The assistant and quality profiles select their model-specific parsers and context limits.

  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/dry-state" -n start assistant 2>&1 | tail -n 1
  + vllm-mlx serve mlx-community/gemma-4-26B-A4B-it-qat-4bit --served-model-name mlx-community/gemma-4-26B-A4B-it-qat-4bit --host 127.0.0.1 --port 5413 --mllm --max-kv-size 32768 --cache-memory-mb 2048 --max-num-seqs 1 --default-chat-template-kwargs \{\"enable_thinking\":false\} --enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/dry-state" -n start quality 2>&1 | tail -n 1
  + vllm-mlx serve mlx-community/Qwen3.8-27B-4bit --served-model-name mlx-community/Qwen3.8-27B-4bit --host 127.0.0.1 --port 5413 --mllm --max-kv-size 32768 --cache-memory-mb 2048 --max-num-seqs 1 --default-chat-template-kwargs \{\"enable_thinking\":false\} --enable-auto-tool-choice --tool-call-parser qwen --reasoning-parser qwen3

Starting every physical model at once is rejected.

  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/dry-state" -n start all 2>&1
  start requires one physical model; use switch to change models
  [1]

Switch starts the requested model when no managed server is active.

  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/dry-state" -n switch assistant 2>&1 | tail -n 1
  + vllm-mlx serve mlx-community/gemma-4-26B-A4B-it-qat-4bit --served-model-name mlx-community/gemma-4-26B-A4B-it-qat-4bit --host 127.0.0.1 --port 5413 --mllm --max-kv-size 32768 --cache-memory-mb 2048 --max-num-seqs 1 --default-chat-template-kwargs \{\"enable_thinking\":false\} --enable-auto-tool-choice --tool-call-parser gemma4 --reasoning-parser gemma4

Switch replaces a running managed profile and reports the other shared-port profiles as stopped.

  $ cat >"$CRAMTMP/bin/lsof" <<'EOF'
  > #!/bin/sh
  > if [ "${1:-}" = "-p" ]; then
  >     kill -0 "$2" 2>/dev/null
  >     exit
  > fi
  > if [ -f "$TEST_LISTENER_PID_FILE" ]; then
  >     pid=$(sed -n '1p' "$TEST_LISTENER_PID_FILE")
  >     if kill -0 "$pid" 2>/dev/null; then
  >         echo "$pid"
  >         exit 0
  >     fi
  > fi
  > exit 1
  > EOF
  $ cat >"$CRAMTMP/bin/vllm-mlx" <<'EOF'
  > #!/bin/sh
  > echo "$$" >"$TEST_LISTENER_PID_FILE"
  > exec sleep 300
  > EOF
  $ cat >"$CRAMTMP/bin/curl" <<'EOF'
  > #!/bin/sh
  > exit 0
  > EOF
  $ chmod +x "$CRAMTMP/bin/lsof" "$CRAMTMP/bin/vllm-mlx" "$CRAMTMP/bin/curl"
  $ export TEST_LISTENER_PID_FILE="$CRAMTMP/listener.pid"
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/state" start agent 2>&1 | sed -E 's/pid: [0-9]+/pid: PID/'
  agent ready (pid: PID, port: 5413)
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/state" switch assistant 2>&1 | sed -E 's/pid: [0-9]+/pid: PID/'
  agent stopped
  assistant ready (pid: PID, port: 5413)
  $ ret=0; output=$(PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/state" start quality 2>&1) || ret=$?
  $ printf '%s\nret=%s\n' "$output" "$ret" | sed -E 's/pid [0-9]+/pid PID/'
  assistant is running; use switch quality to change physical models
  ret=1
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/state" status 2>&1 | sed -E 's/pid=[0-9]+/pid=PID/'
  agent stopped port=5413 model=mlx-community/Qwen3.6-35B-A3B-4bit
  assistant running pid=PID port=5413 model=mlx-community/gemma-4-26B-A4B-it-qat-4bit
  quality stopped port=5413 model=mlx-community/Qwen3.8-27B-4bit
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/state" stop assistant 2>&1
  assistant stopped

Switching to a profile that is still initializing leaves the existing load alone.

  $ sleep 300 & initializing_pid=$!
  $ mkdir "$CRAMTMP/initializing-state"
  $ printf '%s\n' "$initializing_pid" >"$CRAMTMP/initializing-state/agent.pid"
  $ ps -p "$initializing_pid" -o lstart= | sed 's/^ *//;s/ *$//' >"$CRAMTMP/initializing-state/agent.start"
  $ PATH="$CRAMTMP/bin:$PATH" NO_COLOR=1 "$TESTDIR/../llm-server" -s "$CRAMTMP/initializing-state" switch agent 2>&1 | sed -E 's/pid: [0-9]+/pid: PID/'
  agent already initializing (pid: PID)
  $ kill "$initializing_pid"
