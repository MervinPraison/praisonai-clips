// Optional source-cut export through the pinned standard MCP SDK client.
import {createRequire} from 'node:module';
import {readFile,writeFile,rename,mkdir,copyFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';

const root=fileURLToPath(new URL('../',import.meta.url));
const require=createRequire(new URL('../tools/kdenlive-mcp/apps/mcp-server/package.json',import.meta.url));
const {Client}=await import(require.resolve('@modelcontextprotocol/sdk/client/index.js'));
const {StdioClientTransport}=await import(require.resolve('@modelcontextprotocol/sdk/client/stdio.js'));
const request=JSON.parse(await readFile(process.argv[2],'utf8'));
const statePath=resolve(request.output,'mcp-state.json');
await mkdir(request.output,{recursive:true});
let state;
try{state=JSON.parse(await readFile(statePath,'utf8'))}catch(error){if(error.code!=='ENOENT')throw error;state={client_id:'praisonai-shorts',operations:[]}}
if(state.source_sha256 && (state.source_sha256!==request.source_sha256 || state.edl_sha256!==request.edl_sha256))throw Error('Export input changed; use a new export directory');
Object.assign(state,{source_sha256:request.source_sha256,edl_sha256:request.edl_sha256,source:request.source,frame_mappings:request.mappings,mcp_job_ids:state.mcp_job_ids||[]});
async function save(){await writeFile(statePath+'.tmp',JSON.stringify(state,null,2));await rename(statePath+'.tmp',statePath)}
const client=new Client({name:'praisonai-shorts',version:'0.1.0'});
const transport=new StdioClientTransport({command:resolve(root,'scripts/kdenlive-mcp'),args:['--client-id','praisonai-shorts'],cwd:root,stderr:'pipe'});
transport.stderr?.on('data',data=>process.stderr.write(data));
async function call(name,args={}){
 const r=await client.callTool({name,arguments:args},undefined,{timeout:120000});
 if(r.isError || !r.structuredContent?.ok)throw Error(`${name}: ${JSON.stringify(r.structuredContent||r.content)}`);
 const data=r.structuredContent.data;
 state.operations.push({name,at:new Date().toISOString()});
 if(data?.revision!==undefined)state.revision=data.revision;
 await save();return data;
}
try{
 await client.connect(transport);
 let project;
 if(state.project_id){
  await call('project_open',{path:state.project_path});
  project=await call('project_get',{projectId:state.project_id});
 }else{
  state.project_path=resolve(request.output,'canonical-project');await save();
  // Recover a creation response lost before persisting the returned project ID.
  try{project=await call('project_open',{path:state.project_path})}
  catch{project=await call('project_create',{path:state.project_path,name:request.title,settings:{fps:{numerator:30,denominator:1},width:1080,height:1920}})}
  state.project_id=project.id;state.revision=project.revision;await save();
 }
 let asset=project.assets.find(a=>a.sha256===request.source_sha256);
 if(!asset){const imported=await call('media_import',{projectId:state.project_id,expectedRevision:project.revision,paths:[request.source],mode:'external'});project=imported.project;asset=imported.imported[0]}
 if(asset.sha256!==request.source_sha256)throw Error('Imported source hash mismatch');
 state.asset_id=asset.id;await save();
 const clips=project.tracks.filter(t=>t.kind==='video').flatMap(t=>t.clips).sort((a,b)=>a.timelineStart-b.timelineStart);
 if(!clips.length){
  const added=await call('timeline_add_clips',{projectId:state.project_id,expectedRevision:project.revision,
   requests:request.mappings.map(m=>({assetId:asset.id,sourceIn:m.source_in,sourceOut:m.source_out,linkedAv:true})),options:{mode:'append'}});
  project=added.project;state.clip_ids=added.changedIds;await save();
 }else if(clips.length!==request.mappings.length || clips.some((c,i)=>c.assetId!==asset.id || c.sourceIn!==request.mappings[i].source_in || c.sourceOut!==request.mappings[i].source_out || c.timelineStart!==request.mappings[i].output_start)){
  throw Error('Existing editable timeline differs from the requested EDL; refusing to overwrite edits');
 }
 state.validation=await call('project_validate',{projectId:state.project_id});
 state.export=await call('interchange_export',{projectId:state.project_id,format:'kdenlive',outputName:'editable-source-cuts'});
 await copyFile(state.export.path,resolve(request.output,'editable.kdenlive'));
 state.status='completed';await save();
 console.log(JSON.stringify({path:resolve(request.output,'editable.kdenlive'),state:statePath,revision:state.revision,fidelity:state.export.fidelity}));
}catch(error){state.status='failed';state.error=String(error);await save();throw error}
finally{await client.close()}
