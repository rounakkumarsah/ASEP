import { test } from 'bun:test';
import { candidateModels, setupAgent } from 'ori/eval';

const candidates = await candidateModels({
  limit: 2,
  maxPromptPrice: 0.000000,
  maxCompletionPrice: 0.000000,
});

for (const model of candidates) {
  test(`evaluates code generation on ${model}`, async () => {
    const run = await setupAgent({ model }).run('Write a Python function named reverse_string(s: str) -> str that reverses a string.');
    run.toComplete();
    run.toCostAtMost(0.00);
  }, { timeout: 60000 });
}
