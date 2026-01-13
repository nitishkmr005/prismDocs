## Source: Tensor Parallelism in Transformers_ A Hands-On Guide for Multi-GPU Inference _ Gian Paolo Santopaolo

Source: src/output/f_731f081f543b0beb72d078dc/source/Tensor Parallelism in Transformers_ A Hands-On Guide for Multi-GPU Inference _ Gian Paolo Santopaolo.pdf

Posted Dec 5, 2025 • Updated Dec 9, 2025

<!-- image -->

D=

## Gian Paolo Santopaolo

FP16 or FP32

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

HOME

- 

POSTS

- 

- PROJECTS 

- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

Home  ›  Tensor Parallelism in Transformers: A Hands-On Guide fo…

Search... 

## Tensor Parallelism in Transformers: A HandsOn Guide for Multi-GPU Inference ALI Au ALa Bus BI.s Bu CIa

ALe

ALI

ALa

Au

BLe

Posted Dec 5, 2025 ·  Updated Dec 9, 2025

FP16

FP16

Cu

Cu

FP16 or FP32

<!-- image -->

By Gian Paolo Santopaolo

Contents ›

Running a 70B parameter model on a single GPU? Not happening. Even the beefiest H100 with 80GB of VRAM canʼt hold Llama-2-70B in full precision. This is where Tensor

Parallelism (TP) comes in - it splits the modelʼs weight matrices across multiple GPUs so you can run models that would otherwise be impossible.

This guide is hands-on. Weʼll cover the theory just enough to understand whatʼs happening, then dive straight into code. By the end, youʼll have working scripts for running tensorparallel inference on RunPod and Lambda Cloud .

## Why Tensor Parallelism? The Memory Wall Problem

Modern LLMs are massive. Hereʼs a quick reality check:

| Model        | Parameters   | FP16 Memory   | FP32 Memory   |
|--------------|--------------|---------------|---------------|
| Llama-3-8B   | 8B           | ~16 GB        | ~32 GB        |
| Llama-3-70B  | 70B          | ~140 GB       | ~280 GB       |
| Llama-3-405B | 405B         | ~810 GB       | ~1.6 TB       |

A single A100 (80GB) can barely fit Llama-3-70B in FP16 - and thatʼs before accounting for KV cache, activations, and batch size overhead. For anything larger, you need to split the model across GPUs.

The Parallelism Zoo

<!-- image -->

15 min read

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

HOME

- 

POSTS

- 

PROJECTS

- 

ABOUT

- 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

There are several ways to distribute work across GPUs:

<!-- image -->

<!-- image -->

<!-- image -->

| Strategy             | Whatʼs Split    | Memory perGPU         | Communication       |
|----------------------|-----------------|-----------------------|---------------------|
| Data Parallelism     | Data batches    | Full model on eachGPU | Gradient sync after |
| Pipeline Parallelism | Layers          | Subset of layers      | Activations betwee  |
| Tensor Parallelism   | Weight matrices | Slice of every layer  | All-reduce within   |

## When to use Tensor Parallelism:

- Model doesnʼt fit on a single GPU
- You have fast interconnects (NVLink, InfiniBand)
- You want to minimize latency for inference

## How Tensor Parallelism Works

The core insight is simple: matrix multiplications can be parallelized by splitting the matrices .

## Column-Parallel Matrix Multiplication

Suppose you need to compute where is your input and is a weight matrix. If you split into column blocks: Y = XW X W W

<!-- formula-not-decoded -->

Then each GPU computes its slice independently:

<!-- formula-not-decoded -->

The outputs are naturally sharded by columns - no communication needed yet.

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

HOME

- 

POSTS

- 

- PROJECTS 

- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Row-Parallel Matrix Multiplication

Now suppose you have column-sharded input and you split into matching row blocks: X = [ X 1 ∣ X 2 ∣ … ∣ Xn ] W

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

Then you sum across GPUs (all-reduce) to get the final output:

<!-- image -->

This is the key operation that requires GPU-to-GPU communication.

## TP in Transformer Layers

Now letʼs see how these primitives apply to actual Transformer components.

## Attention Layer

Each GPU computes a partial result:

<!-- image -->

⌃

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

Tensor Parallelism in Transformers: A Hands-On Guide for Multi-GPU Inference | Gian Paolo Santopaolo

The attention mechanism has three projection matrices: , , (queries, keys, values) and an output projection . WQ WK WV WO

## Step 1: Split Q, K, V Projections (Column-Parallel)

Each GPU gets a subset of attention heads. If you have 32 heads and 4 GPUs, each GPU handles 8 heads.

<!-- image -->

```
 Text  1 2 3 4 GPU i computes (column slices of weight matrices): Q_i = X × W_Q[all_rows, columns_for_heads_i] K_i = X × W_K[all_rows, columns_for_heads_i] V_i = X × W_V[all_rows, columns_for_heads_i]
```

No communication needed - each GPU works independently.

## Step 2: Local Attention Computation

Since attention heads are independent, each GPU computes attention for its heads locally:

<!-- image -->

```
 Text  1 2 GPU i computes attention locally: attn_i = softmax(Q_i × K_i^T / √d_k) × V_i
```

Still no communication.

## Step 3: Output Projection (Row-Parallel)

The output projection is split by rows. Each GPU multiplies its attention output by its slice of , then we all-reduce: WO WO

```
 Text  1 2 3 4 5 GPU i computes partial output (row slice of W_O): partial_i = attn_i × W_O[rows_for_gpu_i, all_cols] All GPUs synchronize: output = AllReduce(partial_0 + partial_1 + ... + partial_n)
```

## One all-reduce per attention layer.

## Feed-Forward Network (FFN)

The FFN typically has two linear layers with an activation in between:

<!-- formula-not-decoded -->

## First Linear (Column-Parallel):

```
 Text  1 2 GPU i computes: hidden_i = GELU(x × W1[all_rows, cols_for_gpu_i])
```

## Second Linear (Row-Parallel):

 Text



⌃

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

```
partial_i = hidden_i × W2[rows_for_gpu_i, all_cols]
```

```
1 2 3 4 5 GPU i computes: All GPUs synchronize: output = AllReduce(sum of all partial_i)
```

One all-reduce per FFN layer.

## The Full Picture

<!-- image -->

Total communication per layer: 2 all-reduce operations.

## Constraints

TP comes with a few practical constraints:

1. TP size ≤ number of attention heads - you canʼt split a single head across GPUs
2. Heads must be divisible by TP size - each GPU needs an equal share
3. FFN hidden dimension must be divisible by TP size

For Llama-3-70B with 64 heads, valid TP sizes are: 1, 2, 4, 8, 16, 32, 64.

## Tensor Parallelism with HuggingFace Transformers

The good news: HuggingFace Transformers now has built-in TP support. For supported models, itʼs a one-liner.

## The 3-Line Solution

```
 Python  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 # tp_inference.py import torch from transformers import AutoModelForCausalLM, AutoTokenizer model = AutoModelForCausalLM.from_pretrained( "meta-llama/Meta-Llama-3-8B-Instruct", torch_dtype=torch.bfloat16, tp_plan="auto"  # <-- This enables tensor parallelism ) tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Ins prompt = "Explain tensor parallelism in one paragraph:" inputs = tokenizer(prompt, return_tensors="pt").to(model.device) outputs = model.generate(**inputs, max_new_tokens=100) print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Launching with torchrun

You canʼt just run python tp\_inference.py . You need to launch it with torchrun to spawn multiple processes:

<!-- image -->

<!-- image -->

⌃

<!-- image -->

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

HOME

- 

POSTS

- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

```
1 2 # Run on 4 GPUs
```

```
torchrun --nproc-per-node 4 tp_inference.py
```

Each process gets assigned to one GPU, and PyTorchʼs distributed runtime handles the communication.

## Supported Models

As of late 2025, HuggingFace supports TP for:

- Llama (all versions)
- Mistral
- Mixtral
- Qwen
- Gemma
- And more…

Check the modelʼs config for \_tp\_plan to see if itʼs supported:

```
 Python  1 2 3 from transformers import AutoConfig config = AutoConfig.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct") print(config._tp_plan)  # Shows the default TP plan
```

## Partitioning Strategies

Under the hood, HuggingFace uses these strategies:

| Strategy          | Description                               |
|-------------------|-------------------------------------------|
| colwise           | Column-parallel (for Q, K, V projections) |
| rowwise           | Row-parallel (for output projections)     |
| sequence_parallel | For LayerNorm, Dropout                    |
| replicate         | Keep full copy on eachGPU                 |

You can define a custom tp\_plan if needed:

```
 Python  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 tp_plan = { "model.layers.*.self_attn.q_proj": "colwise", "model.layers.*.self_attn.k_proj": "colwise", "model.layers.*.self_attn.v_proj": "colwise", "model.layers.*.self_attn.o_proj": "rowwise", "model.layers.*.mlp.gate_proj": "colwise", "model.layers.*.mlp.up_proj": "colwise", "model.layers.*.mlp.down_proj": "rowwise", } model = AutoModelForCausalLM.from_pretrained( "meta-llama/Meta-Llama-3-8B-Instruct", torch_dtype=torch.bfloat16, tp_plan=tp_plan ) ⌃
```

<!-- image -->

Pod name selective\_silver\_bug

Pod Template runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

GPU count

1

<!-- image -->

## Gian Paolo Santopaolo 3

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact Instance pricing Non-Interruptible

$5.96/hr

4

5

Save $3,842.96

Savings Plan

$5.08/hr

$22,184.36

Reserve a GPU for six months at a

discounted hourly cost.

$5.20/hr

- HOME 

Reserve a GPU for

Pay as you go, with three months at a

- POSTS 
- PROJECTS 

Encrypt volume

- ABOUT 

Start Jupyter notebook

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Hands-On: Running TP on RunPod

RunPod offers on-demand GPU pods with multi-GPU configurations. Letʼs run Llama-3-70B with tensor parallelism.

0 Edit

Change Template

## Step 1: Spin Up a Multi-GPU Pod

1.  Go to RunPod → Pods → Deploy
2.  Select a template with PyTorch (e.g., runpod/pytorch:2.1.0-py3.10-cuda11.8.0 ) 8
3.  Choose a multi-GPU configuration:
4. 4× A100 80GB for Llama-3-70B
5. 8× H100 for larger models or faster inference Plan

$3.80/hr

- Critical: Select instances with NVLink interconnect (e.g., SXM variants like A100SXM or H100-SXM), not PCIe. NVLink provides 600-900 GB/s bandwidth between GPUs, while PCIe is limited to ~64 GB/s. Without NVLink, the all-reduce operations in tensor parallelism become a severe bottleneck, negating most of the performance gains.  $42,748.80 Reserve a GPU for cost. instance.

Selecting a 4×A100 pod on RunPod - look for SXM variants with NVLink

<!-- image -->

## Step 2: Environment Setup

SSH into your pod and set up the environment:

<!-- image -->

<!-- image -->

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

HOME

<!-- image -->

POSTS

<!-- image -->

- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

```
1 2 3 4 5 6 7 8 # Update and install dependencies pip install --upgrade transformers accelerate torch # Verify GPU setup nvidia-smi # Check NCCL (the communication backend) python -c "import torch; print(f'CUDA available: {torch.cuda.is_available(
```

Expected output:

<!-- image -->

 Plaintext  CUDA available: True

```
GPU count: 4
```

## Step 3: Create the Inference Script

 Python

<!-- image -->



⌃

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

```
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 # runpod_tp_inference.py import os import torch from transformers import AutoModelForCausalLM, AutoTokenizer def main(): model_id = "meta-llama/Meta-Llama-3-70B-Instruct" # Load model with tensor parallelism model = AutoModelForCausalLM.from_pretrained( model_id, torch_dtype=torch.bfloat16, tp_plan="auto" ) tokenizer = AutoTokenizer.from_pretrained(model_id) tokenizer.pad_token = tokenizer.eos_token # Only rank 0 should print rank = int(os.environ.get("RANK", 0)) prompts = [ "What is tensor parallelism?", "Explain the difference between data and model parallelism.", ] for prompt in prompts: inputs = tokenizer(prompt, return_tensors="pt").to(model.device) with torch.no_grad(): outputs = model.generate( **inputs, max_new_tokens=200, do_sample=True, temperature=0.7, top_p=0.9, ) if rank == 0: response = tokenizer.decode(outputs[0], skip_special_tokens=T print(f"\n{'='*50}") print(f"Prompt: {prompt}") print(f"Response: {response}") print(f"{'='*50}\n") if __name__ == "__main__": main()
```

## Step 4: Launch with torchrun

```
 Shell  1 2 3 4 5 # Set your HuggingFace token for gated models export HF_TOKEN="your_token_here" # Launch on 4 GPUs torchrun --nproc-per-node 4 runpod_tp_inference.py
```

## Using vLLM with Tensor Parallelism on RunPod

For production inference, vLLM is often faster. RunPod has native vLLM support:

<!-- image -->

⌃



<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

```
1 2 3 4 5 6 7 8 9 # Install vLLM pip install vllm # Run with tensor parallelism python -m vllm.entrypoints.openai.api_server \ --model meta-llama/Meta-Llama-3-70B-Instruct \ --tensor-parallel-size 4 \ --dtype bfloat16 \ --port 8000
```

Or use RunPodʼs serverless vLLM workers which handle TP automatically:

```
 Python  1 2 3 4 5 6 # In your RunPod serverless handler handler_config = { "model_name": "meta-llama/Meta-Llama-3-70B-Instruct", "tensor_parallel_size": 4, "dtype": "bfloat16", }
```

## Hands-On: Running TP on Lambda Cloud

Lambda Cloud offers GPU instances with up to 8× H100s. The setup is similar but with some Lambda-specific details.

## Step 1: Launch a Multi-GPU Instance

1.  Go to Lambda Cloud → Instances → Launch
2.  Select instance type:
3. gpu\_8x\_h100\_sxm5 (8× H100 80GB) - best for large models
4. gpu\_4x\_a100\_80gb\_sxm4 (4× A100 80GB) - good for 70B models
5. Critical: Always choose SXM variants (e.g., sxm4 , sxm5 ) over PCIe. The 'SXM' designation indicates GPUs connected via NVLink with 600-900 GB/s inter-GPU bandwidth. PCIe-based instances share bandwidth through the CPUʼs PCIe lanes (~64 GB/s), creating a communication bottleneck that cripples tensor parallelism performance. 

LAUNCH INSTANCE

••--

Instance type

Region

-

Select instance type

1x GH200 (96 GB)|

ARM64 + H100

<!-- image -->

## Gian Paolo Santopaolo

208 VCPUs, 2900 GiB RAM, 22 TiB SSD

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

104 VCPUs, 900 GiB RAM, 11 TiB SSD

- HOME 

52 VCPUs, 450 GiB RAM, 5.5 TiB SSD

- POSTS 

1x H100 (80 GB SXM5)

- PROJECTS 
- ABOUT 

26 VCPUs, 200 GiB RAM, 1 TiB SSD

8x A100 (80 GB SXM4)

1000 AiD DANL DA TiD COD

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

Base image

-

Filesystem

<!-- image -->

Selecting a multi-GPU instance on Lambda Cloud - SXM variants have NVLink

## Step 2: SSH and Setup

<!-- image -->

## Step 3: Create the Inference Script

<!-- image -->

X

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

```
1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 # lambda_tp_inference.py import os import time import torch from transformers import AutoModelForCausalLM, AutoTokenizer def main(): model_id = "meta-llama/Meta-Llama-3-70B-Instruct" rank = int(os.environ.get("RANK", 0)) world_size = int(os.environ.get("WORLD_SIZE", 1)) if rank == 0: print(f"Loading {model_id} with TP across {world_size} GPUs...") start_time = time.time() model = AutoModelForCausalLM.from_pretrained( model_id, torch_dtype=torch.bfloat16, tp_plan="auto" ) if rank == 0: load_time = time.time() - start_time print(f"Model loaded in {load_time:.2f}s") tokenizer = AutoTokenizer.from_pretrained(model_id) tokenizer.pad_token = tokenizer.eos_token # Benchmark inference prompt = "Write a short poem about distributed computing:" inputs = tokenizer(prompt, return_tensors="pt").to(model.device) # Warmup with torch.no_grad(): _ = model.generate(**inputs, max_new_tokens=10) # Timed generation torch.cuda.synchronize() start = time.time() with torch.no_grad(): outputs = model.generate( **inputs, max_new_tokens=100, do_sample=False,  # Greedy for reproducibility ) torch.cuda.synchronize() gen_time = time.time() - start if rank == 0: response = tokenizer.decode(outputs[0], skip_special_tokens=True) tokens_generated = outputs.shape[1] - inputs["input_ids"].shape[1 tokens_per_sec = tokens_generated / gen_time print(f"\nPrompt: {prompt}") print(f"Response: {response}") print(f"\n--- Performance ---") print(f"Tokens generated: {tokens_generated}") print(f"Time: {gen_time:.2f}s") print(f"Throughput: {tokens_per_sec:.1f} tokens/sec") if __name__ == "__main__": main() ⌃
```

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Step 4: Launch with torchrun

```
 Shell  1 2 3 4 5 # For a single node with 4 GPUs torchrun --nproc-per-node 4 lambda_tp_inference.py # For 8 GPUs torchrun --nproc-per-node 8 lambda_tp_inference.py
```

## Multi-Node Setup on Lambda Cloud

If you need more than 8 GPUs, you can run across multiple nodes. Lambda instances support this via torchrun :

```
 Shell  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 # On Node 0 (master) torchrun \ --nproc-per-node 8 \ --nnodes 2 \ --node-rank 0 \ --master-addr <master-ip> \ --master-port 29500 \ lambda_tp_inference.py # On Node 1 (worker) torchrun \ --nproc-per-node 8 \ --nnodes 2 \ --node-rank 1 \ --master-addr <master-ip> \ --master-port 29500 \ lambda_tp_inference.py
```

This gives you 16 GPUs with tensor parallelism across nodes.

<!-- image -->

- Warning: Cross-node TP requires high-bandwidth interconnects (InfiniBand). Without it, communication overhead can kill performance. 

## Performance Benchmarks

Hereʼs what you can expect with tensor parallelism on different configurations:

## Llama-3-70B Inference Throughput

| Configuration   |   TP Size | Tokens/sec   | Memory/GPU   |
|-----------------|-----------|--------------|--------------|
| 1× H100 80GB    |         1 | OOM          | -            |
| 2× H100 80GB    |         2 | ~45          | ~38 GB       |
| 4× H100 80GB    |         4 | ~85          | ~20 GB       |
| 8× H100 80GB    |         8 | ~140         | ~12 GB       |

## Key Observations

1. Memory scales linearly - 4× GPUs = ~4× less memory per GPU

⌃

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 
2. Throughput scales sub-linearly - communication overhead increases with TP size
3. Sweet spot is often 4-8 GPUs - beyond that, communication dominates

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## What TP Doesn't Solve

Tensor parallelism is powerful, but it has limitations:

## 1. Scalability is Capped by Attention Heads

If your model has 64 attention heads, TP size canʼt exceed 64. In practice, you want TP size much smaller than head count to maintain efficiency.

## 2. Communication Overhead Across Nodes

TP requires frequent all-reduce operations (2 per layer). Within a node with NVLink (900 GB/s), this is fast. Across nodes with InfiniBand (~400 GB/s) or worse, Ethernet (~100 Gbps), it becomes a bottleneck.

Rule of thumb: Keep TP within a single node. Use Pipeline Parallelism (PP) across nodes.

## 3. Doesn't Help with Activation Memory

TP reduces weight memory but not activation memory. For very long sequences, you may still need gradient checkpointing or other techniques.

## When to Combine with Pipeline Parallelism

For truly massive models (400B+), combine TP and PP:

<!-- image -->

```
 Plaintext  Node 0: Layers 0-19  (TP=8 within node) Node 1: Layers 20-39 (TP=8 within node) Node 2: Layers 40-59 (TP=8 within node) Node 3: Layers 60-79 (TP=8 within node)
```

This gives you 32 GPUs total: 8-way TP × 4-way PP.

## Practical Takeaways

Decision Tree: Which Parallelism Strategy?

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

- HOME 
- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

HOME

- POSTS 
- PROJECTS 
- ABOUT 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Wrapping Up

Tensor parallelism is the go-to technique for running models that donʼt fit on a single GPU. The key ideas:

1. Split weight matrices across GPUs (column-wise for projections, row-wise for outputs)
2. All-reduce to aggregate partial results (2× per transformer layer)
3. Keep TP within a node for best performance
4. Use tp\_plan="auto" in HuggingFace for the easy path

For production inference, consider vLLM which has highly optimized TP implementations. For training, look into FSDP (Fully Sharded Data Parallel) which combines aspects of TP and data parallelism.

## References

- HuggingFace Distributed Inference Documentation
- Megatron-LM: Training Multi-Billion Parameter Language Models
- RunPod Multi-GPU Training Guide
- Lambda Labs Multi-Node PyTorch Guide
- vLLM Documentation
- PyTorch Distributed Overview
-  Tensor Parallelism, Tensor, Transformers, Multi-GPU, PyTorch, RunPod, Lambda Cloud

This post is licensed under CC BY 4.0 by the author.

## Further Reading

Dec 2, 2025

What Is a Tensor? A Practical Guide for AI Engineers

When dealing with deep learning, we quickly encounter the word tensor. But what exactly i…

Dec 18, 2025

PyTorch Training Loop: A Production-Ready Template for …

You can train almost anything in PyTorch with seven lines of code. The problem? Those seve…

OLDER

Share:

Dec 3, 2025

Why GPUs Love Tensors: Understanding Tensor Cores and…

Understanding why modern AI is so fast requires understanding the hardware that …

<!-- image -->

⌃

NEWER

<!-- image -->

<!-- image -->

<!-- image -->

  

<!-- image -->

<!-- image -->

## Gian Paolo Santopaolo

Hands-On ML Engineering Meets Strategic VisionBridging Code and Cloud to Drive Enterprise AI for RealWorld Impact

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

HOME

- 

POSTS

- 

PROJECTS

- 

ABOUT

- 

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

## Why GPUs Love Tensors: Understanding Tensor Cores and AI Acceleration

© 2025 Gian Paolo Santopaolo . Some rights reserved.

Choosing the Right Loss Function for your ML Problem

Opinions expressed in this website are my own.