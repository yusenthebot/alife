export const meta = {
  name: 'review-r2-selection',
  description: 'Adversarially verify that R2 evolution is real selection, not a bug/drift/fake',
  phases: [
    { title: 'Refute', detail: '3 skeptics each try to falsify "selection is real"' },
    { title: 'Synthesize', detail: 'judge weighs the verdicts' },
  ],
}

const ROOT = '/home/yusen/alife'
const CONTEXT = `
Project ${ROOT}: an evolving artificial-life ecosystem (Round 2).
Claim under test: "From random genomes, NATURAL SELECTION genuinely drives heritable
traits — food-attraction (w_food) rises ~1.9->3.0 and metabolism falls ~1.2->0.77 over
~1500 steps, with population sustaining and generations turning over (gen 0->12)."

Run tests with: env -u PYTHONPATH ${ROOT}/.venv/bin/python -m pytest -q -p no:cacheprovider
Verified data + plots are in ${ROOT}/runs/r2_evo/ (population.png, traits.png, trait_hist.png, evolution.csv).
Source: ${ROOT}/alife/ecosystem.py, genome.py, boids.py, world.py, metrics.py.
`

const VERDICT = {
  type: 'object',
  additionalProperties: false,
  required: ['refuted', 'confidence', 'findings', 'reasoning'],
  properties: {
    refuted: { type: 'boolean', description: 'true if you found a real reason the claim is false/overstated' },
    confidence: { type: 'number', description: '0..1 confidence in your verdict' },
    findings: { type: 'array', items: { type: 'string' }, description: 'concrete issues found (file:line where possible), or empty' },
    reasoning: { type: 'string', description: 'one-paragraph justification grounded in code/data you actually read' },
  },
}

const LENSES = [
  { key: 'code', prompt: `${CONTEXT}\nLENS = CODE CORRECTNESS. Read ecosystem.py + genome.py + boids.py. Try to REFUTE the claim by finding a bug that would PRODUCE the trait change WITHOUT real differential reproduction: e.g. mutation biased toward high w_food / low metabolism, energy accounting that rewards a trait directly, clipping at bounds masquerading as a trend, offspring not actually inheriting parent genome, cull/reproduce indexing bugs. Default to refuted=true if you find such a mechanism.` },
  { key: 'stats', prompt: `${CONTEXT}\nLENS = STATISTICAL VALIDITY (selection vs drift). Read runs/r2_evo/traits.png, trait_hist.png, population.png and evolution.csv. Try to REFUTE the claim: could w_food up / metabolism down be genetic DRIFT, founder effects, or an artifact of bounded mutation rather than directional selection? Is the direction consistent and large vs trait range? Are neutral traits (social weights) staying flat as a drift control? Default refuted=true if the signal is indistinguishable from drift.` },
  { key: 'fake', prompt: `${CONTEXT}\nLENS = NO-FAKING AUDIT. Verify results are REAL, not staged. Re-run the test suite yourself; spot-check that ecosystem.step actually computes movement/eat/reproduce/die (not hardcoded outputs), that the renderer draws real per-agent state, and that no metric is faked. Default refuted=true if anything is mocked, hardcoded, or the tests don't actually exercise selection.` },
]

phase('Refute')
const verdicts = await parallel(LENSES.map(l => () =>
  agent(l.prompt, { label: `refute:${l.key}`, phase: 'Refute', schema: VERDICT, model: 'sonnet', agentType: 'general-purpose' })
    .then(v => ({ lens: l.key, ...v }))
))

phase('Synthesize')
const real = verdicts.filter(Boolean)
const summary = await agent(
  `${CONTEXT}\nThree skeptics tried to refute the selection claim. Verdicts:\n${JSON.stringify(real, null, 2)}\n` +
  `Decide: is the claim CONFIRMED (selection is genuinely real), or are there material problems to fix? ` +
  `List any real issues worth fixing in R3, and any false alarms. Be concise.`,
  { label: 'synthesize', phase: 'Synthesize', model: 'sonnet' }
)
return { verdicts: real, summary }
