"""Load a Kev LoRA checkpoint with the backbone split across the visible GPUs (Kev-9B on 2 x T4).

Upstream Kev loads everything on one device (DecisionModel.__init__ ends with self.to(device)), so a 19 GB bf16 backbone
cannot go on a 16 GB T4. This mirrors Checkpoint._adapted_torch (dtype bf16, adapter merged, no fused kernels, no CUDA
graphs) but builds and merges on the CPU, then spreads the decoder layers over the GPUs with accelerate. The pointer head
stays on cuda:0; accelerate's hooks move the inputs to the first layer's device and bring the hidden states back to cuda:0.

Not covered by upstream tests: run `kev/run.py --smoke --shard` first and compare against a single-device run on a small
model (see the notebook's shard check). Imports are lazy so the module can be imported without torch.
"""


def load_sharded(ck, max_gib=13):
    import torch
    from accelerate import dispatch_model, infer_auto_device_map
    from kev.model import DecisionModel, load_tokenizer
    from peft import PeftModel

    n = torch.cuda.device_count()
    assert n >= 2, f"--shard needs at least 2 GPUs, found {n}"
    meta = ck.meta
    tok = load_tokenizer(meta.base, revision=meta.base_revision)
    if ck.full:
        raise ValueError("--shard is written for LoRA checkpoints (Kev-9B)")
    # CPU build in bf16 (host RAM about 19 GB; Kaggle gives about 29 GB), adapter merged there: W + delta in fp32, one rounding
    m = DecisionModel(meta.base, tok, "cpu", lora=None, revision=meta.base_revision, head_dim=meta.head_dim,
                      option_isolation=meta.option_isolation, dtype=torch.bfloat16)
    m.lm = PeftModel.from_pretrained(m.lm, ck.path, torch_device="cpu")
    m.lm = m.lm.merge_and_unload().to(torch.bfloat16)
    layer_cls = type(m.lm.layers[0]).__name__
    dmap = infer_auto_device_map(m.lm, max_memory={i: f"{max_gib}GiB" for i in range(n)}, no_split_module_classes=[layer_cls],
                                 dtype=torch.bfloat16)
    m.lm = dispatch_model(m.lm, device_map=dmap)
    m.head.to("cuda:0")
    m.device = "cuda:0"
    m.shard_map = {k: str(v) for k, v in dmap.items()}
    m.head.load_state_dict(meta.head)
    m.eval()
    m.head.temperature = meta.temperature
    return tok, m


def sync_all():
    import torch
    for i in range(torch.cuda.device_count()):
        torch.cuda.synchronize(i)


def peak_mem_mb():
    import torch
    return [round(torch.cuda.max_memory_allocated(i) / 1e6, 1) for i in range(torch.cuda.device_count())]
