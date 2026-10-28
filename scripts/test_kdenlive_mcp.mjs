import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(new URL('../tools/kdenlive-mcp/apps/mcp-server/package.json', import.meta.url));
const { Client } = await import(require.resolve('@modelcontextprotocol/sdk/client/index.js'));
const { StdioClientTransport } = await import(require.resolve('@modelcontextprotocol/sdk/client/stdio.js'));
const output = resolve(root, 'data/kdenlive-mcp-test');
await mkdir(output, { recursive: true });
const report = { source: resolve(root, 'input/backup video.mp4'), operations: [] };
const client = new Client({ name: 'praisonai-shorts-real-video-test', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: resolve(root, 'scripts/kdenlive-mcp'), cwd: root, stderr: 'pipe',
});
transport.stderr?.on('data', data => process.stderr.write(data));
async function call(name, args = {}) {
  const result = await client.callTool({ name, arguments: args }, undefined, { timeout: 180000 });
  const envelope = result.structuredContent;
  if (result.isError || !envelope?.ok) throw new Error(`${name}: ${JSON.stringify(result)}`);
  report.operations.push({ name, arguments: args, data: envelope.data });
  if (name !== 'job_get') console.log(name, (JSON.stringify(envelope.data) ?? 'ok').slice(0, 700));
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  return envelope.data;
}
async function waitJob(id) {
  const deadline = Date.now() + 240000;
  while (Date.now() < deadline) {
    const job = await call('job_get', { jobId: id });
    if (job.status === 'succeeded') return job;
    if (['failed', 'cancelled'].includes(job.status)) throw new Error(JSON.stringify(job));
    await new Promise(r => setTimeout(r, 1500));
  }
  throw new Error(`Timed out: ${id}`);
}
try {
  await client.connect(transport);
  const tools = await client.listTools();
  await writeFile(resolve(output, 'tools.json'), JSON.stringify(tools, null, 2));
  console.log(`Connected over MCP stdio: ${tools.tools.length} tools`);
  const project = await call('project_create', {
    path: resolve(output, `project-${Date.now()}`), name: 'Backup video - MCP editing test',
    settings: { fps: { numerator: 30, denominator: 1 }, width: 1920, height: 1080 },
  });
  const projectId = project.id;
  const imported = await call('media_import', {
    projectId, expectedRevision: project.revision, paths: [report.source], mode: 'external',
  });
  const assetId = imported.imported[0].id;
  const clips = await call('timeline_add_clips', {
    projectId, expectedRevision: imported.revision,
    requests: [
      { assetId, sourceIn: 0, sourceOut: 150, linkedAv: true },
      { assetId, sourceIn: 300, sourceOut: 450, linkedAv: true },
    ], options: { mode: 'append' },
  });
  await call('project_checkpoint', { projectId, name: 'Two cuts before title' });
  const title = await call('text_edit', {
    projectId, expectedRevision: clips.revision, action: 'add',
    items: [{ start: 0, end: 90, text: 'Backup video - MCP editing test',
      style: { fontSize: 44, x: 0.1, y: 0.8, width: 0.8, height: 0.12 } }],
  });
  const undone = await call('project_undo', { projectId, expectedRevision: title.revision });
  const redone = await call('project_redo', { projectId, expectedRevision: undone.revision });
  await call('text_edit', { projectId, expectedRevision: redone.revision,
    action: 'remove', ids: [title.project.texts[0].id] });
  report.limitations = [
    'This MCP edits a canonical project; opening its exported project in the GUI uses the Kdenlive launcher, not MCP GUI control.',
    'Text add/undo/redo works structurally, but qtext rendering scales incorrectly on this MLT runtime and the Kdenlive export omits text overlays. Text removed from delivered cut test.',
    'Kdenlive 22.12 cannot load these exports; use the installed Kdenlive 26.04.2 launcher.',
  ];
  await call('project_validate', { projectId });
  await call('timeline_query', { projectId });
  report.kdenliveExport = await call('interchange_export', {
    projectId, format: 'kdenlive', outputName: 'backup-mcp-test',
  });
  const preview = await call('preview_submit', { projectId, kind: 'frame', start: 30 });
  report.preview = await waitJob(preview.id);
  const render = await call('render_submit', {
    projectId, profileId: 'youtube-1080p', outputName: 'backup-mcp-test',
  });
  report.render = await waitJob(render.id);
  report.verification = await call('job_verify', { jobId: render.id });
  const cancelled = await call('render_submit', {
    projectId, profileId: 'youtube-1080p', outputName: 'cancellation-check',
  });
  await call('job_cancel', { jobId: cancelled.id });
  report.cancellation = await call('job_get', { jobId: cancelled.id });
  if (report.cancellation.status !== 'cancelled') throw new Error('Cancellation did not take effect');
  report.success = report.verification.valid;
} catch (error) {
  report.success = false;
  report.error = error.stack || String(error);
  console.error(report.error);
  process.exitCode = 1;
} finally {
  await writeFile(resolve(output, 'report.json'), JSON.stringify(report, null, 2));
  await client.close();
}
