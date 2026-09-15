import {createServer} from 'node:net';
export async function requireFreePorts(...ports) {
 for(const port of ports)await new Promise((resolve,reject)=>{
  const probe=createServer();probe.once('error',()=>reject(new Error(`Test port ${port} is occupied; refusing server reuse`)));
  probe.listen(port,'127.0.0.1',()=>probe.close(resolve));
 });
}
export async function stopChild(child) {
 if(!child || child.exitCode!==null || child.signalCode!==null)return;
 await new Promise(resolve=>{
  const timer=setTimeout(()=>child.kill('SIGKILL'),5000);
  child.once('exit',()=>{clearTimeout(timer);resolve();});child.kill('SIGTERM');
 });
}
export function requireRunning(...children) {
 for(const child of children)if(child.exitCode!==null||child.signalCode!==null)throw new Error('Owned test server exited before readiness');
}
