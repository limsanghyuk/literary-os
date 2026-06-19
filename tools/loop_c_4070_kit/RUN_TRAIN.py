# RUN_TRAIN.py - import bisect (0xC0000005 fix) + train, with Python-side tee to result.txt (live).
import os, sys, subprocess

LOG = open("result.txt", "w", encoding="utf-8", buffering=1)
def out(s=""):
    sys.stdout.write(s + "\n"); sys.stdout.flush(); LOG.write(s + "\n"); LOG.flush()

env = os.environ.copy()
env["KMP_DUPLICATE_LIB_OK"] = "TRUE"; env["MKL_THREADING_LAYER"] = "GNU"
env["MKL_SERVICE_FORCE_INTEL"] = "1"; env["OMP_NUM_THREADS"] = "1"; env["TOKENIZERS_PARALLELISM"] = "false"
if not env.get("HF_TOKEN") and os.path.exists("hf_token.txt"):
    env["HF_TOKEN"] = open("hf_token.txt", encoding="utf-8").read().strip()
out("HF_TOKEN set: %s" % bool(env.get("HF_TOKEN")))

out("=== cumulative import bisect (KMP + MKL=GNU + FORCE_INTEL + OMP=1) ===")
imports = [("torch","import torch"),("datasets","from datasets import Dataset"),
           ("transformers","from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig"),
           ("peft","from peft import LoraConfig, prepare_model_for_kbit_training"),
           ("trl","from trl import DPOConfig, DPOTrainer"),("bitsandbytes","import bitsandbytes")]
acc = []; bad = None
for name, stmt in imports:
    acc.append(stmt)
    r = subprocess.run([sys.executable,"-c","\n".join(acc)+"\nprint('CUM_OK')"], capture_output=True, text=True, env=env)
    ok = (r.returncode == 0 and "CUM_OK" in r.stdout)
    out("  +%-14s -> %s (rc=%s)" % (name, "OK" if ok else "CRASH", r.returncode))
    if not ok:
        out("---- stderr ----\n" + r.stderr[-1800:]); bad = name; break
if bad:
    out("\n>>> CONFLICT adding: %s. Paste to Claude." % bad); LOG.close(); sys.exit(1)

out("\nAll imports OK -> training\n")
p = subprocess.Popen([sys.executable, "-u", "train_4070.py"], env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in p.stdout:
    sys.stdout.write(line); sys.stdout.flush(); LOG.write(line); LOG.flush()
p.wait()
out("\n[train_4070 exit code = %s]" % p.returncode)
LOG.close()
