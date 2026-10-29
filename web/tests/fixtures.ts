import fixture from './fixtures/panel.json';
import type { Agent, Audit, Incident, Page, RecordAnalysis, Run, Schema } from '../src/api/types';
import { ApiClient } from '../src/api/client';
import type { Session } from '../src/App';
export const data = fixture as unknown as {
  record: RecordAnalysis;
  blocked: RecordAnalysis;
  insufficient: RecordAnalysis;
  incident: Incident;
  runs: Page<Run>;
  audit: Page<Audit>;
  health: Schema['Readiness'];
  agents: Agent[];
};
export function session(role: 'writer' | 'reader' = 'writer'): Session {
  return {
    api: new ApiClient('test-session-key'),
    principal: { role, actor: `api-${role}` },
    health: data.health,
  };
}
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
