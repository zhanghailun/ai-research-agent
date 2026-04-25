# Management Science Writing Skill

This note summarizes the writing principles that emerged from the Section 4 revision, the Section 5.2 revision, and the Section 6 revision in `body.tex`, together with the writing requirements stated across those conversations.

The goal is not to make the paper less rigorous. The goal is to make the rigor serve a stronger managerial story.

## Core Mindset

A `Management Science` paper should not read like a purely technical note that happens to contain managerial implications at the end. It should read like a paper motivated by an economically important question, where the modeling and theory are tools for uncovering a clear managerial insight.

In practice, this means:

- Start from the managerial problem, not from the technique.
- Keep reminding the reader why the result matters economically.
- Explain the trade-off behind the result, not only the result itself.
- Tell the reader what the theorem means for design, policy, or practice.
- Preserve formal precision. Do not oversell beyond what the theorem proves.

## What This Means for the Prose

The prose should move in the following order:

1. Structural insight
2. Economic question
3. Formal result
4. Managerial meaning
5. Practical implication

The current Section 4 does this better than the earlier draft because it repeatedly translates mathematics into business meaning. Examples include:

- turning connectivity into the "economic value of connectivity"
- describing disconnected designs as creating "fragmented" pooling
- stating that "full opacity is not necessary"
- explaining why load balancing matters operationally, not only theoretically

## Writing Rules for a Management Science Paper

### 1. Lead with the question the manager cares about

Do not open a section by saying only what will be bounded or derived.

Better pattern:

- remind the reader what the previous section established
- raise the next natural economic or managerial question
- explain what this section will show and why it matters

Good example pattern:

`Section 3 established the structural condition. The natural question is then economic. How much value does this structure create?`

This is better than:

`In this section, we derive bounds on relative cost savings.`

In later theory sections, when the reader already understands the main theorem, the recap can be one short hinge sentence or omitted. Lead instead with what this section optimizes, under which constraints, and why that decision matters to the manager. The Section 6 lessons below spell this out in more detail.

### 2. Translate structure into value

When the paper identifies a structural property such as connectivity, sparsity, overlap, or GCG, do not stop there.

Always explain:

- what the property changes operationally
- why that changes costs, profits, or service
- what would happen without that property

The reader should come away with a sentence like:

`Connectivity matters because it lets the retailer absorb demand imbalances system-wide instead of leaving inventory trapped in the wrong items.`

### 3. Make the trade-off explicit

A management paper should show tension, not just improvement.

For each main argument, state both sides:

- connected versus disconnected
- sparse versus fully flexible
- simple heuristic versus optimal policy
- practical design versus infeasible ideal benchmark

This is often the difference between a result and an insight.

### 4. After every theorem, answer three questions

After a formal result, explain:

- What does the theorem say mathematically?
- Why does the result happen?
- Why should a retailer or manager care?

If a paragraph after a theorem answers only the first question, it is still too technical.

### 5. Keep the benchmark visible

The economic meaning of a result usually depends on the benchmark.

In this paper, the important benchmarks are:

- traditional selling
- the fully flexible benchmark
- the optimal fulfillment policy

Do not let the benchmark disappear once the theorem is stated. Keep telling the reader what the result means relative to the benchmark.

### 6. Use interpretation words deliberately

Helpful words and phrases for this style:

- economic value
- managerial message
- operationally
- benchmark
- trade-off
- practical implication
- system-wide pooling
- stranded inventory
- fragmented pooling
- tractable prescription

These words are useful when they explain the result. They should not be decorative.

### 7. Precision matters more than excitement

A `Management Science` paper should be engaging, but it should not overclaim.

Prefer:

- `same order as the fully flexible benchmark`
- `captures the first-order value of flexibility`
- `does not improve the order of cost savings`

Avoid:

- `same savings` when the theorem proves only an order result
- `optimal` unless optimality is formally established
- vague praise such as `very effective` without saying relative to what

### 8. Do not present results as a list of technical steps

Transitions such as these are often too mechanical:

- `Below is our main result`
- `We next discuss`
- `It is easy to see`

Better transitions explain narrative function:

- `Lemma X provides the bridge from structure to performance.`
- `The next theorem is the main quantitative payoff of the section.`
- `Corollary X gives the operational implication of the benchmark comparison.`

### 9. Use short pivot sentences

Short sentences can improve readability when they mark a shift in logic.

Examples:

- `The natural question is then economic.`
- `We also show the corresponding trade-off.`
- `This result matters operationally.`

These work well because they guide the reader through the argument.

### 10. Explain why the assumption is reasonable in practice

If the analysis fixes `N`, assumes large `S`, uses even allocation, or adopts load balancing, explain why that modeling choice is sensible in the application.

A management reader wants to know:

- why the assumption is not arbitrary
- whether the conclusion is likely to matter in practice

### 11. Rigor on constants

A `Management Science` audience forgives loose writing more than it forgives loose math. Whenever the paper asserts `\eta_{\min}=\Omega(q_{\min})`, `c_{\min}=\Omega(1)`, or a similar asymptotic claim, the proof must carry an explicit constant through every step so the claim holds verbatim, not only up to an unspecified factor.

Concrete practices:

- State the threshold constant explicitly, e.g., `\delta\le q_{\min}/(4N^2|\mathcal{A}|)`, rather than `\delta` small enough.
- Carry an explicit lower bound on the stationary quantity (`\eta(\bar{\mathbf{p}})\ge q_{\min}/N`) through the perturbation argument.
- Distinguish per-type perturbations from total-subset perturbations. They differ by combinatorial factors (`N`, `|\mathcal{A}|`, or `1` depending on whether `\sum_i p_i\le 1` applies) and those factors matter for the stated threshold.
- If two propositions look parallel but use different constants, either reconcile them or explain the mechanism behind the gap. A factor-of-`N` discrepancy is an insight, not an embarrassment.

### 12. Parallel structure across cases

When a section studies several variants of the same phenomenon (three demand environments, three allocation rules, three network designs), use parallel syntactic and paragraph structure across the cases.

Concretely, each case paragraph should follow the same internal template:

1. One sentence stating which primitive is fixed and which varies.
2. A sentence giving the explicit bound or set on the varying primitive.
3. One or two sentences of real-world interpretation for that environment.
4. One sentence announcing the retailer's commitment (which allocation is used and why).

Parallel structure lets the reader absorb the common pattern and notice the substantive differences, instead of re-parsing unfamiliar prose each time.

### 13. Quantitative comparison across parallel results

When two parallel propositions deliver the same qualitative conclusion under different tolerances or different thresholds, compare them quantitatively and explain the mechanism.

The template is:

1. State the two thresholds in big-`O` form with the same constants visible.
2. Report the ratio in words. "Case 3 tolerates fluctuations `N` times looser than Case 1."
3. Explain the mechanism. Typically one case benefits from a normalization (`\sum_i p_i\le 1`, transfer-matrix unit mass, simplex constraint) that the other does not.
4. Translate the gap into a managerial sentence. A wider tolerance band is easier forecasting, a tighter band is a forecasting priority.

This pattern turns a technical constant into an economic insight about which source of variation the retailer should fear most.

## Architecture of a Robustness / Extension Section

Sections that extend a base result to more general environments (general allocations, time-varying demand, multi-segment customers) are the easiest place for a paper to drift into a bullet list of technical cases. The following architecture prevents that drift and emerged directly from the Section 5.2 revision.

### Setup: one unified formulation, then a menu of cases

Write one setup block that:

1. Introduces the worst-case or sample-path version of the central structural quantity, here `\eta_{\min}`, once and for all.
2. States the single lemma or theorem that carries through with the worst-case quantity in place of the stationary one.
3. Previews the cases by the source of non-stationarity, not by technique.
4. Defers the unified quantitative payoff to the master theorem placed at the end.

The benefit is that every subsequent case shares the same object of study, the same infrastructure, and the same quantitative goal.

### Each case: problem setup, formal result, streamlined proof, managerial insight

Each case then has exactly four blocks, in this order:

1. A short problem-statement paragraph following the parallel-structure template of rule 12.
2. A single proposition, written in the same format and with the same quantifiers as analogous propositions in earlier sections.
3. A streamlined proof that carries explicit constants per rule 11.
4. A managerial-insight paragraph following the template in the next section.

Resist the temptation to embed interpretation inside the proof or to break the proposition into sub-claims. The parallelism across cases is the reader's main navigational aid.

### Closing paragraph: same message, three environments

End the section with a short paragraph that names the common pattern across the cases without restating the master theorem. The pattern sentence should do three things:

1. Name the three environments in parallel clauses.
2. State the common conclusion in one sentence using the unified quantity.
3. Translate the pattern into a single practical checklist item for the retailer.

Example shape: "Whether the fluctuation comes from base demand, heterogeneous segments, or transfer-matrix drift, the retailer's task reduces to a single check: certify that the induced system has positive sample-path GCG."

## When to Hoist the Master Theorem Into Its Own Subsection

A symptom that the structure is wrong:

- Propositions in the section keep forward-referencing a master theorem with phrases like "Theorem X below" or "deferred to Theorem X."
- The master theorem subsumes results from more than one preceding subsection.
- The master theorem's interpretation is longer than the proposition discussion that invokes it.

When two or more of these are present, move the master theorem out of the case section and into a short closing subsection of the parent section. Keep the label unchanged so cross-references continue to work. In the new subsection:

1. Lead with a single sentence explaining why the separate extensions reduce to the same condition.
2. State the theorem.
3. List which prior propositions verify its hypotheses, in the order they appear.
4. Spell out the scope, typically by noting what the theorem does not assume (no smallness of demand, no specific allocation rule, only i.i.d.\ arrivals).
5. Close with one paragraph that turns the theorem into an economic meaning statement and a practical upshot for the retailer.

The preceding case sections then become clean applications of a known principle, and the master-theorem subsection becomes the paper's clearest articulation of the structural insight.

## Sample-Path and Worst-Case Formulations

Extending a stationary theorem to non-stationary environments rarely requires re-proving the theorem. The usual trick is to replace the stationary quantity by its sample-path worst case and check that the original proof goes through.

The writing pattern is:

1. Define the worst-case quantity in a single display equation.
2. Note in one sentence which step in the existing proof uses this quantity and why the replacement is valid.
3. Frame the rest of the section as verification exercises for the worst-case quantity in specific environments.

This keeps the technical novelty in the right place (the verification) and stops the paper from re-deriving the cost-savings argument for each case.

## The Managerial-Insight Paragraph: Four-Part Template

After each proposition, write one paragraph that follows this order:

1. One sentence naming which regime the proposition captures.
2. One sentence on the mechanism behind the result. Use words like continuity, weighted average, interior point, cross-segment feasibility.
3. One sentence on operational implication. What can the retailer do, offline versus in real time, with which data.
4. One sentence on the failure mode or trade-off. What happens if the hypothesis fails, and what becomes the complementary priority for the retailer.

The last sentence is the one most often missing in technical drafts. It is the one a management reader remembers.

Parallel examples across the three cases of Section 5.2:

- Case 1: pairs accurate base-demand forecasting with an aggressive opaque offering as complements, not substitutes.
- Case 2: pairs segment-level knowledge with a single LP-computed hedging allocation, not real-time reallocation.
- Case 3: pairs promotional drift tolerance with a wider forecasting band on the transfer side than on the base-demand side.

## Link-Forward and Link-Back Transitions

Good transitions carry narrative information. Useful patterns that emerged in Section 5.2:

- Link back at the opening: "Section X showed that efficiency survives on the supply side. A more pressing concern for online retailers is on the demand side."
- Pose the question the section answers: "The question is whether the GCG condition remains the right object when ..."
- Preview the payoff and its location: "The quantitative cost-savings result is deferred to the unifying Theorem X in Section Y."
- Close a case and name the next one with parallel structure: "Proposition X delivers an operationally stronger message than its Case~1 counterpart."

## How to Revise a Technical Paragraph into a Management Science Paragraph

Use this conversion template:

1. State the formal object or result.
2. Say what it means in words.
3. Explain the mechanism behind it.
4. State the managerial implication.

Example template:

`Lemma X shows that ...`

`This means that ...`

`The reason is that ...`

`Managerially, this implies that ...`

Not every paragraph needs all four sentences, but most theory sections should repeatedly follow this logic.

## Section-Level Storytelling Template

For a theory section, a strong flow is:

1. Link back to the previous section.
2. Raise the next economic question.
3. Clarify the benchmark and asymptotic setting.
4. Establish the benchmark result.
5. Show how the new design changes the benchmark.
6. State the main theorem as the payoff.
7. Interpret the corollaries in managerial language.
8. Close with concrete design or policy implications.

This is especially useful for Sections 4, 5, and 6 of this paper.

## Lessons from the Current Section 4

The current Section 4 suggests several concrete stylistic lessons:

- Use `economic value of connectivity` rather than only `positive GCG`.
- Explain that disconnected designs leave pooling `fragmented`.
- State that `full opacity is not necessary` to obtain first-order benefits.
- Describe simple policies as operationally attractive, not just analytically convenient.
- Tie size-two designs to customer acceptance and discount needs, not only graph structure.
- Tie even allocation to a practical prescription, not only to proof convenience.

## Lessons from the Current Section 5.2

The Section 5.2 revision added a distinct set of stylistic lessons for robustness/extension sections:

- Treat the section as case studies of a unifying principle, not as independent results. The unifying theorem belongs in its own closing subsection, not inside the case section.
- Define the worst-case or sample-path version of the paper's central structural quantity once in the setup, and then reuse it across every case.
- Give each case a parallel four-block internal structure (problem setup, proposition, streamlined proof, managerial insight paragraph) so the reader navigates by structure, not by prose.
- Make the constant explicit in every threshold and propagate it through the proof. A threshold like `\delta\le q_{\min}/(4N^2|\mathcal{A}|)` is both more honest and more useful than `\delta` small enough.
- When two parallel propositions use different thresholds, compare them quantitatively and explain the mechanism behind the gap. The factor-of-`N` looseness on the transfer side is a managerial insight about where forecasting precision matters most.
- End the section with one closing paragraph that names the common pattern across the cases and hands the reader a one-line diagnostic checklist, then transition to the unifying theorem.
- Frame the linear program in Case~2 as an offline diagnostic the retailer can run, not as a proof artifact. The same language reframes the GCG computation in the general-allocation section.

## Lessons from the Current Section 6

The Section 6 revision (optimal allocation and opacity design under a performance proxy) added lessons for late-stage theory sections that combine optimization, graph structure, and managerial prescription:

- Open with scope and intuition, not the appendix. State what the section chooses (e.g. allocation and design), why a proxy such as GCG is economically interpretable, and cite the flexibility literature for the logic. Move formal rebalancing or algebraic justification of the objective to the appendix unless the main argument cannot proceed without it.
- Link back only when the hinge needs it. Avoid stock phrases such as "natural follow-up question" and avoid restating the previous section at every opening. Prefer a single sentence that states the economic job of the section and how it differs from what came before.
- State the problem and propositions with clean quantifiers. Fix what is primitive versus choice object, spell out "optimal" relative to which feasible set (e.g. simplex, budget on opaque products), and align numbered parts of propositions with the appendix proof. When graph facts enter the story, keep claims exact (e.g. at least `N-1` edges for connectivity versus `N` edges for a Hamiltonian cycle or 2-edge-connected item graphs) and tie them to the economic budget `K` when that is what the retailer controls.
- One home for each design insight. If decomposition of the proxy already signals which term is a design lever, do not repeat the full network-design discussion before the network subsection. A short bridge sentence that points forward is enough.
- Managerial content in prose, not lists. After each main result, weave mechanism, implication, and failure mode in running paragraphs. Reserve bullets for the skill note or slides, not for the paper body when the goal is a Management Science read.
- Heuristic versus optimal in named regimes. When a closed form (e.g. even allocation) is optimal on a stated class of designs (e.g. forest item graphs), say so explicitly: the regime, the economic reading, and why the rule is easy to implement without re-solving the full program.
- Extensions beyond the leading case. For regimes that matter under tight budget (e.g. opaque products of size three or more), keep the main text to intuition plus a compact formal statement if helpful, and move longer decomposition or subset notation to the appendix with a clear cross-reference.
- Terminology lock across body and appendix. Use one term per object throughout (e.g. opaque product, 2-opaque product, managerial implication) so design and proof text read as one voice.

## Introduction Writing for a Management Science Paper

The introduction is not a compressed abstract. It is a self-contained story that sells the research question to a busy editor and to a reader who has never seen the technical work. It should be readable aloud, should make one clear economic argument, and should lead the reader from a familiar business reality to a formal research question and back to a managerial takeaway.

### Six-Paragraph Narrative Architecture

Organize the introduction as six paragraphs plus a contributions block. Each paragraph plays one narrative role, and the roles do not overlap.

1. **P1 Context.** Hook the reader with the real-world setting. Describe the industry problem in plain language. End by naming every decision object the paper will study.
2. **P2 Trade-off.** Make the central tension concrete through a single, domain-grounded example with numbers. Show both extremes (too broad and too narrow, too much and too little) and why neither works. Close by foreshadowing the analytical message.
3. **P3 Difficulty.** Explain why the problem is hard on its own terms: stochastic environment, combinatorial design space, joint optimization of multiple decisions. Justify the need for a structural insight. Do not preview the answer here.
4. **P4 Research Question.** Identify the closest prior work, describe what they assume and what they prove, and state precisely which of their assumptions are restrictive in your application. State the research question as a single interrogative sentence. Close by previewing what kind of framework will be needed, not the answer itself.
5. **P5 Our Answer (managerial).** Answer P4 at a managerial level. Name the structural condition, describe the practical recipe, state what it means for the retailer or manager. Explicitly defer technical specifics to the contributions block. Close with a pointer: "the precise statements are summarized in the contributions below."
6. **Contributions block.** State four or five formal contributions, each with a bold title and two to four sentences. This is the place for big-`O` orders, theorem references, decomposition terms, and numerical evidence.
7. **P6 Roadmap.** One paragraph walking through the sections in order, one sentence each.

The order is what makes the introduction work. A reader who stops at the end of P2 should already understand the trade-off, a reader who stops at the end of P4 should already know the research question, a reader who stops at the end of P5 should already have the managerial takeaway. The contributions are there for the reader who wants the technical spine.

### Separate the Managerial Answer (P5) from the Contributions

P5 and the contributions are the two parts most prone to duplicating each other. Treat them as complementary jobs:

- **P5 says what the paper means.** It is prescriptive, uses verbs like `capture`, `reduce to`, `need not`, and is legible to a reader who does not know the technical vocabulary. It states the structural property, the closed-form recipes at a prescriptive level, and the retailer-level upshot.
- **The contributions block says what the paper proves.** It is formal, uses theorem references, explicit orders such as `\Omega(1/\sqrt{S})`, characterizations, decompositions, and citations. It is legible to a referee comparing the paper to related work.

Test: if the same sentence could appear in both blocks, it belongs in the contributions block and should be stripped from P5. Reserve for P5 only the claims a manager would quote, and reserve for the contributions block only the claims a referee would check.

### Frame the Paper as a New Research Question, Not an Extension

When the closest prior work is a special case of your setting, resist the framing "we extend X to a more general setting". That framing makes the paper sound incremental.

Better pattern in P4:

1. State what the prior work proves under its assumptions.
2. Name the assumptions that are restrictive in the real application (symmetric demand, fixed allocation, single decision variable, stationary arrivals, and so on).
3. Explain in one sentence why the prior technique (balls-into-bins, LP relaxation, dynamic programming) does not carry over once those assumptions are relaxed.
4. State the research question as a question, not as a goal.
5. Add one sentence previewing the methodological shift required, without previewing the answer.

This reframes the contribution from "we generalize X" to "we ask a question that X does not answer".

### Lead with the Realistic Regime, Not the Baseline

Open P1 with the regime practitioners actually face (Pareto-skewed demand, time-varying preferences, heterogeneous segments). Do not open with the tractable baseline of prior work. The baseline belongs in P4. Anchor the reader in business reality using a Pareto fact, a seasonal or feature-driven demand fact, or a visible platform example (Amazon, Priceline, blind-box promotions). Then let the rest of the introduction justify why the baseline of prior work does not capture this reality.

### Keep the Full Set of Decision Variables Visible from P1 Onward

If the paper jointly optimizes multiple decisions (design and allocation, pricing and assortment, timing and quantity), introduce all of them in P1 and keep all of them visible through P2 and P3. A common failure mode is to introduce one lever in P1, spend P2 and P3 on that lever only, and then surprise the reader in P5 by optimizing a second lever. Every decision object that appears in the contributions block should have been named in P1.

### Contributions Block: Four-Item Template

A four-item block works for most theory-plus-numerics papers. Each item has a bold lead phrase followed by two to four sentences.

1. **Model / representation.** What you formulate, what it generalizes, which mathematical object (bipartite graph, LP, DP) encodes the problem. Emphasize that the representation is the unified analytical language used throughout the paper.
2. **Main structural theorem and robustness.** The central equivalence or sufficiency result (necessary and sufficient, `\Omega`-bound, same-order-as-benchmark). Fold the robustness claim (general allocations, non-stationary demand) into the same item so the reader sees the theorem as one object, not as a base case plus an extension.
3. **Optimization / prescription.** The item that distinguishes the paper from prior work. If prior work fixed a decision variable and you optimize it, this is where the unique contribution is advertised. State the closed-form structure, the class of instances on which a simple rule is provably optimal, and the precise form of the optimum.
4. **Numerical evidence.** The environments covered (utility models, parameter ranges, benchmarks) and the three or four qualitative findings that match the theory.

Write each item in a form that could stand alone in a grant proposal. Avoid soft phrases such as "we explore", "we discuss", "we develop insights". Use verbs that correspond to formal deliverables: formulate, prove, characterize, decompose, identify, validate.

### Anti-AI, Pro-Human Prose

Management Science readers are fast and skeptical. Prose that reads like an AI-generated draft loses them. Prefer concrete, low-register words over high-register or decorative ones.

- Replace decorative verbs: `prominent deployments` becomes `well-known examples`, `channels excess demand toward underutilized inventory` becomes `steers excess demand toward underused inventory`, `chronically overstocks` becomes `overstocks`, `renders the problem analytically intractable` becomes `makes the problem hard to solve analytically`.
- Replace decorative nouns: `demand heterogeneity` becomes `this imbalance`, `operational advantage` becomes `practical advantage`, `residual asymmetries` becomes `asymmetries the design cannot remove`, `co-first-order decisions` becomes `equally important decisions`.
- Delete filler adjectives: `inherently asymmetric`, `fundamentally important`, `significantly challenging`, `truly novel` tend to weaken the sentence.
- Avoid AI-trope openers such as `Remarkably`, `Astonishingly`, `At a high level`. Use `Surprisingly` only when the claim really is surprising and you can defend the surprise.
- Use `that is` or `namely` to unpack a definition rather than parenthetical em-dashes: `the opacity design, that is, which items are combined into each opaque product`.

The aim is to sound like a human researcher explaining the problem to a colleague, not like a polished report.

### Preserve Precision When You Simplify

Simplification does not license overclaim. Some technical phrases survive even an aggressive plain-English pass because they carry the meaning the theorem actually proves.

- Keep `same order as the fully flexible benchmark`, not `same savings`.
- Keep `relative cost savings of order \Omega(1/\sqrt{S})`, not `comparable cost savings`.
- Keep `fully flexible benchmark in which every customer is willing to purchase an opaque product`, not shorthand such as `every customer is opaque`, which reads loose to a referee.
- Keep `provably optimal on a broad class of designs`, not `always optimal`.
- Keep `combinatorially explosive` or `doubly exponential` when that is literally what the design space is, rather than soft phrases such as `very large`.
- Keep the established technical phrase the rest of the paper uses (for this paper, `time-varying version of the GCG condition`) over a plain-English substitute that the body does not introduce.

A good revision pass first rewrites for plain language, then restores the one or two technical phrases whose looser substitutes would mislead a reviewer. Every restored phrase is a deliberate trade between readability and precision.

### Terminology Lock Across the Introduction

Lock one term per concept and use it everywhere in the introduction, the body, and the appendix.

- If the paper uses `opaque product` in Section 2, do not also write `opaque bundle` or `opaque option` in the introduction.
- If the main result is stated with `load balancing policy`, P4 should not call it `balancing policy`.
- If the appendix calls a benchmark `fully flexible`, the introduction should not call it `full flexibility benchmark` in one paragraph and `the fully flexible case` in the next.
- If the body distinguishes `traditional selling`, `partially opaque`, and `fully flexible`, the introduction must use those same three labels, not synonyms.

Small vocabulary drift is the single most common source of referee complaints about clarity. A one-line terminology lock in the header comment block pays for itself at the proofreading stage.

### Accuracy of Numerical and Empirical Claims

Every claim in the contributions block must be backed by something in the body. Before finalizing the contributions, search the body for each advertised feature (lead times, lost sales, backlogging, three utility models, and so on) and confirm that the body implements it. A claim such as `we validate the theory under lead times and lost sales` must be deleted if Section 3 explicitly restricts attention to the zero-lead-time, no-lost-sale regime.

The same rule applies to theoretical claims. If the body proves `\Omega(1/\sqrt{S})` only under a positive-GCG design, the contributions may not assert `\Omega(1/\sqrt{S})` savings for any opaque design. The introduction is the paper's promise to the referee, and the referee will check.

### Annotation Comment Structure

An introduction that will be revised many times benefits from explicit comment annotations next to every paragraph.

At the top of the section, a header comment block states:

1. The role of each paragraph in one or two lines (OVERALL LOGIC FLOW).
2. The DESIGN PRINCIPLES that constrain word choice and framing: lead with the realistic regime, frame as a new question, keep every lever visible, translate structure into managerial meaning, local style rules.

Before each paragraph, a short comment block states:

1. **Role.** What this paragraph does narratively.
2. **Internal Logic.** The order of ideas inside the paragraph.
3. **Big Picture.** What the paragraph sets up for the rest of the paper.

At the bottom, a structure summary block records:

1. A table of paragraph roles and approximate word counts.
2. The role split between P5 and the contributions, so future revisions do not let them drift into duplicates.
3. A one-line style check confirming no em dashes, no semicolons, no emphasis font, and locked terminology.

These comments do not appear in the PDF but they are what keeps a revised introduction coherent across multiple rounds of editing.

### Introduction Revision Checklist

Narrative:

- Does P1 open with a practitioner-facing fact, not with a technical definition?
- Is every decision variable that appears in the contributions block already named in P1?
- Is P2 grounded in a single concrete example with numbers?
- Does P3 explain the difficulty without previewing the answer?
- Is the research question in P4 stated as an interrogative sentence?
- Does P5 avoid reproducing any sentence from the contributions block?
- Does P5 end by pointing forward to the contributions?
- Does the contributions block use active, formal verbs (formulate, prove, characterize, identify, validate)?

Framing:

- Is the paper framed as answering a new question rather than extending prior work?
- Is the closest prior work named explicitly and are its restrictive assumptions stated precisely?
- Is the methodological shift previewed in P4 without revealing the answer?

Accuracy:

- Does every numerical or empirical claim in the contributions block have a matching section in the body?
- Are big-`O` claims stated with the same hypotheses under which they are proved?
- Is every theorem advertised at the level of precision it actually proves (order, class of designs, stated constants)?

Prose:

- Are uncommon or high-register words replaced by plain alternatives wherever precision allows?
- Are decorative openers used at most once and on a claim that can be defended?
- Is every definition unpacked with `that is` or `namely`, not with em-dashes?
- Are all em dashes, semicolons, and emphasis fonts removed from the rendered prose?
- Is one term locked per concept across the introduction, the body, and the appendix?

Comments:

- Does the header block state each paragraph's role and the design principles?
- Does every paragraph carry a Role / Internal Logic / Big Picture comment?
- Does the trailing summary block lock the role split between P5 and the contributions and confirm the style constraints?

## Style Constraints for This Project

For this paper, the prose should also satisfy the following local rules:

- Avoid em dashes.
- Avoid semicolons.
- Avoid emphasis font in the writing.
- Prefer readable, direct sentences over dense technical compression.
- Preserve notation and theorem precision.

## Revision Checklist

Before finalizing a section, check the following.

General narrative:

- Does the opening raise a managerial or economic question?
- Does each theorem have interpretation after it?
- Is the benchmark clear?
- Is the trade-off explicit?
- Are claims stated with the same precision as the theorem?
- Does the section tell a story rather than merely report results?
- Are the practical implications visible before the conclusion?
- Does the prose avoid em dashes, semicolons, and emphasis formatting?

Sections that fix a proxy then optimize allocation and design (Section 6 style):

- Does the opening state section scope and economic intuition without appendix-level algebra?
- Are graph-theoretic or budget statements literally correct and tied to the retailer's decision object?
- Is each design or decomposition insight developed in one place, with at most a short forward bridge elsewhere?
- Is terminology identical in the body and in any appendix material tied to the same results?

Architecture for multi-case sections:

- Is there exactly one setup block that defines the worst-case or sample-path quantity once?
- Does every case follow the same four-block template (setup paragraph, proposition, streamlined proof, managerial insight paragraph)?
- Is the master theorem in its own subsection rather than forward-referenced from inside a case?
- Does the closing paragraph name the common pattern and deliver a one-line diagnostic, without restating the master theorem?

Rigor on constants:

- Are all thresholds stated with explicit constants?
- Are per-type and total-subset perturbations distinguished and justified by combinatorial factors?
- When parallel propositions use different constants, is the gap either reconciled or explained as a mechanism-driven insight?

Managerial-insight paragraphs:

- Does each post-proposition paragraph include a failure-mode or trade-off sentence?
- Does each paragraph translate the mechanism into an operational verb the retailer can execute (precompute, solve, verify, monitor)?

## One-Sentence Summary

Write the paper so that every technical result is immediately translated into economic meaning, managerial insight, and practical design guidance.
