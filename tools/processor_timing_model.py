#!/usr/bin/env python3
"""Lab 2 (OVS): cycle model of the 4-PE SIMT processor for the 49-8-3 network.

Runs three scheduling variants, a sigmoid LUT error check, and writes
processor_model_result.json with everything the report needs.
Standard library only.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "build" / "processor_model_result.json"

WARP = 32          # threads per warp
LANES = 4          # FP32 FMA lanes per PE
PES = 4
WARPS_PER_PE = 2
BUS_BYTES = 8      # bus matrix data width: 64 bits
BUS_OVERHEAD = 2   # arbitration + address phase, cycles
IN_BYTES = 49 * 2  # input image in BF16

# extra cycles after the issue cycles until the result can be read
TAIL = {"MOV": 0, "LD": 2, "STL": 2, "FMA": 3, "ADD": 3, "MUL": 3, "SHFL": 1,
        "CVT": 1, "SIG": 9, "CLS": 2}


def mask(a, b):
    return list(range(a, b + 1))


def make_program(pe, warp):
    """Instruction list of one warp. Warp `warp` of PE `pe` owns hidden neuron 2*pe+warp."""
    n = 2 * pe + warp
    p = [
        ("LD", "r1", [], mask(0, 31), "x[l]"),
        ("LD", "r2", [], mask(0, 31), f"W1[{n}][l]"),
        ("MUL", "r0", ["r2", "r1"], mask(0, 31), "acc = w*x"),
        ("LD", "r1", [], mask(0, 16), "x[l+32]"),
        ("LD", "r2", [], mask(0, 16), f"W1[{n}][l+32]"),
        ("FMA", "r0", ["r2", "r1", "r0"], mask(0, 16), "acc += w*x"),
    ]
    for off in (16, 8, 4, 2, 1):
        p.append(("SHFL", "r3", ["r0"], mask(0, off - 1), f"r3 = r0 of thread l+{off}"))
        p.append(("ADD", "r0", ["r0", "r3"], mask(0, off - 1), "acc += r3"))
    p += [
        ("SIG", "r4", ["r0"], [0], f"h{n} = sigmoid(acc)"),
        ("CVT", "r4", ["r4"], [0], "round h to BF16"),
        ("SHFL", "r4", ["r4"], mask(0, 2), "h to threads 0..2"),
        ("LD", "r5", [], mask(0, 2), f"W2[l][{n}]"),
        ("MUL", "r6", ["r5", "r4"], mask(0, 2), "c = W2*h"),
    ]
    if warp == 1:
        p += [("STL", None, ["r6"], mask(0, 2), "C1[l] = c"),
              ("BAR", None, [], [0], "both warps of the PE")]
    else:
        p += [("BAR", None, [], [0], "both warps of the PE"),
              ("LD", "r7", [], mask(0, 2), "r7 = C1[l]"),
              ("ADD", "r6", ["r6", "r7"], mask(0, 2), "q = c0 + c1"),
              ("STS", None, ["r6"], mask(0, 2), f"MBOX[{3 * pe}+l] = q")]
    if pe == 0 and warp == 0:
        p += [
            ("WAIT", None, [], [0], "4 triples in MBOX"),
            ("LDS", "r7", [], mask(0, 11), "r7 = MBOX[l]"),
            ("SHFL", "r8", ["r7"], mask(0, 5), "r8 = r7 of thread l+6"),
            ("ADD", "r7", ["r7", "r8"], mask(0, 5), ""),
            ("SHFL", "r8", ["r7"], mask(0, 2), "r8 = r7 of thread l+3"),
            ("ADD", "r7", ["r7", "r8"], mask(0, 2), "z_o"),
            ("SIG", "r9", ["r7"], mask(0, 2), "y_o = sigmoid(z_o)"),
            ("CLS", "r10", ["r9"], mask(0, 2), "class"),
            ("STIO", None, ["r9"], mask(0, 2), "OUT.y[l]"),
            ("STIO", None, ["r10"], [0], "OUT.class"),
        ]
    p.append(("END", None, [], [0], ""))
    return p


def portions(active):
    return len({t // LANES for t in active})


def issue_cycles(op, active, skip):
    if op in ("WAIT", "END", "BAR"):
        return 1
    if not skip:
        return WARP // LANES
    if op == "SIG":
        return len(active)          # one interpolator, one thread per cycle
    if op == "CLS":
        return 1
    return portions(active)


class Bus:
    def __init__(self):
        self.free = {"shared": 0, "io": 0}
        self.log = []

    def transfer(self, port, t_req, nbytes, who, label):
        start = max(t_req, self.free[port])
        end = start + BUS_OVERHEAD + math.ceil(nbytes / BUS_BYTES)
        self.free[port] = end
        self.log.append({"port": port, "who": who, "start": start, "end": end, "label": label})
        return end


def simulate(skip=True, policy="interleave"):
    """Cycle-by-cycle issue of all warps. Returns total time and the trace."""
    bus = Bus()
    t_bcast = bus.transfer("shared", 0, IN_BYTES, "IO", "x -> local SRAM of all PE")
    t_start = t_bcast + 1                                   # START strobe
    progs = {(p, w): make_program(p, w) for p in range(PES) for w in range(WARPS_PER_PE)}
    pc = {k: 0 for k in progs}
    ready = {k: {} for k in progs}                          # register -> cycle it can be read
    done = {k: None for k in progs}
    path_free = {p: t_start for p in range(PES)}
    last = {p: WARPS_PER_PE - 1 for p in range(PES)}
    mbox_count, mbox_full_at = 0, None
    bar_at = {k: [i for i, ins in enumerate(v) if ins[0] == "BAR"][0] for k, v in progs.items()}
    store_done = {k: 0 for k in progs}
    pending = []                                            # bus requests not yet granted
    trace, t_result = [], None
    t = t_start
    while t < 10000:
        for req in sorted([r for r in pending if r["t"] <= t], key=lambda r: (r["t"], r["pe"])):
            pending.remove(req)
            end = bus.transfer(req["port"], req["t"], req["bytes"], f"PE{req['pe']}", req["label"])
            if req["kind"] == "STS":
                mbox_count += 1
                if mbox_count == PES:
                    mbox_full_at = end
            elif req["kind"] == "LDS":
                ready[req["key"]][req["dst"]] = end + 1
            elif req["kind"] == "STIO" and req["label"] == "OUT.class":
                t_result = end
        for p in range(PES):
            if path_free[p] > t:
                continue
            order = [(last[p] + 1 + i) % WARPS_PER_PE for i in range(WARPS_PER_PE)]
            if policy == "sequential":
                order = list(range(WARPS_PER_PE))
            for w in order:
                key = (p, w)
                if done[key] is not None:
                    continue
                op, dst, srcs, active, note = progs[key][pc[key]]
                ok = all(ready[key].get(s, 0) <= t for s in srcs)
                if op == "WAIT":
                    ok = mbox_full_at is not None and mbox_full_at <= t
                if op == "BAR":
                    other = (p, 1 - w)
                    o_op = progs[other][pc[other]][0] if done[other] is None else "END"
                    arrived = o_op == "BAR" or pc[other] > bar_at[other]
                    ok = arrived and all(store_done[(p, v)] <= t for v in range(WARPS_PER_PE))
                if not ok:
                    if policy == "sequential" and op not in ("WAIT", "BAR"):
                        break                               # warp 0 stalls, warp 1 may not cut in
                    continue
                n_iss = issue_cycles(op, active, skip)
                if op == "STL":
                    store_done[key] = t + n_iss + TAIL["STL"]
                if dst and op not in ("LDS",):
                    ready[key][dst] = t + n_iss + TAIL.get(op, 0)
                if op in ("STS", "LDS", "STIO"):
                    nbytes = 4 * len(active)
                    port = "io" if op == "STIO" else "shared"
                    pending.append({"t": t + n_iss, "pe": p, "port": port, "bytes": nbytes,
                                    "kind": op, "key": key, "dst": dst, "label": note})
                    if op == "LDS":
                        ready[key][dst] = 10 ** 9
                trace.append({"pe": p, "warp": w, "op": op, "start": t, "issue_end": t + n_iss,
                              "active": len(active), "issue": n_iss, "note": note})
                path_free[p] = t + n_iss
                last[p] = w
                pc[key] += 1
                if op == "END":
                    done[key] = t + n_iss
                break
        if t_result is not None and all(v is not None for v in done.values()) and not pending:
            break
        t += 1
    return {"t_broadcast": t_bcast, "t_start": t_start, "t_result": t_result,
            "trace": trace, "bus": bus.log, "done": {f"PE{k[0]}W{k[1]}": v for k, v in done.items()}}


def pe_metrics(res):
    out = []
    for p in range(PES):
        rows = [r for r in res["trace"] if r["pe"] == p]
        busy = sum(r["issue"] for r in rows if r["op"] not in ("WAIT", "END", "BAR"))
        mac = sum(r["active"] for r in rows if r["op"] in ("FMA", "MUL"))
        flops_threads = sum(r["active"] for r in rows if r["op"] in ("FMA", "ADD", "MUL"))
        end = max(r["issue_end"] for r in rows)
        window = res["t_result"] - res["t_start"]
        out.append({"pe": p, "instr": len([r for r in rows if r["op"] != "END"]),
                    "issue_busy": busy, "end": end, "mac": mac, "arith_thread_ops": flops_threads,
                    "busy_share": busy / window, "lane_share": flops_threads / (LANES * window)})
    return out


def sigmoid_lut_check():
    """257-node LUT on [-8, 8] with step 1/16 and linear interpolation."""
    sig = lambda z: 1.0 / (1.0 + math.exp(-z))
    lut = [sig(-8 + k / 16) for k in range(257)]

    def pwl(z):
        if z <= -8:
            return 0.0
        if z >= 8:
            return 1.0
        u = (z + 8) * 16
        k = min(int(math.floor(u)), 255)
        a = u - k
        return lut[k] + a * (lut[k + 1] - lut[k])

    inner = max(abs(pwl(-8 + i / 4096) - sig(-8 + i / 4096)) for i in range(1, 16 * 4096))
    outer = sig(-8)
    bound = (1 / 16) ** 2 * (math.sqrt(3) / 18) / 8
    return {"max_err_inside": inner, "analytic_bound": bound, "saturation_err": outer}


def main():
    print("[1/4] variant A: no empty-portion skipping, warps interleaved")
    a = simulate(skip=False, policy="interleave")
    print(f"      result at cycle {a['t_result']}")
    print("[2/4] variant B: empty-portion skipping, warps interleaved (chosen design)")
    b = simulate(skip=True, policy="interleave")
    print(f"      result at cycle {b['t_result']}")
    print("[3/4] variant C: empty-portion skipping, warps one after another")
    c = simulate(skip=True, policy="sequential")
    print(f"      result at cycle {c['t_result']}")
    for m in pe_metrics(b):
        print(f"      PE{m['pe']}: {m['instr']} instr, issue busy {m['issue_busy']} cyc, "
              f"MAC {m['mac']}, issue share {m['busy_share']:.1%}, lane share {m['lane_share']:.1%}")
    print("[4/4] sigmoid LUT check")
    s = sigmoid_lut_check()
    print(f"      max error inside (-8,8): {s['max_err_inside']:.3e}, bound {s['analytic_bound']:.3e}, "
          f"saturation {s['saturation_err']:.3e}")
    out = {"A": {k: a[k] for k in ("t_broadcast", "t_start", "t_result")},
           "B": b, "C": {k: c[k] for k in ("t_broadcast", "t_start", "t_result")},
           "B_metrics": pe_metrics(b), "sigmoid": s,
           "programs": {f"PE{p}W{w}": make_program(p, w) for p in range(PES) for w in range(2)}}
    RESULT.parent.mkdir(exist_ok=True)
    with open(RESULT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"      written {RESULT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
