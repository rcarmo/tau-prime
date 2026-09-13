import {test,expect} from 'bun:test';
import {createServer} from 'node:net';
import {spawn} from 'node:child_process';
import {requireFreePorts,stopChild} from './server-lifecycle.mjs';
test('occupied ports are rejected rather than reused',async()=>{
 const server=createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{await expect(requireFreePorts(server.address().port)).rejects.toThrow('refusing server reuse');}
 finally{await new Promise(resolve=>server.close(resolve));}
});
test('cleanup waits for owned child exit',async()=>{
 const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)']);
 await stopChild(child);expect(child.exitCode!==null||child.signalCode!==null).toBe(true);
});
