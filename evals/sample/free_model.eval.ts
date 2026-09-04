import { test } from 'bun:test';
import { setupAgent } from 'ori/eval';

test('evaluates free model answering ping', async () => {
    const run = await setupAgent({ model: 'openrouter/free' }).run('Respond with only PONG');
    run.toComplete();
}, { timeout: 60000 });
