import VersoSlides
import Verso.Doc.Concrete
import Verso.Doc.Elab

open VersoSlides
open Verso Doc Elab

set_option verso.code.warnLineLength 100

@[directive]
public meta def footer : Elab.DirectiveExpanderOf Unit
  | (), stxs => do
  let contents ← stxs.mapM elabBlock
  ``(Block.other (VersoSlides.BlockExt.wrap #[("class", "slide-footer")]) #[$contents,*])

#doc (Slides) "Lean – Architecture, Meaning and Trust" =>

# Lean – Architecture, Meaning and Trust

%%%
state := "title"
%%%

:::class "speaker"
*Joachim Breitner*
:::

Lean FRO

:::class "event"
Mathematics Colloquium · Universität Freiburg · November 17, 2026
:::

# What is Lean?

```lean
/-- A prime is a number larger than 1 with only trivial divisors -/
def IsPrime (n : Nat) := 1 < n ∧ ∀ k, 1 < k → k < n → ¬ k ∣ n

/-- Every number larger than 1 has a prime factor -/
theorem exists_prime_factor :
    ∀ n, 1 < n → ∃ k, IsPrime k ∧ k ∣ n := by
  intro n h1
  -- Either `n` is prime...
  by_cases hprime : IsPrime n
  · grind [Nat.dvd_refl]
  -- ... or it has a non-trivial divisor with a prime factor
  · obtain ⟨k, _⟩ : ∃ k, 1 < k ∧ k < n ∧ k ∣ n := by
      simp_all [IsPrime]
    obtain ⟨p, _, _⟩ := exists_prime_factor k (by grind)
    grind [Nat.dvd_trans]

/-- The factorial, defined recursively, with custom notation -/
def factorial : Nat → Nat
  | 0 => 1
  | n+1 => (n + 1) * factorial n
notation:10000 n "!" => factorial n

/-- The factorial is always positive -/
theorem factorial_pos : ∀ n, 0 < n ! := by
  intro n; induction n <;> grind [factorial]

/-- ... and divided by its constituent factors -/
theorem dvd_factorial : ∀ n, ∀ k ≤ n, 0 < k → k ∣ n ! := by
  intro n; induction n <;>
    grind [Nat.dvd_mul_right, Nat.dvd_mul_left_of_dvd, factorial]

/-- We show that we find arbitrary large (and thus infinitely
many) prime numbers, by picking an arbitrary number `n`
and showing that `n! + 1` has a prime factor larger than `n`
-/
theorem InfinitudeOfPrimes : ∀ n, ∃ p > n, IsPrime p := by
  intro n
  have : 1 < n ! + 1 := by grind [factorial_pos]
  obtain ⟨p, hp, _⟩ := exists_prime_factor (n ! + 1) this
  suffices ¬p ≤ n by grind
  intro (_ : p ≤ n)
  have : 1 < p := hp.1
  have : p ∣ n ! := dvd_factorial n p ‹p ≤ n› (by grind)
  have := Nat.dvd_sub ‹p ∣ n ! + 1› ‹p ∣ n !›
  grind [Nat.add_sub_cancel_left, Nat.dvd_one]
```

:::footer
Example from [lean-lang.org](https://lean-lang.org)
:::

# Why Lean?

{image "static/images/why-lean.svg"}[Why Lean]

# History of Lean

{image "static/images/history.svg"}[History of Lean]

# Scale of Lean Formalizations

%%%
state := "full-figure"
%%%

{image "static/images/formalization-scale-2026-10-24.png"}[Scale of Lean formalizations: total Lean lines, log scale, June 2025 to October 24, 2026]

# What does Lean mean?

{image "static/images/type-theory-sugar.svg"}[Lean syntax and its set-theoretic reading]

# The Architecture of Lean

{image "static/images/architecture.svg"}[Architecture of Lean]

# Threat models

{image "static/images/threat-models.svg"}[Threat models]

# Attacks and defenses

{image "static/images/attacks.svg"}[Attacks and defenses]

# Comparator

{image "static/images/comparator.svg"}[Comparator]

# A Lean checker is a type checker

{image "static/images/checker.svg"}[A Lean checker is a type checker]

# {class "strike"}[The Lean] A simple type system

{image "static/images/judgments.svg"}[The three judgments]

# Typing rules (selection)

{image "static/images/typing-rules.svg"}[Typing rules]

# The standard path to consistency is hard

{image "static/images/standard-path.svg"}[Standard path to consistency]

# A direct path to consistency: syntax-driven interpretation

{image "static/images/interpretation.svg"}[The interpretation]

# A direct path to consistency: syntax-driven interpretation (cont.)

{image "static/images/interpretation2.svg"}[The interpretation, continued]

# Preservation, take 1

{image "static/images/preservation-take1.svg"}[Preservation, take 1]

# Well-denoted terms

{image "static/images/well-denoted.svg"}[Well-denoted terms]

# Preservation, take 2

{image "static/images/preservation-take2.svg"}[Preservation, take 2]

# Preservation up to a point

{image "static/images/preservation-point.svg"}[Preservation up to a point]

# The certification tax

{image "static/images/certification-tax.svg"}[The certification tax]

# Sorts and universes

{image "static/images/sorts-universes.svg"}[Sorts and universes]

# Inductive types

{image "static/images/inductive-types.svg"}[Inductive types]

# The consistency theorem of con-leche

```lean -show
namespace ConLeche
universe w
universe u
/-- `y` and `u` are equinumerous: some (meta-level) function restricts to
a bijection from the members of `y` onto the members of `u`.  This is the
notion Tarski's Axiom A is stated with; using a Lean-level function keeps
ordered pairs out of the core (a first-order presentation instead
describes set-level bijections by formulas).  For the intended models this is
equivalent: a set-level bijection yields a meta-level one by choice, and
the axiom's disjunction is only ever *used* by refuting this side via a
diagonal argument (`Derive/Universe.lean`). -/
def Equinumerous {V : Type u} (mem : V → V → Prop) (y u : V) : Prop :=
  ∃ f : V → V,
    (∀ z, mem z y → mem (f z) u) ∧
    (∀ z z', mem z y → mem z' y → f z = f z' → z = z') ∧
    (∀ w, mem w u → ∃ z, mem z y ∧ f z = w)

/-- The matrix of Tarski's Axiom A (Tarski 1938), strengthened with the
transitivity clause: `u` is a Grothendieck universe (SGA 4, Exp. I,
Appendix).  The four clauses, in order:

1. *transitivity*: members of members are members — the clause that
   distinguishes a Grothendieck universe from a bare Tarski one, and
   what makes the empty set fall out of regularity;
2. *subsets of members are members*;
3. *power sets stay inside*: some member contains all subsets of a
   member (with clause 2 this makes `power y` itself a member);
4. *inaccessibility*: a subset of `u` is equinumerous with `u` or a
   member.  Dropping the equinumerosity disjunct is **inconsistent**
   (`u ⊆ u` would force `u ∈ u`, against regularity). -/
def IsTGUniverse {V : Type u} (mem : V → V → Prop) (u : V) : Prop :=
  (∀ y z, mem y u → mem z y → mem z u) ∧
  (∀ y z, mem y u → (∀ w, mem w z → mem w y) → mem z u) ∧
  (∀ y, mem y u → ∃ p, mem p u ∧ ∀ z, (∀ w, mem w z → mem w y) → mem z p) ∧
  (∀ y, (∀ w, mem w y → mem w u) → Equinumerous mem y u ∨ mem y u)
```

```lean -panel
class SetTheory (V : Type u) where /- !hide -/
  /-- Set membership. -/ /- !end hide -/
  Mem : V → V → Prop /- !hide -/
  /-- Extensionality: sets with the same members are equal. -/
  ext : ∀ {x y : V}, (∀ z, Mem z x ↔ Mem z y) → x = y
  /-- Pairing: the unordered pair. -/ /- !end hide -/
  upair : V → V → V /- !hide -/
  /-- Characterization of the unordered pair. -/
  mem_upair : ∀ {z a b : V}, Mem z (upair a b) ↔ z = a ∨ z = b
  /-- Union: the union of the members. -/ /- !end hide -/
  sUnion : V → V /- !hide -/
  /-- Characterization of the union. -/
  mem_sUnion : ∀ {z x : V}, Mem z (sUnion x) ↔ ∃ y, Mem y x ∧ Mem z y
  /-- Power set. -/ /- !end hide -/
  power : V → V /- !hide -/
  /-- Characterization of the power set: members are the subsets. -/ /- !end hide -/
  mem_power : ∀ {z x : V}, Mem z (power x) ↔ ∀ w, Mem w z → Mem w x /- !hide -/
  /-- Regularity: every nonempty set has an `∈`-minimal member. -/
  regularity : ∀ x : V, (∃ y, Mem y x) → ∃ y, Mem y x ∧ ¬ ∃ z, Mem z y ∧ Mem z x
  /-- Replacement, as a Lean-level scheme: the image of a set under an
  arbitrary function `V → V`. -/ /- !end hide -/
  image : (V → V) → V → V /- !hide -/
  /-- Characterization of the replacement image. -/
  mem_image : ∀ {f : V → V} {a z : V}, Mem z (image f a) ↔ ∃ w, Mem w a ∧ z = f w
  /-- An ω-chain of Grothendieck universes: the sets interpreting the
  universe tower (Carneiro's ω-many inaccessibles, op. cit.;
  intended model `V_{κ n}`). -/ /- !end hide -/
  univChain : Nat → V /- !hide -/
  /-- The chain increases strictly: each universe is a member of the
  next. -/
  univChain_mem : ∀ n : Nat, Mem (univChain n) (univChain (n + 1))
  /-- Each chain member is a Grothendieck universe (Tarski's Axiom A
  matrix with transitivity, `IsTGUniverse`). -/
  univChain_tg : ∀ n : Nat, IsTGUniverse Mem (univChain n) /- !end hide -/
  -- … more laws
```

```lean -show
/-- A model of set theory of exactly the strength the checker needs:
membership, the six ZF⁻ axioms (extensionality, pairing, union, power
set, regularity, Lean-level replacement), and an ω-chain of
Grothendieck universes.  Infinity is derivable; choice is inherited
from the meta-logic (`Classical.choice`); see the module docstring. -/
add_decl_doc SetTheory
/-- The global environment: the constants accepted so far and the
structures' projection tables, each list newest first.  Names are
unique (the checker rejects duplicates), so the order is irrelevant for
lookup; so are the tables' structure names (a block installs a table
only for its own, fresh, structure-like members).

The tables are not constants (task #362): no `.const` names one, they
are read by `.proj` nodes alone, keyed on the structure's name
(`findTable?`). -/
axiom Env : Type
/-- A declaration presented to the checker. -/
axiom Declaration : Type
/-- The pins of one toolchain: eight pinned defining expressions and
eight certificate-proof lists and eight type-pin lists, in the order of
`natDivModNames`' family (`div`, `mod`, `gcd`, `land`, `lor`, `xor`,
`shiftLeft`, `shiftRight`), plus the toolchain string for
diagnostics.  A type pin `(n, ty)` says that the constant `n`, which
the operation's certificates use, has type `ty` in this toolchain. -/
axiom NatOpPinSet : Type
axiom CheckError : Type
/-- **The checker's mode setting** — two values, validated once at
startup and threaded as configuration, never re-read at runtime.

* `.verified` (the default, `--verified`): the verified lane.  The
  surface the **graded** set-theoretic
  model proves — `no_proof_of_Empty_cached`
  (`ConLeche/Verify/Cached/MainC.lean`) is its letter over the driver
  this binary runs.  The seven TT-lane checks (tasks #126, #129, #130,
  #135, #136, #137, #146) are off; the λ and η checks (task #342) run,
  and every certificate family runs.
* `.trusted` (`--trusted`): the unverified lane — the same checker
  with the work that exists **for certification only** omitted.
  What must not be dropped is everything believed necessary for
  *soundness* (which is different from "necessary for our soundness
  proof to go through"), so the lane is never optimized on its own:
  it is the real mode with certain steps omitted (DESIGN.md, "MODE
  RENAME").  Since 2026-09-06 it is literally that: the one cached
  driver (`ConLeche/Cached/ParsedC.lean`) at `.trusted`, where
  `verifiedChecks` is `false` — so what it omits is exactly what that
  function gates in `ConLeche/Cached/CoreC.lean` (DESIGN.md, "CORET
  RETIRED").

**The mode is the public interface** (task #185, 2026-09-06; task
#452): what it carries is the function `verifiedChecks` below, a
`match` on the two constructors, so each read reduces by `rfl` at
either mode.

The two values are spelled `--verified` and `--trusted` on the command
line, and they say what the modes are FOR rather than which artefact
proves them.

The cores' other parameter is not the mode's: the official kernel's
`m_eager_reduce` flag, an argument `eager : Bool` of the knot (tasks
#353, #452; see `coreKnot`).  It is internal to the core, and every
entry point outside the knot runs at `eager := false`. -/
inductive CheckMode where
  | verified
  | trusted
/-- **A model of the environment `env` in the set theory `V`**: one
assignment `cval` of a set to every constant at every level
assignment — fixed once, for the whole environment — under which every
stored constant is a member of what its type denotes, the built-in
`False` is the empty set, and the built-in `Eq` is set equality.

The interpretation of the constants *is* the model: there is nothing
else to choose (`Sort`, `∀`, `λ`, application and projection are read
by fixed set operations).  `mem` is what makes every stored theorem
true — a theorem `t : P` is a constant whose type `P` denotes a truth
value, and `cval t φ ∈ˢ ⟦P⟧` says that truth value is `{pt}` — and
`false_empty` is what makes truth mean something: a proof of `False`
would be a member of `∅`.

`False` and `Eq` are both built in (the checker installs them from its
own pins and rejects a stream that declares them otherwise), so the
last two fields are facts about the checker's own constants, not
hypotheses about the input; each is stated of whatever the stored
constant denotes, so it says nothing when nothing is stored.

The model says nothing about *definitional* equalities — a
definition's unfolding, an inductive type's iota rules, η — because it
does not have to, and `eq_equality` is what discharges that debt: any
such equality a reader cares about can be stated as a theorem `h : a = b`
and proved by `rfl`; the checker accepts it; `mem` puts `cval h φ` in
what `Eq A a b` denotes, which by `eq_equality` is `eqv ⟦a⟧ ⟦b⟧`; and
`eqv x y` is inhabited only when `x = y` (`SetTheory.eq_of_mem_eqv`).  So the
two sides of every accepted equation denote the same set.  Types are
the whole statement; values are the checker's business. -/
axiom Model (V : Type w) [SetTheory V] (env : Env) : Type w
/-- **The declaration fold.**

The records are the array the frontend produces (`Frontend.preparePrelude`); the proofs read the
fold as `ds.toList.foldlM` (`Array.foldlM_toList`), which is where `DeclsRun` lives.  The `× Nat` of
the error is the failure's position: here the record's position in the fold, in the frontend's half
of the same error type the input's line number (`ConLeche/Frontend/Export.lean`). -/
axiom checkDecls (mode : CheckMode) (pins : List NatOpPinSet) (maxNatSize : Nat) (ds : Array Declaration) :
    Except (CheckError × Nat) Env
/-- **A file system snapshot**: the real path of every path that names
something, and the bytes of every regular file, by its real path. -/
structure FS where
  /-- the real path of a path that names something, `none` where nothing is -/
  real : System.FilePath → Option System.FilePath
  /-- a regular file's bytes, by its real path; `none` for a directory or
  anything else that is not a readable regular file -/
  bytes : System.FilePath → Option ByteArray
/-- A regular file's bytes by any path to it. -/
def FS.file (fs : FS) (p : System.FilePath) : Option ByteArray := (fs.real p).bind fs.bytes
/-- **The model's open handles**: each a file's bytes and the position of
its next read; a handle is its index. -/
abbrev HS := Array (ByteArray × Nat)
/-- **The model's monad**: an action is the set of its possible
outcomes on a snapshot from the open handles before it — a value or an
exception, and the open handles after it.  A run that does not end has
no outcome (no loop of the driver needs one: they all terminate). -/
def ModelIO (α : Type) : Type := FS → HS → Except IO.Error α → HS → Prop
/-- **`v` is a value the action can give**: a value outcome of it, from
some open handles to some.  What the specifications of the `.olean`
reads say of an action whose answer does not depend on the handles. -/
axiom ModelIO.CanGive {α : Type} (x : ModelIO α) (fs : FS) (v : α) : Prop
class CheckerIO (m : Type → Type) where
instance : CheckerIO ModelIO := ⟨⟩
/-- **What `main` runs, generic in the IO class** (tasks #424, #450): the
argument parse, `--help` and the usage errors, the request run, and the
catch of `IO` errors into exit 3.  It reaches the runtime through
`CheckerIO.liftIO`, and the exit code, the `UInt8` `IO.Process.exit`
takes, is computed here and returned outside `liftIO`, so that what the
model says of the code is what the run computed.  The binary's `main`
(`Main.lean`) is the plumbing around this at `IO`.

**An uncaught IO exception is an internal error, exit 3 — never a REJECT
(task #335).**  `IO.Error` can surface anywhere below: the input path
naming a directory, a read failing mid-stream, a write to stdout/stderr
failing (a closed pipe).  Left uncaught, it would reach the Lean
runtime's own top-level handler, which prints "uncaught exception: …"
and exits with status 1 — exactly the code the arena convention reserves
for a declaration *positively* rejected as invalid.  This `try` is the
one place that turns any such exception into exit 3 instead, and it is
here, not in `main`, so that the model sees it.  A verdict that is
deliberately exit 1 (`.invalid`) or exit 2 (`.notImplemented`) is a plain
`return` out of `runReq`, never a `throw`, so it passes through
untouched.  The catch handler's own write can itself fail (that same
closed stderr, say); that must not flip the exit code either, so it is
best-effort and its own failure is swallowed. -/
axiom Driver.runArgs {m : Type → Type} [CheckerIO m] (args : List String) : m UInt8
/-- **One JSON file that declares a theorem of type `False`.**  The
whole file, as one template: four lines of the lean4export format, in
this order, each on a line of its own, with anything at all before,
between and after them:

* `{"in":i,"str":{"pre":0,"str":"False"}}` — name entry `i` is `False`;
* `{"ie":j,"const":{"name":i,"us":[]}}` — expression entry `j` is the
  constant `False`;
* `{"in":k,"str":{"pre":0,"str":"<name>"}}` — name entry `k` is the
  theorem's own name, any name;
* `{"thm":{"all":[k],"levelParams":[],"name":k,"type":j,"value":v}}` —
  a theorem named `k` whose type is `j` and whose proof is expression
  entry `v`, whatever that is.

This is ONE shape of such a file, not every proof of `False`: a file
that declares the same theorem with its lines in another order, or
proves a contradiction some other way, is outside the predicate — what
the corollary says of the files inside it is that the checker rejects
them.  The five parts are unconstrained otherwise: a part may hold any
number of further lines, including malformed ones — then the file does
not parse and is rejected for that reason.  They are `String`s, so the
file is the UTF-8 of one interpolated Lean string; a file whose parts
carry bytes that are no UTF-8 at all is outside the predicate too,
which costs nothing for an export, the exporter writing UTF-8. -/
axiom jsonWithTheoremFalse (chunks : List ByteArray) : Prop
```

```lean -panel
theorem model_exists (V : Type w) [SetTheory V]
    (pins : List NatOpPinSet) (maxNatSize : Nat) (ds : Array Declaration) (env : Env)
    (accepted : checkDecls .verified pins maxNatSize ds = .ok env) :
    Nonempty (Model V env) /- !hide -/ := sorry /- !end hide -/

theorem main_no_False (V : Type w) [SetTheory V] {file : String} {fs : FS} {b : ByteArray}
    (hb : fs.file file = some b) (hF : jsonWithTheoremFalse [b]) :
    ¬ ModelIO.CanGive (Driver.runArgs ["--", file]) fs 0 /- !hide -/ := sorry /- !end hide -/
```

```lean -show
end ConLeche
```

:::footer
[ConLeche/MainTheorem.lean](https://github.com/leanprover/con-leche/blob/master/ConLeche/MainTheorem.lean)
:::

# Thank You

%%%
state := "title"
%%%

:::class "speaker"
*Joachim Breitner* · [joachim-breitner.de](https://www.joachim-breitner.de)
:::

:::class "further-reading-title"
Further reading
:::

* [The Lean website: lean-lang.org](https://lean-lang.org)
* [Lean reference manual, “Validating a Lean Proof”: lean-lang.org/doc/reference/latest/ValidatingProofs](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
* [The con-leche proof idea: leanprover.github.io/con-leche](https://leanprover.github.io/con-leche/)
* [The Lean community Zulip: leanprover.zulipchat.com](https://leanprover.zulipchat.com)

:::class "event"
Mathematics Colloquium · Universität Freiburg · November 17, 2026
:::

# The con-leche family of checkers

{image "static/images/checker-family.svg"}[The con-leche family of checkers]

# Why is the point not the empty set?

{image "static/images/point-not-empty.svg"}[Why is the point not the empty set]
