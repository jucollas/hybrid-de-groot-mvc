r""" Built by claude -> ENGINE_PATH=../engine.py python -m unittest -v test_engine
Regression tests for engine.py (constructive eps-reachability on strongly
connected graphs).

HOW TO RUN
    Put this file next to engine.py, then from that directory:
        python -m unittest -v test_engine        (standard library only)
        pytest -v test_engine.py                 (if you use pytest)
    Or point at the engine explicitly from anywhere:
        ENGINE_PATH=path/to/engine.py python -m unittest -v test_engine
    Optional knobs:
        ENGINE_RANDOM_N=200        instances per randomized test (default 200)
        ENGINE_TIMEOUT_SCALE=1.0   multiply every timeout (slow machines)

WHAT IS CHECKED
    Each test is named after the item of the code review it pins down
    (item01 ... item17 from the first review; item23 ... item25 from the
    second review, of the revised engine). Only outcomes are checked:
      * termination (every engine call runs in a separate process with a
        timeout, so an infinite loop is reported as a failure, not a freeze);
      * the reachable / unreachable verdict, compared with Theorem SCG
        eps-Reachability (non-puppet) and Corollary Puppet SCG
        eps-Reachability (puppet);
      * eps-consensus of the final opinions (strict: |x_v - tau| < eps);
      * validity of the returned schedule (format, and that replaying it under
        the hybrid DeGroot transition reproduces the result);
      * schedule length of level cloning against the bound of Arborescence
        Cloning.
    Deliberately NOT checked: min(x) <= tau <= max(x) after the two-agent
    game, and the V_u / V_v split of the third step of SCG Opinion Generation
    (both irrelevant for eps-reachability).

SECOND REVIEW (revised engine)
    item23  windows built with _get_low_and_high are clamped to [0, 1] and then
            tested strictly, so an opinion of exactly 0.0 or 1.0 is never
            "inside" (wrong verdicts, spurious ValueError, infinite loops).
    item24  the fixed cap of 10**5 iterations in _build_node_tao.
    item25  a cloning radius at or below floating-point resolution.
    _copy_opinion_all is called with whichever signature the engine has:
    (root, opinions, adj, radius) or the older (root, opinions, adj, center,
    radius).

ORDER OF FIXING
    If engine.py fails to import because of item 1, the worker loads it with
    deferred annotations so every other test still runs; only test_item01
    reports the import problem. Item 2 blocks every puppet instance and the
    "clone from a single node" branch, so tests for items 3, 11 and 12 can
    only pass once item 2 is fixed.
"""

import ast
import json
import math
import os
import queue
import random
import subprocess
import sys
import tempfile
import threading
import unittest
import warnings

THIS_FILE = os.path.abspath(__file__)
TIMEOUT_SCALE = float(os.environ.get("ENGINE_TIMEOUT_SCALE", "1.0"))
RANDOM_N = int(os.environ.get("ENGINE_RANDOM_N", "200"))


# --------------------------------------------------------------------------
# Locating engine.py
# --------------------------------------------------------------------------
_SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules",
              "build", "dist", "target", ".tox", ".mypy_cache", ".pytest_cache"}


def find_engine():
    env = os.environ.get("ENGINE_PATH")
    if env:
        path = os.path.abspath(env)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"ENGINE_PATH={env!r} is not a file")
        return path
    # 1) the directory of this file and its parents
    d = os.path.dirname(THIS_FILE)
    while True:
        cand = os.path.join(d, "engine.py")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # 2) a unique engine.py below the current working directory
    found = []
    for root, dirs, files in os.walk(os.getcwd()):
        dirs[:] = [x for x in dirs if x not in _SKIP_DIRS and not x.startswith(".")]
        if "engine.py" in files:
            found.append(os.path.join(root, "engine.py"))
    if len(found) == 1:
        return found[0]
    raise FileNotFoundError(
        "Could not locate engine.py unambiguously "
        f"(candidates: {found}). Set ENGINE_PATH=path/to/engine.py.")


# --------------------------------------------------------------------------
# Worker process: loads the engine and executes calls, one JSON line each
# --------------------------------------------------------------------------
def _load_engine_module(path, strict):
    """Execute engine.py as a module. With strict=False, a NameError raised
    while defining the module (item 1) is retried with deferred annotations,
    which keeps line numbers intact."""
    import __future__
    import types
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    flags_to_try = [0] if strict else [0, __future__.annotations.compiler_flag]
    last = None
    for flags in flags_to_try:
        mod = types.ModuleType("engine_under_test")
        mod.__file__ = path
        sys.modules["engine_under_test"] = mod
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                code = compile(src, path, "exec", flags=flags, dont_inherit=True)
            exec(code, mod.__dict__)
            return mod
        except NameError as e:
            last = e
    raise last


def _jsonable(obj):
    if isinstance(obj, (list, tuple)):
        return [_jsonable(o) for o in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    return obj


def _engine_frame(tb, path):
    import traceback
    frames = [f for f in traceback.extract_tb(tb) if os.path.abspath(f.filename) == path]
    if frames:
        f = frames[-1]
        return f"{f.name} (engine.py:{f.lineno})"
    return "outside engine.py"


def _build_graph(n, edges):
    edges = [(int(u), int(v), float(w)) for u, v, w in edges]
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    return edges, adj


def _worker_execute(mod, path, call):
    kind = call["kind"]
    if kind == "probe_import":
        import typing
        try:
            m = _load_engine_module(path, strict=True)
        except Exception as e:
            return {"status": "error", "type": type(e).__name__, "message": str(e),
                    "where": "module import"}
        bad = []
        for name, attr in vars(m.Engine).items():
            fn = attr.__func__ if isinstance(attr, (staticmethod, classmethod)) else attr
            if callable(fn) and hasattr(fn, "__annotations__"):
                try:
                    typing.get_type_hints(fn)
                except Exception as e:
                    bad.append(f"{name}: {type(e).__name__}: {e}")
        return {"status": "ok", "result": bad}

    engine = mod.Engine()
    if kind == "consensus":
        x = [float(t) for t in call["x"]]
        edges, adj = _build_graph(len(x), call["edges"])
        result = engine._compute_steps_consensus_python(x, edges, adj, call["tau"], call["eps"])
        if call.get("summary") and result is not None:      # very long schedules
            result = {"steps": len(result)}
        return {"status": "ok", "result": _jsonable(result), "x_after": x}
    if kind == "copy_all":
        x = [float(t) for t in call["x"]]
        edges, adj = _build_graph(len(x), call["edges"])
        import inspect
        if len(inspect.signature(engine._copy_opinion_all).parameters) >= 5:
            result = engine._copy_opinion_all(call["root"], x, adj, call["center"], call["radius"])
        else:   # revised signature: the ball is centred at the root's own opinion
            result = engine._copy_opinion_all(call["root"], x, adj, call["radius"])
        return {"status": "ok", "result": _jsonable(result), "x_after": x}
    if kind == "check_all":
        engine._check_all([float(t) for t in call["x"]], call["tau"], call["eps"])
        return {"status": "ok", "result": None}
    raise ValueError(f"unknown call kind {kind!r}")


def _worker_main(path):
    calls = json.loads(sys.stdin.read())
    mod = None
    for call in calls:
        try:
            if mod is None and call["kind"] != "probe_import":
                mod = _load_engine_module(path, strict=False)
            out = _worker_execute(mod, path, call)
        except Exception as e:
            out = {"status": "error", "type": type(e).__name__, "message": str(e)[:500],
                   "where": _engine_frame(e.__traceback__, path)}
        print(json.dumps(out), flush=True)


def run_calls(calls, timeout):
    """Run calls in a worker process; a call exceeding `timeout` seconds is
    reported as {"status": "timeout"} and the worker is restarted for the rest."""
    engine = find_engine()
    timeout = timeout * TIMEOUT_SCALE
    results, pending = [], list(calls)
    while pending:
        with tempfile.TemporaryFile(mode="w+") as err:
            proc = subprocess.Popen([sys.executable, THIS_FILE, "--worker", engine],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=err, text=True)
            proc.stdin.write(json.dumps(pending))
            proc.stdin.close()
            lines = queue.Queue()

            def pump():
                for line in proc.stdout:
                    lines.put(line)
                lines.put(None)

            threading.Thread(target=pump, daemon=True).start()
            consumed = 0
            for _ in pending:
                try:
                    line = lines.get(timeout=timeout)
                except queue.Empty:
                    proc.kill()
                    results.append({"status": "timeout", "seconds": timeout})
                    consumed += 1
                    break
                if line is None:
                    proc.wait()
                    err.seek(0)
                    results.append({"status": "worker-crash", "message": err.read()[-1500:]})
                    consumed += 1
                    break
                results.append(json.loads(line))
                consumed += 1
            proc.wait()
            proc.stdout.close()
        pending = pending[consumed:]
    return results


def run_one(call, timeout):
    return run_calls([call], timeout)[0]


# --------------------------------------------------------------------------
# Model and theory (definitions.tex, proofs_on_reachability.tex)
# --------------------------------------------------------------------------
def validate_instance(x, edges):
    """Hybrid DeGroot assumptions: no self-loops, incoming influence <= 1,
    influences in (0, 1]; plus strong connectivity (the engine's scope)."""
    n = len(x)
    insum = [0.0] * n
    for u, v, w in edges:
        assert u != v, "self-loop"
        assert 0 < w <= 1, f"influence {w} outside (0, 1]"
        insum[v] += w
    assert all(s <= 1 + 1e-12 for s in insum), f"incoming influence > 1: {insum}"
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]
    for u, v, _ in edges:
        adj[u].append(v)
        radj[v].append(u)
    for g in (adj, radj):
        seen, stack = {0}, [0]
        while stack:
            a = stack.pop()
            for b in g[a]:
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        assert len(seen) == n, "graph is not strongly connected"


def min_edge(edges):
    return min((w for _, _, w in edges), default=1.0)   # zeta(G) = 1 when E is empty


def theorem_reachable(x, edges, tau, eps):
    if min_edge(edges) >= 1.0:   # Corollary Puppet SCG eps-Reachability
        return any(abs(xi - tau) < eps for xi in x)
    return min(x) - eps < tau < max(x) + eps   # Theorem SCG eps-Reachability


def is_eps_consensus(x, tau, eps):
    return all(abs(xi - tau) < eps for xi in x)


def _is_edge(e):
    return isinstance(e, list) and len(e) in (2, 3) and isinstance(e[0], int)


def is_step(s):
    return isinstance(s, list) and all(_is_edge(e) for e in s)


def count_steps(schedule):
    """Number of time steps, tolerating extra nesting (so item 8 is measured
    independently of item 9)."""
    return sum(1 if is_step(s) else count_steps(s) for s in schedule)


def replay(x0, edges, schedule):
    """Apply the schedule with mu_{E'}(x)_v = (1 - sum I_uv) x_v + sum I_uv x_u.
    Steps may list edges as (u, v) or (u, v, w); w, if given, must equal I_uv."""
    weight = {(u, v): w for u, v, w in edges}
    x = list(x0)
    for t, step in enumerate(schedule):
        if not is_step(step):
            raise AssertionError(f"schedule[{t}] is not a list of edges (nested list of steps?)")
        seen = set()
        new = list(x)
        for e in step:
            u, v = e[0], e[1]
            if (u, v) not in weight:
                raise AssertionError(f"schedule[{t}] uses ({u},{v}), which is not an edge")
            if (u, v) in seen:
                raise AssertionError(f"schedule[{t}] lists ({u},{v}) twice")
            seen.add((u, v))
            if len(e) == 3 and abs(e[2] - weight[(u, v)]) > 1e-12:
                raise AssertionError(f"schedule[{t}] gives weight {e[2]} to ({u},{v}); I_uv = {weight[(u, v)]}")
            new[v] += weight[(u, v)] * (x[u] - x[v])
        x = new
    return x


def category(res):
    """Short failure label used to group randomized failures."""
    if res["status"] == "error":
        return f"{res['type']} in {res.get('where', '?')}"
    if res["status"] == "timeout":
        return "did not terminate"
    return res["status"]


def describe(res):
    if res["status"] == "error":
        return f"{res['type']} in {res.get('where', '?')}: {res['message']}"
    if res["status"] == "timeout":
        return f"did not terminate within {res['seconds']:.0f} s"
    if res["status"] == "worker-crash":
        return f"worker crashed: {res['message']}"
    return "ok"


# --------------------------------------------------------------------------
# Fixed instances
# --------------------------------------------------------------------------
def cycle(n, w):
    return [(i, (i + 1) % n, w) for i in range(n)]


TWO_NODE_HALF = [(0, 1, 0.5), (1, 0, 0.5)]

# Instance on which the predicted side of u (L211-212) is wrong; the pair then
# settles at 0.87053 with tau = 0.88203, eps = 0.01 (found by random search).
MISPREDICTION = dict(
    edges=[(3, 1, 0.2897621429181283), (6, 1, 0.35603136752395487), (5, 7, 0.3112397980390314),
           (0, 6, 0.4367374388966127), (3, 0, 0.4733604591328567), (7, 3, 0.4714467543905419),
           (1, 4, 0.3355007744161565), (4, 2, 0.032744639135705265), (6, 3, 0.21906456749572523),
           (0, 2, 0.44250345170047317), (2, 5, 0.5344716747032425), (5, 2, 0.34484518635124056)],
    x=[0.19180306385632173, 0.13013490305034947, 0.6766584956327384, 0.95948433853464,
       0.24858665831156102, 0.3679028177209237, 0.8236720221600523, 0.9725239399140262],
    tau=0.8820259764412312, eps=0.01)

# A small instance on which the current engine runs to completion.
SCHEDULE_INSTANCE = dict(edges=[(0, 1, 0.3), (1, 2, 0.6), (2, 0, 0.7), (0, 2, 0.3)],
                         x=[0.1, 0.9, 0.4], tau=0.5, eps=0.05)


def random_instance(rng, opinion=None):
    """opinion: optional sampler rng -> float (default: uniform on [0, 1))."""
    n = rng.randint(3, 8)
    perm = list(range(n))
    rng.shuffle(perm)
    es = set((perm[i], perm[(i + 1) % n]) for i in range(n))
    for _ in range(rng.randint(0, 2 * n)):
        a, b = rng.sample(range(n), 2)
        es.add((a, b))
    es = sorted(es)
    raw = {e: rng.random() + 0.05 for e in es}
    insum = {}
    for (a, b), w in raw.items():
        insum[b] = insum.get(b, 0.0) + w
    cap = {b: rng.uniform(0.3, 1.0) for b in range(n)}
    edges = [(a, b, raw[(a, b)] / insum[b] * cap[b]) for (a, b) in es]
    x = [opinion(rng) if opinion else rng.random() for _ in range(n)]
    eps = rng.choice([0.05, 0.02, 0.01])
    return x, edges, eps


def binary_opinion(rng):
    return float(rng.random() < 0.5)


def grid_opinion(rng):
    return rng.choice([0.0, 0.25, 0.5, 0.75, 1.0])


def check_against_theorem(inst, res):
    """Failure label for one randomized instance, or None if it is fine."""
    x, edges, tau, eps = inst
    if res["status"] != "ok":
        return category(res)
    expected = theorem_reachable(x, edges, tau, eps)
    if expected and res["result"] is None:
        return "returned None for a reachable tau"
    if not expected and res["result"] is not None:
        return "returned a schedule for an unreachable tau"
    if expected:
        if not is_eps_consensus(res["x_after"], tau, eps):
            return "final state is not eps-consensus"
        try:
            final = replay(x, edges, res["result"])
        except AssertionError as e:
            return "invalid schedule: " + str(e).split(",")[0][:50]
        if not is_eps_consensus(final, tau, eps) or \
                max(abs(a - b) for a, b in zip(final, res["x_after"])) > 1e-9:
            return "replaying the schedule does not reproduce the final state"
    return None


# --------------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------------
class EngineTestCase(unittest.TestCase):
    maxDiff = None

    def consensus(self, x, edges, tau, eps, timeout=10):
        validate_instance(x, edges)
        return run_one(dict(kind="consensus", x=x, edges=edges, tau=tau, eps=eps), timeout)

    def assertReachedConsensus(self, res, x, edges, tau, eps):
        self.assertEqual(res["status"], "ok", describe(res))
        self.assertIsNotNone(res["result"], f"returned None, but tau={tau} is eps-reachable")
        self.assertTrue(is_eps_consensus(res["x_after"], tau, eps),
                        f"final opinions {res['x_after']} are not eps-consensus at {tau} (eps={eps})")

    def assertUnreachable(self, res, tau):
        self.assertEqual(res["status"], "ok", describe(res))
        self.assertIsNone(res["result"], f"returned a schedule, but tau={tau} is not eps-reachable")


class TestItem01Import(EngineTestCase):
    def test_item01_module_imports_and_annotations_resolve(self):
        """L281: `function[float, float]` is undefined. On Python <= 3.13 the
        module does not import; on 3.14 it imports but typing.get_type_hints fails."""
        res = run_one(dict(kind="probe_import"), timeout=20)
        self.assertEqual(res["status"], "ok", describe(res))
        self.assertEqual(res["result"], [], "unresolvable annotations: " + "; ".join(res["result"]))


class TestVerdicts(EngineTestCase):
    def test_item02_puppet_reachable(self):
        """L35-37: @staticmethod with a `self` parameter shifts the arguments."""
        edges = cycle(3, 1.0)
        x, tau, eps = [0.1, 0.5, 0.9], 0.5, 0.1
        self.assertReachedConsensus(self.consensus(x, edges, tau, eps), x, edges, tau, eps)

    def test_item02_puppet_unreachable(self):
        res = self.consensus([0.1, 0.3, 0.9], cycle(3, 1.0), 0.6, 0.1)
        self.assertUnreachable(res, 0.6)

    def test_item03_tau_between_min_minus_eps_and_min_minus_half_eps(self):
        """L360-361, L374: outer bounds use eps/2 instead of eps.
        Needs item 2 fixed (single-node cloning branch)."""
        x, eps, tau = [0.5, 0.625], 0.25, 0.3125          # tau in (0.25, 0.375)
        self.assertReachedConsensus(self.consensus(x, TWO_NODE_HALF, tau, eps), x, TWO_NODE_HALF, tau, eps)

    def test_item03_tau_between_max_plus_half_eps_and_max_plus_eps(self):
        x, eps, tau = [0.5, 0.625], 0.25, 0.8125          # tau in (0.75, 0.875)
        self.assertReachedConsensus(self.consensus(x, TWO_NODE_HALF, tau, eps), x, TWO_NODE_HALF, tau, eps)

    def test_item11_puppet_tau_exactly_eps_away_is_unreachable(self):
        """Closed tests (L50, L326) accept |x_u - tau| = eps; the thesis uses <.
        Needs item 2 fixed."""
        res = self.consensus([0.5, 1.0], cycle(2, 1.0), 0.25, 0.25)
        self.assertUnreachable(res, 0.25)

    def test_item11_nonpuppet_tau_exactly_eps_outside_range_is_unreachable(self):
        """Passes today; guards the fix of item 3 (must stay strict, otherwise
        the cloning radius becomes 0 and level cloning never stops)."""
        for x, tau in (([0.5, 0.625], 0.25), ([0.375, 0.5], 0.75)):
            with self.subTest(x=x, tau=tau):
                self.assertUnreachable(self.consensus(x, TWO_NODE_HALF, tau, 0.25), tau)

    def test_item11_check_all_is_strict(self):
        """L326: _check_all must reject |x_v - tau| = eps."""
        res = run_one(dict(kind="check_all", x=[0.5], tau=0.25, eps=0.25), timeout=10)
        self.assertEqual(res.get("type"), "ValueError",
                         "_check_all accepted an opinion exactly eps away from tau")

    def test_item12_single_node_graph(self):
        """L353-354: E empty means zeta(G) = 1 (puppet), not a crash. Needs item 2 fixed."""
        with self.subTest(case="reachable"):
            self.assertReachedConsensus(self.consensus([0.5], [], 0.5, 0.1), [0.5], [], 0.5, 0.1)
        with self.subTest(case="unreachable"):
            self.assertUnreachable(self.consensus([0.5], [], 0.9, 0.1), 0.9)


class TestGeneration(EngineTestCase):
    def test_item04_path_from_omega_to_u_must_pass_through_v(self):
        """L309: _find_path returns [] (not None), so the fallback to omega -> v
        never runs and _copy_opinion_path([]) raises IndexError at L171.
        Here alpha = (0,1), omega = 2, and every 2 -> 0 path passes through 1."""
        edges = [(0, 1, 0.3), (1, 2, 0.9), (2, 1, 0.6), (1, 0, 0.9)]
        x, tau, eps = [0.9, 0.8, 0.0], 0.5, 0.1
        self.assertReachedConsensus(self.consensus(x, edges, tau, eps), x, edges, tau, eps)

    def test_item05_side_misprediction_instance(self):
        """L211-212: the side of u is predicted with x_v instead of the cloned x_w;
        on this instance u ends 0.0115 from tau (eps = 0.01) and cloning loops."""
        inst = MISPREDICTION
        res = self.consensus(inst["x"], inst["edges"], inst["tau"], inst["eps"], timeout=20)
        self.assertReachedConsensus(res, inst["x"], inst["edges"], inst["tau"], inst["eps"])

    def test_item06_small_min_edge_needs_more_than_1000_iterations(self):
        """L187: timeout=1000 with no check. With I = 0.001 the proof's y_o is ~5300."""
        edges = [(0, 1, 0.001), (1, 0, 0.001)]
        x, tau, eps = [0.0, 1.0], 0.5, 0.02
        res = self.consensus(x, edges, tau, eps, timeout=20)
        self.assertReachedConsensus(res, x, edges, tau, eps)

    def test_item07_cloning_with_nonpositive_radius_terminates(self):
        """L378-379 / L99-104: with radius <= 0 the target ball is empty and the
        loop at L101 never ends. Defensive: if you validate the radius before
        calling _copy_opinion_all instead of inside it, delete this test."""
        res = run_one(dict(kind="copy_all", root=0, x=[0.3, 1.0], edges=TWO_NODE_HALF,
                           center=0.3, radius=-0.01), timeout=10)
        self.assertNotEqual(res["status"], "timeout", describe(res))


class TestCloningComplexity(EngineTestCase):
    def test_item08_level_cloning_meets_arborescence_cloning_bound(self):
        """L99-104, L149: stopping when a node is within gamma of the ROOT makes
        the slack decay like p^depth, so steps grow quadratically in depth and
        eventually stall one ulp outside the ball.
        Bound used: the construction in the proof of Arborescence Cloning,
        (|V_a| - 1) * ceil(log_{1-zeta}(lambda/|V_a|)) steps, plus one step per
        level of slack for rounding / strict-vs-closed conventions.
        Instance: path 0 -> 1 -> ... -> n-1 (plus back edge for strong
        connectivity), root at 0.3, every other node at 1.0, lambda = 0.1."""
        cases = [(0.5, 10), (0.5, 40), (0.2, 20)]
        calls, bounds = [], []
        lam, center = 0.1, 0.3
        for p, n in cases:
            edges = [(i, i + 1, p) for i in range(n - 1)] + [(n - 1, 0, p)]
            x = [center] + [1.0] * (n - 1)
            validate_instance(x, edges)
            calls.append(dict(kind="copy_all", root=0, x=x, edges=edges, center=center, radius=lam))
            bounds.append((n - 1) * (math.ceil(math.log(lam / n, 1 - p)) + 1))
        results = run_calls(calls, timeout=15)
        for (p, n), bound, res in zip(cases, bounds, results):
            with self.subTest(p=p, n=n):
                self.assertEqual(res["status"], "ok", describe(res))
                self.assertTrue(is_eps_consensus(res["x_after"], center, lam),
                                "not every node ended within lambda of the root")
                steps = count_steps(res["result"])
                self.assertLessEqual(steps, bound, f"{steps} time steps; Arborescence Cloning needs at most {bound}")


class TestSchedule(EngineTestCase):
    def run_instance(self):
        inst = SCHEDULE_INSTANCE
        res = self.consensus(inst["x"], inst["edges"], inst["tau"], inst["eps"])
        self.assertEqual(res["status"], "ok", describe(res))
        self.assertIsNotNone(res["result"])
        return inst, res

    def test_item09_schedule_is_a_flat_list_of_time_steps(self):
        """L153: ans.append(steps) nests a whole BFS level into one element."""
        _, res = self.run_instance()
        nested = [t for t, s in enumerate(res["result"]) if not is_step(s)]
        self.assertEqual(nested, [], f"elements {nested} are lists of time steps, not time steps")

    def test_item10_every_edge_is_a_weighted_triple(self):
        """Docstring L344 promises [(u, v, w), ...]; L177, L219, L224, L226,
        L229, L235 emit (u, v) pairs."""
        inst, res = self.run_instance()
        weight = {(u, v): w for u, v, w in inst["edges"]}
        bad = []
        for t, s in enumerate(res["result"]):
            for e in (s if is_step(s) else []):
                if len(e) != 3 or abs(e[2] - weight.get((e[0], e[1]), float("nan"))) > 1e-12:
                    bad.append((t, e))
        self.assertEqual(bad[:5], [], f"{len(bad)} edges are not (u, v, I_uv) triples; first ones shown")

    def test_item09_10_replaying_the_schedule_reaches_consensus(self):
        """The certificate _check_all (L382) does not provide: replay the
        returned schedule from the initial opinions under hybrid DeGroot and
        compare with the engine's own final state. Pairs (u, v) are tolerated
        here so this test isolates item 9 from item 10."""
        inst, res = self.run_instance()
        final = replay(inst["x"], inst["edges"], res["result"])
        self.assertTrue(is_eps_consensus(final, inst["tau"], inst["eps"]),
                        f"replayed state {final} is not eps-consensus")
        for a, b in zip(final, res["x_after"]):
            self.assertAlmostEqual(a, b, places=9)


class TestRandomInstances(EngineTestCase):
    def run_batch(self, instances, check):
        calls = [dict(kind="consensus", x=x, edges=e, tau=t, eps=eps) for x, e, t, eps in instances]
        results = run_calls(calls, timeout=10)
        failures = {}
        for inst, res in zip(instances, results):
            category = check(inst, res)
            if category:
                failures.setdefault(category, []).append(inst)
        if failures:
            lines = [f"{len(v)} x {k}" for k, v in sorted(failures.items(), key=lambda kv: -len(kv[1]))]
            examples = [f"  {k}:\n    x={v[0][0]!r}\n    edges={v[0][1]!r}\n    tau={v[0][2]!r} eps={v[0][3]!r}"
                        for k, v in failures.items()]
            self.fail(f"{sum(len(v) for v in failures.values())} of {len(instances)} instances failed:\n  "
                      + "\n  ".join(lines) + "\nOne example per category:\n" + "\n".join(examples))

    def test_items04_to_07_random_generation_range(self):
        """tau in [min x + eps/2, max x - eps/2] (the two-agent game branch).
        Every instance must terminate with eps-consensus."""
        rng = random.Random(2026)
        instances = []
        while len(instances) < RANDOM_N:
            x, edges, eps = random_instance(rng)
            lo, hi = min(x) + eps / 2, max(x) - eps / 2
            if lo <= hi:
                instances.append((x, edges, rng.uniform(lo, hi), eps))

        self.run_batch(instances, check_against_theorem)

    def test_items02_03_11_random_verdicts_near_the_boundaries(self):
        """tau drawn near min x - eps, max x + eps and in between; the verdict
        must match Theorem SCG eps-Reachability, and reachable instances must end
        in eps-consensus."""
        rng = random.Random(1789)
        instances = []
        for k in range(RANDOM_N):
            x, edges, eps = random_instance(rng)
            mode = k % 3
            if mode == 0:
                tau = min(x) + eps * rng.uniform(-1.5, 0.75)
            elif mode == 1:
                tau = max(x) + eps * rng.uniform(-0.75, 1.5)
            else:
                tau = rng.uniform(min(x), max(x))
            instances.append((x, edges, min(1.0, max(0.0, tau)), eps))

        self.run_batch(instances, check_against_theorem)

    def test_item23_random_binary_and_grid_opinions(self):
        """Opinions drawn from {0, 1} and {0, .25, .5, .75, 1} (the usual
        initial states of experiments), tau anywhere including 0, 1 and the
        boundaries of the reachable interval. Instances whose distance to a
        boundary is at rounding-noise level are skipped (see item 25)."""
        rng = random.Random(1848)
        instances = []
        while len(instances) < RANDOM_N:
            x, edges, eps = random_instance(rng, binary_opinion if len(instances) % 2 else grid_opinion)
            mode = rng.randrange(5)
            if mode == 0:
                tau = rng.uniform(min(x), max(x))
            elif mode == 1:
                tau = min(x) + eps * rng.uniform(-1.5, 0.75)
            elif mode == 2:
                tau = max(x) + eps * rng.uniform(-0.75, 1.5)
            else:
                tau = rng.choice([0.0, 1.0, min(x), max(x)])
            tau = min(1.0, max(0.0, tau))
            if all(abs(abs(xi - tau) - eps) > 1e-9 for xi in x):
                instances.append((x, edges, tau, eps))
        self.run_batch(instances, check_against_theorem)


class TestBoundaryValues(EngineTestCase):
    """item23: _get_low_and_high clamps the window to [0, 1]; with the strict
    tests (L51, L173, L209, L326) an opinion of exactly 0.0 or 1.0 is then
    excluded whenever tau - eps <= 0 or tau + eps >= 1."""

    def test_item23_node_exactly_at_0_or_1_is_found(self):
        """L49-51: _find_node_tao_opinion misses a node sitting AT tau when
        tau is 0 or 1, and any node at 0.0 / 1.0 when tau is within eps of it."""
        cases = [
            ("puppet, tau = 0",           [0.0, 1.0],      cycle(2, 1.0), 0.0,  0.1),
            ("puppet, tau = 1",           [0.0, 1.0],      cycle(2, 1.0), 1.0,  0.1),
            ("non-puppet, tau near 0",    [0.0, 1.0, 1.0], cycle(3, 0.5), 0.04, 0.1),
            ("non-puppet, tau near 1",    [0.0, 0.0, 1.0], cycle(3, 0.5), 0.96, 0.1),
            ("already in consensus at 0", [0.0, 0.0, 0.0], cycle(3, 0.5), 0.05, 0.1),
        ]
        for name, x, edges, tau, eps in cases:
            with self.subTest(case=name):
                self.assertReachedConsensus(self.consensus(x, edges, tau, eps), x, edges, tau, eps)

    def test_item23_path_cloning_between_equal_opinions_at_0_or_1(self):
        """L172-173: in the two-agent game the path v -> ... -> w is cloned with
        start and end both at exactly 0.0 (or 1.0); `0.0 < 0.0` is False and the
        opinions never change, so the loop never ends. Binary opinions, tau = 0.5."""
        edges = [(0, 1, 0.3), (1, 2, 0.4), (2, 0, 0.4)]       # alpha = (0, 1), path 1 -> 2 -> 0
        for x in ([1.0, 0.0, 0.0], [0.0, 1.0, 1.0]):
            with self.subTest(x=x):
                self.assertReachedConsensus(self.consensus(x, edges, 0.5, 0.1), x, edges, 0.5, 0.1)

    def test_item23_check_all_accepts_opinions_at_0_and_1(self):
        """L324-326: |0.0 - 0.05| < 0.1, yet `0.0 < 0.0` rejects it."""
        for x, tau in (([0.0, 0.01], 0.05), ([1.0, 0.99], 0.95)):
            with self.subTest(x=x, tau=tau):
                res = run_one(dict(kind="check_all", x=x, tau=tau, eps=0.1), timeout=10)
                self.assertEqual(res["status"], "ok", describe(res))


class TestIterationCap(EngineTestCase):
    def test_item24_min_edge_1e_5_needs_more_than_1e5_iterations(self):
        """L185/L209: the game stops silently after 10**5 iterations. With
        I = 1e-5 in both directions it needs about 3.3e5 (the proof's
        y_o = ceil(log_c(eps'/2)) is about 5.3e5). Today the failure surfaces
        as the assert at L144 (or as a hang under `python -O`)."""
        edges = [(0, 1, 1e-5), (1, 0, 1e-5)]
        x, tau, eps = [0.0, 1.0], 0.5, 0.02
        validate_instance(x, edges)
        res = run_one(dict(kind="consensus", x=x, edges=edges, tau=tau, eps=eps, summary=True), timeout=60)
        self.assertReachedConsensus(res, x, edges, tau, eps)


class TestFloatingPointResolution(EngineTestCase):
    def test_item25_radius_below_resolution_terminates(self):
        """L83 with L148: when gama = radius / levels is below the spacing of
        doubles around the parent's opinion, `x_u - gama < x_v < x_u + gama` is
        False even for x_v == x_u, so level cloning never ends. Only termination
        is required here (a schedule, None, or an exception are all accepted):
        the first two cases are 'reachable' only by rounding noise."""
        cases = [
            ("puppet, tau=0.1, eps=0.2, node at 0.3",
             [0.3, 0.5, 0.3, 0.3, 1.0, 0.0, 1.0, 0.5], cycle(8, 1.0), 0.1, 0.2),
            ("non-puppet, same decimals", [0.3, 0.5, 1.0], cycle(3, 0.4), 0.1, 0.2),
            ("non-puppet, radius 2.8e-16", [0.5, 0.7, 0.9], cycle(3, 0.3), 0.25 + 3e-16, 0.25),
        ]
        for name, x, edges, tau, eps in cases:
            with self.subTest(case=name):
                res = self.consensus(x, edges, tau, eps)
                self.assertNotEqual(res["status"], "timeout", describe(res))


class TestSlips(unittest.TestCase):
    def test_item17_docstrings_are_raw(self):
        r"""Non-raw docstrings: `\to` becomes TAB + 'o'; `\i`, `\l`, `\m`, `\g`
        are invalid escapes (SyntaxWarning, an error in a future Python)."""
        path = find_engine()
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tree = compile(src, path, "exec", flags=ast.PyCF_ONLY_AST, dont_inherit=True)
            compile(src, path, "exec", dont_inherit=True)
        escapes = sorted({f"line {w.lineno}" for w in caught
                          if issubclass(w.category, (SyntaxWarning, DeprecationWarning))})
        tabs = [n.body[0].lineno for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Module))
                and n.body and isinstance(n.body[0], ast.Expr)
                and isinstance(n.body[0].value, ast.Constant)
                and isinstance(n.body[0].value.value, str) and "\t" in n.body[0].value.value]
        self.assertEqual((escapes, tabs), ([], []),
                         f"invalid escapes at {escapes}; docstrings containing a TAB start at lines {tabs}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        _worker_main(os.path.abspath(sys.argv[2]))
    else:
        unittest.main(verbosity=2)