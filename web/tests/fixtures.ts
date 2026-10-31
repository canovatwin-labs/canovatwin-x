import fixture from './fixtures/panel.json';
import type { Agent, Audit, Incident, Page, RecordAnalysis, Run, Schema } from '../src/api/types';
import { ApiClient } from '../src/api/client';
import type { Session } from '../src/App';
import { vi } from 'vitest';
export const assetPage: Page<Schema['AssetSummary']> = {
  limit: 10,
  offset: 0,
  items: ['01', '02'].map((suffix) => ({
    asset_id: `synthetic-unit-${suffix}`,
    incident_count: 0,
    open_incident_count: 0,
    run_count: 0,
    latest_run_id: null,
    last_recorded_at: null,
    definition: {
      asset_id: `synthetic-unit-${suffix}`,
      name: `Pilot ${suffix}`,
      location: 'Sentetik pilot alan',
      source: 'synthetic',
      model: 'single-zone-10kW',
      expected_interval_s: 1,
      default_conditions: {
        workload: 'cyclic',
        baseline_load_kw: 4.2,
        ambient_c: 30,
        fan_response_s: 6,
      },
    },
  })),
};
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
  const api = new ApiClient('test-session-key');
  vi.spyOn(api, 'assets').mockResolvedValue(assetPage);
  return {
    api,
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
